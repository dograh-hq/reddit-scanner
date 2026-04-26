// Subreddit Memory Bank dashboard - permanent archive of PASS/UNSURE posts grouped by subreddit
"use client";

import { useState, useEffect, useCallback } from "react";
import { Tour, type TourStep } from "../Tour";

// Tour for /memory — primary insight is "rows are clickable accordions"
const MEMORY_TOUR_STEPS: TourStep[] = [
  {
    id: "tour-pagination",
    title: "Pagination",
    body: "20 subreddits per page. Same Prev / Next mirrored at the bottom — use whichever is closer.",
  },
  {
    id: "tour-mem-toolbar",
    title: "Sort subreddits",
    body: "Default = Keyword finds (unbiased): posts discovered via blind keyword fetches with no subreddit pre-selection. Descending order = where promo-relevant content actually lives. Switch to Posts (total) or Members for the other views.",
  },
  {
    id: "tour-mem-list",
    title: "Rows expand on click",
    body: "Each row shows '<unbiased> · <total>' counts. Click anywhere to view the subreddit's PASS/UNSURE posts; inside, sort by comments / upvotes / date and search titles.",
  },
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8007";
const PAGE_SIZE = 20;

// Reused sessionStorage key from page.tsx (must stay in sync)
const getStoredPassword = (): string | null => sessionStorage.getItem("access_password");

interface SubRow {
  subreddit: string;
  subreddit_subscribers: number;
  post_count: number;       // total: counts every PASS/UNSURE post regardless of fetch mode
  keyword_count: number;    // unbiased: counts only posts found via keyword fetches (no subreddit pre-selection)
  last_saved_at: string;
}

/** Format subscriber count as "21k" / "0k" — same helper as page.tsx, duplicated to keep this route self-contained. */
function fmtK(n: number | undefined | null): string {
  if (!n || n < 0) return "0k";
  return `${Math.round(n / 1000)}k`;
}

interface PostRow {
  post_id: string;
  permalink: string;
  title: string;
  flair: string | null;
  summary: string | null;
  upvotes: number;
  num_comments: number;
  // ISO 8601 string from Apify (e.g. "2026-04-20T19:51:08.000Z"); never a unix epoch number
  created_utc: string | null;
  tag: "pass" | "unsure";
  qualifying_gate: "comment" | "post" | "both";
  saved_at: string;
}

interface PostsState {
  page: number;
  total: number;
  items: PostRow[];
  sortBy: "comments" | "upvotes" | "date";
  order: "desc" | "asc";
  filter: "all" | "pass" | "unsure";
  q: string;
  loading: boolean;
}

const DEFAULT_POSTS_STATE: PostsState = {
  page: 1, total: 0, items: [],
  sortBy: "comments", order: "desc", filter: "all", q: "", loading: false,
};

export default function MemoryPage() {
  // Auth: read sessionStorage password set by main page; if missing, show inline prompt
  const [password, setPassword] = useState<string>("");
  const [needsAuth, setNeedsAuth] = useState<boolean>(false);

  // Subreddits list state
  const [subs, setSubs] = useState<SubRow[]>([]);
  const [subTotal, setSubTotal] = useState(0);
  const [subPage, setSubPage] = useState(1);
  // Default sort = keyword_finds (matches backend default; unbiased view by design)
  const [subSort, setSubSort] = useState<"keyword_finds" | "posts" | "members">("keyword_finds");
  const [subOrder, setSubOrder] = useState<"desc" | "asc">("desc");
  const [subLoading, setSubLoading] = useState(false);

  // Currently-expanded subreddit + per-sub posts cache
  const [openSub, setOpenSub] = useState<string | null>(null);
  const [postsBySub, setPostsBySub] = useState<Record<string, PostsState>>({});

  // Hydrate password from sessionStorage on mount
  useEffect(() => {
    const stored = getStoredPassword();
    if (!stored) { setNeedsAuth(true); return; }
    setPassword(stored);
  }, []);

  /** Wraps fetch with X-Access-Password header */
  const authFetch = useCallback((url: string) => {
    return fetch(url, { headers: { "X-Access-Password": password } });
  }, [password]);

  /** Fetch paginated subreddit list whenever page / sort / order / password changes */
  useEffect(() => {
    if (!password) return;
    let cancelled = false;
    setSubLoading(true);
    const url = `${API_BASE}/memory/subreddits?page=${subPage}&page_size=${PAGE_SIZE}&sort_by=${subSort}&order=${subOrder}`;
    authFetch(url)
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then((data) => { if (!cancelled) { setSubs(data.items); setSubTotal(data.total); } })
      .catch((s) => { if (s === 401) setNeedsAuth(true); })
      .finally(() => { if (!cancelled) setSubLoading(false); });
    return () => { cancelled = true; };
  }, [subPage, subSort, subOrder, password, authFetch]);

  /** Fetch posts for a subreddit (called only on accordion expand or sort/filter/page change) */
  const loadPosts = useCallback(async (
    name: string,
    page: number,
    sortBy: PostsState["sortBy"],
    order: PostsState["order"],
    filter: PostsState["filter"],
    q: string,
  ) => {
    setPostsBySub((prev) => ({
      ...prev,
      [name]: { ...(prev[name] || DEFAULT_POSTS_STATE), loading: true, sortBy, order, filter, q, page },
    }));
    const params = new URLSearchParams({
      page: String(page), page_size: String(PAGE_SIZE),
      sort_by: sortBy, order, filter,
    });
    if (q.trim()) params.set("q", q.trim());
    try {
      const r = await authFetch(`${API_BASE}/memory/subreddits/${encodeURIComponent(name)}/posts?${params}`);
      if (r.status === 401) { setNeedsAuth(true); return; }
      if (!r.ok) throw new Error(String(r.status));
      const data = await r.json();
      setPostsBySub((prev) => ({
        ...prev,
        [name]: { page, total: data.total, items: data.items, sortBy, order, filter, q, loading: false },
      }));
    } catch {
      setPostsBySub((prev) => ({ ...prev, [name]: { ...(prev[name] || DEFAULT_POSTS_STATE), loading: false } }));
    }
  }, [authFetch]);

  /** Toggle accordion - first open triggers the API call; close just collapses */
  const toggleSub = (name: string) => {
    if (openSub === name) { setOpenSub(null); return; }
    setOpenSub(name);
    if (!postsBySub[name]) {
      loadPosts(name, 1, "comments", "desc", "all", "");
    }
  };

  if (needsAuth) {
    return (
      <div className="memory-container">
        <a href="/" className="back-link">← Back to runs</a>
        <h1>Subreddit Memory Bank</h1>
        <div className="memory-empty">
          Please sign in on the main page first, then return here.
        </div>
      </div>
    );
  }

  // Pre-compute total pages for the top pager — same math as the bottom pager.
  const subTotalPages = Math.max(1, Math.ceil(subTotal / PAGE_SIZE));

  return (
    <div className="memory-container">
      <a href="/" className="back-link">← Back to runs</a>
      <div className="page-header-row">
        <h1>Subreddit Memory Bank</h1>
        {/* Top pager — always rendered (Prev/Next disable when only 1 page) so the user
            always sees the pagination affordance. ID drives the guided-tour step. */}
        <div id="tour-pagination" className="memory-pager memory-pager-top" title="20 subreddits per page — Prev / Next to navigate. Same pager mirrored at the bottom.">
          <button disabled={subPage <= 1} onClick={() => setSubPage((p) => p - 1)}>← Prev</button>
          <span>Page {subPage} of {subTotalPages}</span>
          <button
            disabled={subPage >= subTotalPages}
            onClick={() => setSubPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      </div>

      <div id="tour-mem-toolbar" className="memory-toolbar">
        <div className="posts-toolbar" style={{ margin: 0 }}>
          <span className="posts-label">Sort by:</span>
          {(["keyword_finds", "posts", "members"] as const).map((k) => (
            <button
              key={k}
              className={`posts-sort ${subSort === k ? "active" : ""}`}
              onClick={() => {
                setSubPage(1);
                if (subSort === k) setSubOrder((o) => (o === "desc" ? "asc" : "desc"));
                else { setSubSort(k); setSubOrder("desc"); }
              }}
            >
              {k === "keyword_finds" ? "Keyword finds (unbiased)" : k === "posts" ? "Posts" : "Members"}
              {subSort === k && <span> {subOrder === "desc" ? "↓" : "↑"}</span>}
            </button>
          ))}
        </div>
        <span className="memory-toolbar-meta">
          {subTotal} subreddit{subTotal === 1 ? "" : "s"} · page {subPage} of {Math.max(1, Math.ceil(subTotal / PAGE_SIZE))}
        </span>
      </div>

      {subLoading && <div className="memory-empty">Loading…</div>}
      {!subLoading && subs.length === 0 && (
        <div className="memory-empty">
          No subreddits archived yet. Run a workflow with PASS or UNSURE results to populate the bank.
        </div>
      )}

      <div id="tour-mem-list">
      {subs.map((s) => (
        <div key={s.subreddit} className="sub-accordion">
          <button className="sub-row" onClick={() => toggleSub(s.subreddit)}>
            <span className="sub-name">
              r/{s.subreddit}
              <span className="sub-subscribers"> · {fmtK(s.subreddit_subscribers)} members</span>
            </span>
            <span className="sub-meta">
              {/* Unbiased on the LEFT, total on the RIGHT — matches the dashboard's default sort */}
              <strong>{s.keyword_count}</strong> unbiased · {s.post_count} total
              {" · last "}{new Date(s.last_saved_at).toLocaleDateString()}
            </span>
            <span className="sub-hint">{openSub === s.subreddit ? "Click to collapse" : "Click to view posts"}</span>
            <span className={openSub === s.subreddit ? "chev open" : "chev"}>›</span>
          </button>
          {openSub === s.subreddit && (
            <PostsPanel
              name={s.subreddit}
              state={postsBySub[s.subreddit] || DEFAULT_POSTS_STATE}
              onChange={(page, sortBy, order, filter, q) => loadPosts(s.subreddit, page, sortBy, order, filter, q)}
            />
          )}
        </div>
      ))}

      </div>

      {/* Pager for subreddit list (bottom mirror of the top pager) */}
      <div className="memory-pager" title="20 subreddits per page — also available at the top right of the page heading">
        <button disabled={subPage <= 1} onClick={() => setSubPage((p) => p - 1)}>← Previous</button>
        <span>Page {subPage}</span>
        <button
          disabled={subPage * PAGE_SIZE >= subTotal}
          onClick={() => setSubPage((p) => p + 1)}
        >
          Next →
        </button>
      </div>

      <Tour steps={MEMORY_TOUR_STEPS} storageKey="tour_memory_seen" />
    </div>
  );
}

/** Posts list inside an expanded subreddit accordion */
function PostsPanel({
  name, state, onChange,
}: {
  name: string;
  state: PostsState;
  onChange: (page: number, sortBy: PostsState["sortBy"], order: PostsState["order"], filter: PostsState["filter"], q: string) => void;
}) {
  const [qDraft, setQDraft] = useState(state.q);

  const setSort = (sortBy: PostsState["sortBy"]) => {
    const order = state.sortBy === sortBy ? (state.order === "desc" ? "asc" : "desc") : "desc";
    onChange(1, sortBy, order, state.filter, state.q);
  };
  const setFilter = (filter: PostsState["filter"]) => onChange(1, state.sortBy, state.order, filter, state.q);
  const submitSearch = () => onChange(1, state.sortBy, state.order, state.filter, qDraft);

  const totalPages = Math.max(1, Math.ceil(state.total / PAGE_SIZE));

  return (
    <div className="posts-panel">
      <div className="posts-toolbar">
        <span className="posts-label">Sort By:</span>
        {(["comments", "upvotes", "date"] as const).map((k) => (
          <button
            key={k}
            className={`posts-sort ${state.sortBy === k ? "active" : ""}`}
            onClick={() => setSort(k)}
          >
            {k === "comments" ? "Comments" : k === "upvotes" ? "Upvotes" : "Date"}
            {state.sortBy === k && <span> {state.order === "desc" ? "↓" : "↑"}</span>}
          </button>
        ))}
        <span className="posts-divider">|</span>
        <span className="posts-label">Filter Posts:</span>
        {(["all", "pass", "unsure"] as const).map((f) => (
          <button
            key={f}
            className={`posts-filter ${state.filter === f ? "active" : ""}`}
            onClick={() => setFilter(f)}
          >
            {f.toUpperCase()}
          </button>
        ))}
        <span className="posts-divider">|</span>
        <input
          className="posts-search"
          value={qDraft}
          onChange={(e) => setQDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submitSearch()}
          placeholder="Search title…"
        />
        <button onClick={submitSearch}>Search</button>
      </div>

      {state.loading && <div className="memory-empty">Loading posts from r/{name}…</div>}
      {!state.loading && state.items.length === 0 && (
        <div className="memory-empty">No posts match these filters.</div>
      )}

      {state.items.map((p) => (
        <div key={p.post_id} className="memory-post">
          <a href={p.permalink} target="_blank" rel="noopener noreferrer" className="memory-post-title">
            {p.title}
          </a>
          <div className="memory-post-meta">
            <span className={`tag ${p.tag}`}>{p.tag.toUpperCase()}</span>
            {p.flair && <span className="memory-post-flair">{p.flair}</span>}
            <span>{p.upvotes} upvotes</span>
            <span>{p.num_comments} comments</span>
            {p.created_utc && (
              <span>{new Date(p.created_utc).toLocaleDateString()}</span>
            )}
            <span className="memory-post-gate">via {p.qualifying_gate}</span>
          </div>
          {p.summary && <div className="memory-post-summary">{p.summary}</div>}
        </div>
      ))}

      {/* Pager for posts list */}
      {state.total > PAGE_SIZE && (
        <div className="memory-pager">
          <button
            disabled={state.page <= 1}
            onClick={() => onChange(state.page - 1, state.sortBy, state.order, state.filter, state.q)}
          >
            ← Previous
          </button>
          <span>Page {state.page} of {totalPages}</span>
          <button
            disabled={state.page >= totalPages}
            onClick={() => onChange(state.page + 1, state.sortBy, state.order, state.filter, state.q)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
