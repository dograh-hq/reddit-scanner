// Main page - Single page app for Reddit comments and LinkedIn content discovery
"use client";

import { useState, useEffect, useCallback } from "react";

// Use env var for production, fallback to localhost for dev
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8007";
const POLL_INTERVAL = 5000; // 5 seconds - faster for progressive updates
// Posts at or above this score render in the high-signal zone; below it render
// in a visually-demoted, collapsed-by-default sub-section within each results card list.
const LOW_SCORE_THRESHOLD = 5;

// --- sessionStorage helpers for password persistence across page reloads ---
const getStoredPassword = (): string | null => sessionStorage.getItem("access_password");
const storePassword = (pw: string): void => sessionStorage.setItem("access_password", pw);
const clearPassword = (): void => sessionStorage.removeItem("access_password");

// Type definitions for API responses
interface Post {
  id: string;
  title: string;
  body: string;
  subreddit: string;
  subreddit_subscribers?: number;
  score: number;
  num_comments: number;
  url: string;
  flair: string | null;
  created_utc: string;
  author: string;
  // Multi-source attribution: every subreddit this canonical post appeared in
  // (cross-posts get one entry per subreddit; single-source posts have a one-element list)
  subreddit_sources?: Array<{ subreddit: string; subreddit_subscribers: number; permalink: string }>;
}

/** Format a subscriber count as "21k" / "0k" (rounded to thousands).
 * Sub-1000 counts also render as "0k" per spec. */
function fmtK(n: number | undefined | null): string {
  if (!n || n < 0) return "0k";
  return `${Math.round(n / 1000)}k`;
}

/** Inline list of all subreddit sources for a canonical post, with [Link N] tags + member counts.
 * Falls back to single-subreddit display when sources aren't attached. */
function PostSourcesLine({ post }: { post: Post }) {
  const sources = post.subreddit_sources && post.subreddit_sources.length > 0
    ? post.subreddit_sources
    : [{ subreddit: post.subreddit, subreddit_subscribers: post.subreddit_subscribers ?? 0, permalink: post.url }];
  return (
    <div className="post-sources">
      {sources.map((s, i) => (
        <span key={s.subreddit + i} className="post-source-chip">
          <a href={s.permalink} target="_blank" rel="noopener noreferrer">[Link{sources.length > 1 ? ` ${i + 1}` : ""}]</a>
          <span className="post-source-name"> r/{s.subreddit}</span>
          <span className="post-source-subs"> {fmtK(s.subreddit_subscribers)}</span>
        </span>
      ))}
    </div>
  );
}

/** Click-to-expand wrapper used to hide secondary content (comments / strategy bodies)
 * for low-score posts. Header content (title, meta, summary, "why" reasoning) stays outside. */
function CollapsibleBody({ children, defaultOpen = false, label = "Show comments / details" }: {
  children: React.ReactNode;
  defaultOpen?: boolean;
  label?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <>
      <button className="collapsible-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "▾ Hide" : `▸ ${label}`}
      </button>
      {open && children}
    </>
  );
}

interface CommentEvaluation {
  post_index: number;
  summary: string;  // LLM-generated 1-line summary
  decision: string;
  reasoning: string;
}

interface GeneratedComment {
  post_id: string;
  post_index: number;
  comments: string[];
}

interface CommentValidation {
  post_id: string;
  validations: Array<{
    total_score?: number;
    score?: number;
    tag: string;
    reasoning: string;
  }>;
}

interface PostScore {
  post_index: number;
  virality_score: number;
  fit_score: number;
  decision: string;  // SELECT or IGNORE - only SELECT posts get strategies
  reasoning: string;
}

interface PostStrategy {
  post_id: string;
  post_index: number;
  strategy: string;
}

interface PostValidation {
  post_id: string;
  validation: {
    tag: string;
    reasoning: string;
  };
}

interface LLMCall {
  seq: number;
  call_type: string;
  step_name: string;
  group_id: string | null;
  prompt: string;
  response: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  started_at: string;
  finished_at: string;
  success: boolean;
  error: string | null;
}

interface TaskResults {
  task_id: string;
  status: string;
  input_type: string;
  inputs: string[];  // original URLs/keywords the run was started with
  llm_calls?: LLMCall[];  // populated progressively; powers the bottom Prompt Debugger panel
  filtered_posts: Post[];
  comment_evaluations: CommentEvaluation[];
  generated_comments: GeneratedComment[];
  comment_validations: CommentValidation[];
  post_scores: PostScore[];
  post_strategies: PostStrategy[];
  post_validations: PostValidation[];
  error_log: string[];
}

interface HistoryItem {
  task_id: string;
  timestamp: string;
  input_type: string;
  status: string;
}

/**
 * PromptDebugger — bottom-of-page collapsible panel showing every LLM call's full prompt + response.
 * Multi-level accordion: Step → (parallel group | single batched call) → leaf prompt+tokens.
 * Calls are read in `seq` order; parallel calls (same group_id) collapse under one inner accordion.
 */
function PromptDebugger({ calls }: { calls: LLMCall[] }) {
  const [open, setOpen] = useState(false);
  const [openSteps, setOpenSteps] = useState<Set<string>>(new Set());
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set());
  const [openLeaves, setOpenLeaves] = useState<Set<number>>(new Set());

  const toggleSet = <T,>(set: Set<T>, key: T): Set<T> => {
    const next = new Set(set);
    if (next.has(key)) next.delete(key); else next.add(key);
    return next;
  };

  // Group calls by step (preserving first-seen order); inside each step, group parallel calls by group_id
  type Bucket = { groupId: string | null; calls: LLMCall[] };
  type StepBucket = { step: string; buckets: Bucket[] };
  const stepOrder: string[] = [];
  const stepMap: Record<string, StepBucket> = {};
  const sorted = [...calls].sort((a, b) => a.seq - b.seq);
  for (const c of sorted) {
    if (!stepMap[c.step_name]) {
      stepMap[c.step_name] = { step: c.step_name, buckets: [] };
      stepOrder.push(c.step_name);
    }
    const sb = stepMap[c.step_name];
    if (c.group_id) {
      const existing = sb.buckets.find((b) => b.groupId === c.group_id);
      if (existing) existing.calls.push(c);
      else sb.buckets.push({ groupId: c.group_id, calls: [c] });
    } else {
      sb.buckets.push({ groupId: null, calls: [c] });
    }
  }

  const grandTotal = calls.reduce((s, c) => s + (c.total_tokens || 0), 0);
  const grandIn = calls.reduce((s, c) => s + (c.input_tokens || 0), 0);
  const grandOut = calls.reduce((s, c) => s + (c.output_tokens || 0), 0);

  return (
    <div className={`prompt-debugger ${open ? "" : "collapsed"}`}>
      <div className="prompt-debugger-bar" onClick={() => setOpen((o) => !o)}>
        <span>
          🔍 Prompt Debugger — {calls.length} call{calls.length === 1 ? "" : "s"} ·{" "}
          {grandIn.toLocaleString()} in / {grandOut.toLocaleString()} out / {grandTotal.toLocaleString()} total tokens
        </span>
        <span>{open ? "▼" : "▲"}</span>
      </div>
      {open && (
        <div className="prompt-debugger-body">
          {stepOrder.map((step) => {
            const sb = stepMap[step];
            const stepTotal = sb.buckets.reduce(
              (s, b) => s + b.calls.reduce((s2, c) => s2 + c.total_tokens, 0), 0
            );
            const stepCalls = sb.buckets.reduce((n, b) => n + b.calls.length, 0);
            const stepOpen = openSteps.has(step);
            return (
              <div key={step} className="pd-step">
                <div className="pd-step-header" onClick={() => setOpenSteps((s) => toggleSet(s, step))}>
                  <span>{stepOpen ? "▾" : "▸"} {step}</span>
                  <span>{stepCalls} call{stepCalls === 1 ? "" : "s"} · {stepTotal.toLocaleString()} tok</span>
                </div>
                {stepOpen && sb.buckets.map((b, bi) => {
                  if (b.groupId) {
                    // Parallel group → inner accordion
                    const groupKey = `${step}::${b.groupId}`;
                    const gOpen = openGroups.has(groupKey);
                    const gTotal = b.calls.reduce((s, c) => s + c.total_tokens, 0);
                    return (
                      <div key={groupKey} className="pd-group">
                        <div className="pd-group-header" onClick={() => setOpenGroups((s) => toggleSet(s, groupKey))}>
                          <span>{gOpen ? "▾" : "▸"} Parallel batch ({b.calls.length} calls)</span>
                          <span>{gTotal.toLocaleString()} tok</span>
                        </div>
                        {gOpen && b.calls.map((c) => renderLeaf(c, openLeaves, setOpenLeaves))}
                      </div>
                    );
                  } else {
                    // Single batched call
                    return <div key={`${step}::${bi}`} className="pd-group">{renderLeaf(b.calls[0], openLeaves, setOpenLeaves)}</div>;
                  }
                })}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/** Render one leaf accordion: header (call type + tokens) + collapsed prompt + response.
 * NOTE: this is a plain helper (not a component); the returned <div> uses `key={c.seq}` which only
 * acts as a React key because the call sites map an array of leaves — see PromptDebugger above. */
function renderLeaf(
  c: LLMCall,
  openLeaves: Set<number>,
  setOpenLeaves: React.Dispatch<React.SetStateAction<Set<number>>>,
) {
  const isOpen = openLeaves.has(c.seq);
  const toggle = () => setOpenLeaves((s) => {
    const next = new Set(s);
    if (next.has(c.seq)) next.delete(c.seq); else next.add(c.seq);
    return next;
  });
  return (
    <div key={c.seq} className="pd-leaf">
      <div className="pd-leaf-header" onClick={toggle}>
        <span>
          {isOpen ? "▾" : "▸"} #{c.seq + 1} {c.call_type}
          {!c.success && <span style={{ color: "#f87171" }}> · ERROR</span>}
        </span>
        <span>{c.input_tokens.toLocaleString()} / {c.output_tokens.toLocaleString()} / {c.total_tokens.toLocaleString()} tok</span>
      </div>
      {isOpen && (
        <>
          <div style={{ padding: "4px 12px 0", fontSize: 11, color: "#9ca3af" }}>
            Prompt ({c.prompt.length.toLocaleString()} chars)
          </div>
          <pre className="pd-prompt">{c.prompt}</pre>
          <div style={{ padding: "4px 12px 0", fontSize: 11, color: "#9ca3af" }}>
            Response ({c.response.length.toLocaleString()} chars)
            {c.error && <span style={{ color: "#f87171" }}> · {c.error}</span>}
          </div>
          <pre className="pd-response">{c.response || "(empty)"}</pre>
        </>
      )}
    </div>
  );
}

export default function Home() {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [isAuthChecking, setIsAuthChecking] = useState(true); // true while checking sessionStorage on mount

  // Input state
  const [inputType, setInputType] = useState<"urls" | "keywords">("urls");
  const [inputText, setInputText] = useState("");

  // Task state
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<{ step?: number; description?: string }>({});
  const [results, setResults] = useState<TaskResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // History state
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Filter state
  const [commentFilter, setCommentFilter] = useState<string>("all");
  const [postFilter, setPostFilter] = useState<string>("all");

  // Keyword-mode controls (shipped to backend on /run; ignored in URL mode)
  const [keywordTimeframe, setKeywordTimeframe] = useState<string>("week");
  const [keywordSort, setKeywordSort] = useState<string>("relevance");
  const [keywordMaxPosts, setKeywordMaxPosts] = useState<number>(20);
  // Subreddit-mode controls (shipped to backend; ignored in keywords mode). Backend constructs the URL.
  const [subType, setSubType] = useState<string>("top");
  const [subTimeframe, setSubTimeframe] = useState<string>("day");

  /** Wraps fetch() to include auth header + auto-logout on 401 */
  const authFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
    const password = getStoredPassword();
    const headers = new Headers(options.headers);
    if (password) headers.set("X-Access-Password", password);
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
      // Password was invalidated or changed - force re-login
      clearPassword();
      setIsAuthenticated(false);
    }
    return res;
  };

  /** Handle login form submission */
  const handleLogin = async () => {
    setAuthError(null);
    setIsAuthChecking(true);
    try {
      const res = await fetch(`${API_BASE}/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: passwordInput }),
      });
      const data = await res.json();
      if (data.valid) {
        storePassword(passwordInput);
        setIsAuthenticated(true);
        setPasswordInput("");
      } else {
        setAuthError("Incorrect password");
      }
    } catch {
      setAuthError("Cannot reach server");
    } finally {
      setIsAuthChecking(false);
    }
  };

  /** Logout clears session and resets state */
  const handleLogout = () => {
    clearPassword();
    setIsAuthenticated(false);
    setPasswordInput("");
  };

  // Auto-verify stored password on mount
  useEffect(() => {
    const stored = getStoredPassword();
    if (!stored) {
      setIsAuthChecking(false);
      return;
    }
    fetch(`${API_BASE}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: stored }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.valid) setIsAuthenticated(true);
        else clearPassword(); // stored password no longer valid
      })
      .catch(() => clearPassword())
      .finally(() => setIsAuthChecking(false));
  }, []);

  // Fetch history on mount (only when authenticated)
  useEffect(() => {
    if (isAuthenticated) fetchHistory();
  }, [isAuthenticated]);

  // Polling effect
  useEffect(() => {
    if (!taskId || status === "complete" || status === "failed") return;

    const interval = setInterval(async () => {
      await pollStatus();
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [taskId, status]);

  /** GET /history - load list of previous runs into the dropdown */
  const fetchHistory = async () => {
    try {
      const res = await authFetch(`${API_BASE}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Failed to fetch history:", e);
    }
  };

  /** Poll GET /status and refresh results progressively until complete/failed.
   * Optional `tidOverride` lets handleRun pass the freshly-created task id directly
   * (avoids a stale-closure flash where the previous run's results briefly render). */
  const pollStatus = async (tidOverride?: string) => {
    const tid = tidOverride ?? taskId;
    if (!tid) return;

    try {
      const res = await authFetch(`${API_BASE}/status/${tid}`);
      if (!res.ok) throw new Error("Failed to get status");

      const data = await res.json();
      setStatus(data.status);
      setProgress(data.progress);

      // Fetch results on every poll for progressive updates
      await fetchResults(tid);

      if (data.status === "complete" || data.status === "failed") {
        setIsLoading(false);
        fetchHistory();
      }
    } catch (e) {
      console.error("Poll error:", e);
    }
  };

  /** GET /results/{id} - fetch full task results object */
  const fetchResults = async (tid: string) => {
    try {
      const res = await authFetch(`${API_BASE}/results/${tid}`);
      if (!res.ok) throw new Error("Failed to fetch results");
      const data = await res.json();
      setResults(data);
    } catch (e) {
      setError("Failed to fetch results");
    }
  };

  /** Parse inputs and POST /run to start a new workflow, then begin polling */
  const handleRun = async () => {
    setError(null);
    setResults(null);
    setIsLoading(true);

    // Parse inputs (comma or newline separated)
    const inputs = inputText
      .split(/[,\n]/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    if (inputs.length === 0) {
      setError("Please enter at least one URL or keyword");
      setIsLoading(false);
      return;
    }

    try {
      // Only send mode-specific controls; backend ignores when not applicable
      const body: Record<string, unknown> = { input_type: inputType, inputs };
      if (inputType === "keywords") {
        body.timeframe = keywordTimeframe;
        body.sort = keywordSort;
        body.max_posts = keywordMaxPosts;
      } else {
        body.sub_type = subType;
        // Reddit only honours ?t=<timeframe> for /top — omit for other sort types
        if (subType === "top") body.sub_timeframe = subTimeframe;
      }
      const res = await authFetch(`${API_BASE}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start run");
      }

      const data = await res.json();
      const newTaskId: string = data.task_id;
      setTaskId(newTaskId);
      setStatus("running");
      setProgress({ step: 1, description: "Starting..." });

      // Immediately start polling - pass new task id explicitly to avoid stale-closure flash
      setTimeout(() => pollStatus(newTaskId), 1000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setIsLoading(false);
    }
  };

  /** Load a previous run's status + results when picked from the history dropdown.
   * Also restores the input box + mode toggle to that run's original inputs so the
   * displayed cards always match what's visible in the input field. */
  const handleHistorySelect = async (tid: string) => {
    if (!tid) return;
    setTaskId(tid);
    setIsLoading(true);
    setError(null);

    try {
      const statusRes = await authFetch(`${API_BASE}/status/${tid}`);
      const statusData = await statusRes.json();
      setStatus(statusData.status);
      setProgress(statusData.progress);

      // Fetch results inline so we can also restore inputText + inputType from this run
      const resRes = await authFetch(`${API_BASE}/results/${tid}`);
      if (!resRes.ok) throw new Error("Failed to fetch results");
      const data: TaskResults = await resRes.json();
      setResults(data);
      if (data.input_type === "urls" || data.input_type === "keywords") {
        setInputType(data.input_type);
      }
      setInputText(Array.isArray(data.inputs) ? data.inputs.join("\n") : "");
    } catch (e) {
      setError("Failed to load run");
    } finally {
      setIsLoading(false);
    }
  };

  // Filter helpers
  const getCommentTag = useCallback(
    (postId: string): string => {
      const validation = results?.comment_validations.find((v) => v.post_id === postId);
      if (!validation || !validation.validations[0]) return "error";
      return validation.validations[0].tag.toLowerCase();
    },
    [results]
  );

  const getPostTag = useCallback(
    (postId: string): string => {
      const validation = results?.post_validations.find((v) => v.post_id === postId);
      if (!validation) return "error";
      return validation.validation.tag.toLowerCase();
    },
    [results]
  );

  // Get LLM-generated summary for a post by index
  const getPostSummary = useCallback(
    (postIndex: number, fallbackBody: string): string => {
      const evaluation = results?.comment_evaluations.find((e) => e.post_index === postIndex);
      if (evaluation?.summary) return evaluation.summary;
      return fallbackBody?.slice(0, 150) + "..." || "No summary available";
    },
    [results]
  );

  // Get evaluation reasoning for why post was selected for commenting
  const getEvaluationReasoning = useCallback(
    (postIndex: number): string | null => {
      const evaluation = results?.comment_evaluations.find((e) => e.post_index === postIndex);
      return evaluation?.reasoning || null;
    },
    [results]
  );

  // Filtered data
  const selectedPostsWithComments = results?.generated_comments.filter((gc) => {
    if (commentFilter === "all") return true;
    return getCommentTag(gc.post_id) === commentFilter;
  });

  const postSuggestions = results?.post_strategies.filter((ls) => {
    if (postFilter === "all") return true;
    return getPostTag(ls.post_id) === postFilter;
  });

  // Get rejected posts: those NOT present in generated_comments (i.e. evaluation said NO or item was dropped).
  // Match by stable post.id, NOT by Array.indexOf — duplicates in filtered_posts make indexOf collide.
  const yesPostIds = new Set(results?.generated_comments.map((gc) => gc.post_id) ?? []);
  const rejectedPosts = results?.filtered_posts.filter((post) => !yesPostIds.has(post.id));

  // Partition any post-indexed item list by the corresponding post's score.
  // Used by both Selected Posts and Post Suggestions sections to render a high-signal
  // group at top, and a visually-demoted low-score group below.
  function partitionByScore<T extends { post_index: number }>(items: T[] | undefined) {
    const high: T[] = [];
    const low: T[] = [];
    for (const it of items ?? []) {
      const s = results?.filtered_posts[it.post_index]?.score ?? 0;
      (s >= LOW_SCORE_THRESHOLD ? high : low).push(it);
    }
    return { high, low };
  }
  const sel = partitionByScore(selectedPostsWithComments);
  const sug = partitionByScore(postSuggestions);

  /** Render one Selected Posts with Comments card.
   * Header (title/sources/meta/tag/summary/why-selected) is always visible; for low-score
   * posts the comment-box list is hidden behind a CollapsibleBody toggle. */
  const renderSelectedCard = (gc: GeneratedComment, lowScore: boolean) => {
    if (!results) return null;
    const post = results.filtered_posts[gc.post_index];
    const validation = results.comment_validations.find((v) => v.post_id === gc.post_id);
    if (!post) return null;

    const commentList = (
      <>
        {gc.comments.map((comment, i) => (
          <div className="comment-box" key={i}>
            <h4>Comment Suggestion {i + 1}</h4>
            <div className="comment-text">{comment}</div>
            {validation?.validations[i] && (
              <div className="comment-score">
                Score: {validation.validations[i].total_score || validation.validations[i].score || "N/A"}/100
                {" | "}
                {validation.validations[i].reasoning?.slice(0, 100)}...
              </div>
            )}
          </div>
        ))}
      </>
    );

    return (
      <div className={`post-card${lowScore ? " low-score" : ""}`} key={gc.post_id}>
        <div className="post-header">
          <div>
            <div className="post-title">
              <a href={post.url} target="_blank" rel="noopener noreferrer">
                {post.title}
              </a>
            </div>
            <PostSourcesLine post={post} />
            <div className="post-meta">
              <span>{post.score} upvotes</span>
              <span>{post.num_comments} comments</span>
              {post.flair && <span>{post.flair}</span>}
            </div>
          </div>
          <span className={`tag ${getCommentTag(gc.post_id)}`}>
            {getCommentTag(gc.post_id)}
          </span>
        </div>

        <div className="post-summary">{getPostSummary(gc.post_index, post.body)}</div>

        {getEvaluationReasoning(gc.post_index) && (
          <div className="reasoning-box">
            <strong>Why selected:</strong> {getEvaluationReasoning(gc.post_index)}
          </div>
        )}

        {lowScore
          ? <CollapsibleBody label={`Show ${gc.comments.length} comment suggestion${gc.comments.length === 1 ? "" : "s"}`}>{commentList}</CollapsibleBody>
          : commentList}
      </div>
    );
  };

  /** Render one Post Suggestions (Reddit/LinkedIn) card.
   * Header (title/sources/meta/tag/summary/why-it-scores-well) is always visible; for low-score
   * posts the strategy-box (scores + bullets + validation reasoning) collapses behind a toggle. */
  const renderSuggestionCard = (ls: PostStrategy, lowScore: boolean) => {
    if (!results) return null;
    const post = results.filtered_posts[ls.post_index];
    const scores = results.post_scores.find((s) => s.post_index === ls.post_index);
    const validation = results.post_validations.find((v) => v.post_id === ls.post_id);
    if (!post) return null;

    const strategyBlock = (
      <div className="strategy-box">
        <div className="scores">
          <span className="score-item">
            Virality: <strong>{scores?.virality_score || "?"}/10</strong>
          </span>
          <span className="score-item">
            Fit: <strong>{scores?.fit_score || "?"}/10</strong>
          </span>
        </div>
        {/* Strategy is a markdown bullet list (lines starting with `- `); render each as <li> for scannability */}
        <ul className="strategy-bullets">
          {(ls.strategy || "")
            .split("\n")
            .map((line) => line.replace(/^\s*[-*]\s+/, "").trim())
            .filter((line) => line.length > 0)
            .map((line, i) => <li key={i}>{line}</li>)}
        </ul>
        {validation && (
          <div className="comment-score" style={{ marginTop: 8 }}>
            {validation.validation.reasoning}
          </div>
        )}
      </div>
    );

    return (
      <div className={`post-card${lowScore ? " low-score" : ""}`} key={ls.post_id}>
        <div className="post-header">
          <div>
            <div className="post-title">
              <a href={post.url} target="_blank" rel="noopener noreferrer">
                {post.title}
              </a>
            </div>
            <PostSourcesLine post={post} />
            <div className="post-meta">
              <span>{post.score} upvotes</span>
            </div>
          </div>
          <span className={`tag ${getPostTag(ls.post_id)}`}>
            {getPostTag(ls.post_id)}
          </span>
        </div>

        <div className="post-summary">{getPostSummary(ls.post_index, post.body)}</div>

        {scores?.reasoning && (
          <div className="reasoning-box">
            <strong>Why it scores well:</strong> {scores.reasoning}
          </div>
        )}

        {lowScore
          ? <CollapsibleBody label="Show strategy & validation">{strategyBlock}</CollapsibleBody>
          : strategyBlock}
      </div>
    );
  };

  // Show loading spinner while checking stored password
  if (isAuthChecking) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <div className="spinner" />
        </div>
      </div>
    );
  }

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h1>Reddit & Lin Discovery</h1>
          <p>Enter the access password to continue.</p>
          <input
            className="password-input"
            type="password"
            placeholder="Password"
            value={passwordInput}
            onChange={(e) => setPasswordInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />
          <button className="auth-button" onClick={handleLogin}>
            Sign In
          </button>
          {authError && <div className="auth-error">{authError}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header with title and logout */}
      <div className="header-bar">
        <h1>Reddit Comments & Reddit/LIn Posts Discovery</h1>
        <button className="logout-button" onClick={handleLogout}>Logout</button>
      </div>

      {/* Action row: Memory Bank button (left) + History dropdown (right) */}
      <div className="header-actions">
        <a href="/memory" className="memory-bank-button">📚 Subreddit Memory Bank</a>
        <select className="history-select" onChange={(e) => handleHistorySelect(e.target.value)} defaultValue="">
          <option value="">Load previous run...</option>
          {history.map((h) => (
            <option key={h.task_id} value={h.task_id}>
              {new Date(h.timestamp).toLocaleString()} - {h.input_type} ({h.status})
            </option>
          ))}
        </select>
      </div>

      {/* Input Section */}
      <div className="input-section">
        {/* Header row: radios on the left, mode-specific dropdowns on the right (same row) */}
        <div className="input-header">
          <div className="radio-group">
            <label>
              <input
                type="radio"
                name="inputType"
                checked={inputType === "urls"}
                onChange={() => setInputType("urls")}
              />
              Subreddits
            </label>
            <label>
              <input
                type="radio"
                name="inputType"
                checked={inputType === "keywords"}
                onChange={() => setInputType("keywords")}
              />
              Keywords
            </label>
          </div>

          <div className="mode-controls">
            {inputType === "urls" ? (
              <>
                <label>
                  Sort
                  <select value={subType} onChange={(e) => setSubType(e.target.value)}>
                    <option value="top">Top posts</option>
                    <option value="hot">Hot now</option>
                    <option value="new">Newest</option>
                    <option value="best">Best</option>
                    <option value="rising">Rising</option>
                  </select>
                </label>
                {subType === "top" && (
                  <label>
                    Time frame
                    <select value={subTimeframe} onChange={(e) => setSubTimeframe(e.target.value)}>
                      <option value="hour">Past hour</option>
                      <option value="day">Today</option>
                      <option value="week">This week</option>
                      <option value="month">This month</option>
                      <option value="year">This year</option>
                      <option value="all">All time</option>
                    </select>
                  </label>
                )}
              </>
            ) : (
              <>
                <label>
                  Time frame
                  <select value={keywordTimeframe} onChange={(e) => setKeywordTimeframe(e.target.value)}>
                    <option value="day">Last 24 hours</option>
                    <option value="week">Past week</option>
                    <option value="month">Past month</option>
                    <option value="year">Past year</option>
                    <option value="all">All time</option>
                  </select>
                </label>
                <label>
                  Sort
                  <select value={keywordSort} onChange={(e) => setKeywordSort(e.target.value)}>
                    <option value="relevance">Most relevant</option>
                    <option value="top">Most upvoted</option>
                  </select>
                </label>
                <label>
                  Posts per keyword
                  <select value={keywordMaxPosts} onChange={(e) => setKeywordMaxPosts(Number(e.target.value))}>
                    <option value={10}>10 posts</option>
                    <option value={20}>20 posts</option>
                    <option value={30}>30 posts</option>
                    <option value={50}>50 posts</option>
                  </select>
                </label>
              </>
            )}
          </div>
        </div>

        <textarea
          rows={3}
          style={{
            minHeight: "60px",
            backgroundColor: inputType === "urls" ? "#e0f2fe" : "#fee2e2",
          }}
          placeholder={
            inputType === "urls"
              ? "Enter subreddit names (one per line or comma-separated). Any format: /n8n • SaaS • r/AI_Agents • reddit.com/r/ollama\ne.g. SaaS, n8n, ollama"
              : "Enter keywords (one per line or comma-separated)\ne.g., voice ai, voice agent, pipecat, livekit, ai reception, cold calling"
          }
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />

        <button onClick={handleRun} disabled={isLoading}>
          {isLoading ? "Running..." : "Run Now"}
        </button>
      </div>

      {/* Status Bar */}
      {status && status !== "complete" && (
        <div className={`status-bar ${error ? "error" : ""}`}>
          {isLoading && <div className="spinner" />}
          <span>
            {error || `Step ${progress.step || "?"}: ${progress.description || "Processing..."}`}
          </span>
        </div>
      )}

      {/* Error Display */}
      {error && <div className="status-bar error">{error}</div>}

      {/* Results */}
      {results && (
        <>
          {/* Sections 1 & 2 sit side-by-side (50/50); Section 3 below at full width */}
          <div className="results-row">
          {/* Section 1: Selected Posts with Comments */}
          <div className="results-section">
            <h2>Selected Posts with Comments ({selectedPostsWithComments?.length || 0})</h2>

            <div className="filter-tabs">
              {["all", "pass", "unsure", "fail"].map((f) => (
                <button
                  key={f}
                  className={`filter-tab ${commentFilter === f ? "active" : ""}`}
                  onClick={() => setCommentFilter(f)}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>

            {selectedPostsWithComments?.length === 0 && (
              <div className="empty-state">No posts match this filter</div>
            )}

            {/* High-score Selected cards (score >= LOW_SCORE_THRESHOLD) — full body always visible */}
            {sel.high.map((gc) => renderSelectedCard(gc, false))}

            {/* Low-score Selected cards — body collapsed by default behind a toggle */}
            {sel.low.length > 0 && (
              <>
                <div className="low-score-banner">
                  ↓ Below posts have lower upvotes (less than {LOW_SCORE_THRESHOLD})
                </div>
                {sel.low.map((gc) => renderSelectedCard(gc, true))}
              </>
            )}
          </div>

          {/* Section 2: Post Suggestions: For Reddit and LinkedIn */}
          <div className="results-section">
            <h2>Post Suggestions: For Reddit and LinkedIn ({postSuggestions?.length || 0})</h2>

            <div className="filter-tabs">
              {["all", "pass", "unsure", "fail"].map((f) => (
                <button
                  key={f}
                  className={`filter-tab ${postFilter === f ? "active" : ""}`}
                  onClick={() => setPostFilter(f)}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>

            {postSuggestions?.length === 0 && (
              <div className="empty-state">No posts match this filter</div>
            )}

            {/* High-score Suggestion cards (score >= LOW_SCORE_THRESHOLD) — strategy block always visible */}
            {sug.high.map((ls) => renderSuggestionCard(ls, false))}

            {/* Low-score Suggestion cards — strategy block collapsed by default behind a toggle */}
            {sug.low.length > 0 && (
              <>
                <div className="low-score-banner">
                  ↓ Below posts have lower upvotes (less than {LOW_SCORE_THRESHOLD})
                </div>
                {sug.low.map((ls) => renderSuggestionCard(ls, true))}
              </>
            )}
          </div>
          </div>

          {/* Section 3: Rejected Posts (full-width below the side-by-side row) */}
          <div className="results-section">
            <h2>Rejected Posts ({rejectedPosts?.length || 0})</h2>

            {rejectedPosts?.length === 0 && (
              <div className="empty-state">No rejected posts</div>
            )}

            {rejectedPosts?.map((post) => {
              const postIndex = results.filtered_posts.indexOf(post);
              return (
                <div className="post-card" key={post.id} style={{ background: "#f9f9f9" }}>
                  <div className="post-title">
                    <a href={post.url} target="_blank" rel="noopener noreferrer">
                      {post.title}
                    </a>
                  </div>
                  <div className="post-meta">
                    <span>r/{post.subreddit}</span>
                    <span>{post.score} upvotes</span>
                    <span>{post.num_comments} comments</span>
                  </div>
                  <div className="post-summary">{getPostSummary(postIndex, post.body)}</div>
                </div>
              );
            })}
          </div>

          {/* Error Log */}
          {results.error_log.length > 0 && (
            <div className="results-section" style={{ background: "#fff5f5" }}>
              <h2>Errors ({results.error_log.length})</h2>
              {results.error_log.map((err, i) => (
                <div key={i} style={{ fontSize: 13, color: "#c00", marginBottom: 8 }}>
                  {err}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Bottom-of-page collapsible Prompt Debugger (only when llm_calls present on this run) */}
      {results?.llm_calls && results.llm_calls.length > 0 && (
        <PromptDebugger calls={results.llm_calls} />
      )}
    </div>
  );
}

