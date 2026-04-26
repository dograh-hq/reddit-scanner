// Promotional / Launch Bank dashboard - permanent archive of posts where the author was
// promoting / launching / mentioning something they built (detected at workflow Step 2.5).
"use client";

import { useState, useEffect, useCallback } from "react";
import { Tour, type TourStep } from "../Tour";

// Tour steps for /promo. Most important step is the subreddit filter — the dropdown
// is sorted by promo-post count DESC, and crossposts contribute to EVERY subreddit they
// appeared in, so the per-subreddit number is intentionally cross-post-aware.
const PROMO_TOUR_STEPS: TourStep[] = [
  {
    id: "tour-pagination",
    title: "Pagination",
    body: "20 promo posts per page. Same Prev / Next mirrored at the bottom — use whichever is closer.",
  },
  {
    id: "tour-promo-row1",
    title: "Sort + Validation tag",
    body: "Sort by upvotes / comments / Reddit publish date. Validaiton Tag filter is whether post is relevant(PASS) or not.",
  },
  {
    id: "tour-promo-subreddit",
    title: "Subreddit filter",
    body: "Each option: '<unbiased> · <total>'. Sorted by UNBIASED count desc — descending order of promo posts found via blind keyword fetches (no subreddit pre-selection). The total includes URL-mode fetches and is biased by how often you fetched each sub. Filtering returns posts whose subreddit_sources include the picked sub.",
  },
  {
    id: "tour-promo-type",
    title: "Promo style",
    body: "LAUNCH / BUILT / PROMO / SUBTLE. Hover for full names. SUBTLE = the soft Reddit plugs worth studying.",
  },
  {
    id: "tour-promo-search",
    title: "Title search",
    body: "Substring match. Combines with the filters above.",
  },
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8007";
const PAGE_SIZE = 20;

// Reused sessionStorage key from page.tsx (must stay in sync)
const getStoredPassword = (): string | null => sessionStorage.getItem("access_password");

interface SubredditSource {
  subreddit: string;
  subreddit_subscribers: number;
  permalink: string;
}

interface PromoRow {
  post_id: string;
  title: string;
  body_excerpt: string | null;
  permalink: string;
  primary_subreddit: string;
  subreddit_sources: SubredditSource[];
  author: string | null;
  flair: string | null;
  upvotes: number;
  num_comments: number;
  created_utc: string | null;
  promo_type: string;
  promo_reasoning: string | null;
  validation_tag: string | null;  // null = unrated yet
  source_task_id: string;
  detected_at: string;
}

/** Format subscriber count as "21k" — same helper duplicated in memory page; kept local for self-containment. */
function fmtK(n: number | undefined | null): string {
  if (!n || n < 0) return "0k";
  return `${Math.round(n / 1000)}k`;
}

const PROMO_TYPES = ["all", "launch", "built-something", "self-promo", "subtle-mention"] as const;
const TAG_FILTERS = ["all", "pass", "unsure", "fail", "unrated"] as const;
type PromoType = (typeof PROMO_TYPES)[number];
type TagFilter = (typeof TAG_FILTERS)[number];

export default function PromoPage() {
  // Auth: hydrate from sessionStorage; the user signs in on the main page first
  const [password, setPassword] = useState<string>("");
  const [needsAuth, setNeedsAuth] = useState<boolean>(false);

  const [items, setItems] = useState<PromoRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  // `detected` sort was removed — created_utc covers freshness; detected_at is just "when the workflow ran"
  const [sortBy, setSortBy] = useState<"upvotes" | "comments" | "date">("upvotes");
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [tagFilter, setTagFilter] = useState<TagFilter>("all");
  const [promoType, setPromoType] = useState<PromoType>("all");
  const [subreddit, setSubreddit] = useState<string>("");  // "" = all subreddits
  // Aggregate {subreddit, keyword_count, total_count} for the dropdown; populated once + when password changes.
  // Sorted by keyword_count DESC server-side (unbiased view) — first option is the sub with the most
  // promo posts found via blind keyword fetches, NOT the one we happened to fetch from most.
  const [subAgg, setSubAgg] = useState<Array<{ subreddit: string; keyword_count: number; total_count: number }>>([]);
  const [qDraft, setQDraft] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  // Hydrate password on mount
  useEffect(() => {
    const stored = getStoredPassword();
    if (!stored) { setNeedsAuth(true); return; }
    setPassword(stored);
  }, []);

  /** authFetch: GET with X-Access-Password header; sets needsAuth on 401 */
  const authFetch = useCallback((url: string) => {
    return fetch(url, { headers: { "X-Access-Password": password } });
  }, [password]);

  // Fetch list whenever any query input changes
  useEffect(() => {
    if (!password) return;
    let cancelled = false;
    setLoading(true);
    const params = new URLSearchParams({
      page: String(page), page_size: String(PAGE_SIZE),
      sort_by: sortBy, order, filter: tagFilter, promo_type: promoType,
    });
    if (subreddit) params.set("subreddit", subreddit);
    if (q.trim()) params.set("q", q.trim());
    authFetch(`${API_BASE}/promotional?${params}`)
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then((data) => { if (!cancelled) { setItems(data.items); setTotal(data.total); } })
      .catch((s) => { if (s === 401) setNeedsAuth(true); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [page, sortBy, order, tagFilter, promoType, subreddit, q, password, authFetch]);

  // Fetch subreddit→count aggregate once we have a password. Refreshed whenever the user
  // returns to the page (mount). The dropdown shows totals at fetch time — slightly stale
  // is fine since the bank only grows.
  useEffect(() => {
    if (!password) return;
    let cancelled = false;
    authFetch(`${API_BASE}/promotional/subreddits`)
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then((data) => { if (!cancelled) setSubAgg(data); })
      .catch(() => { /* non-fatal — dropdown just stays empty */ });
    return () => { cancelled = true; };
  }, [password, authFetch]);

  // Reset to page 1 whenever a filter / sort changes (page itself is excluded)
  const resetAndSet = (fn: () => void) => { setPage(1); fn(); };

  if (needsAuth) {
    return (
      <div className="memory-container">
        <a href="/" className="back-link">← Back to runs</a>
        <h1>Promotional / Launch Bank</h1>
        <div className="memory-empty">Please sign in on the main page first, then return here.</div>
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="memory-container">
      <a href="/" className="back-link">← Back to runs</a>
      <div className="page-header-row">
        <h1>🚀 Promotional / Launch Bank</h1>
        {/* Top pager — always rendered (Prev/Next disable when only 1 page) so the user
            always sees the pagination affordance. ID drives the guided-tour step. */}
        <div id="tour-pagination" className="memory-pager memory-pager-top" title="20 promo posts per page — Prev / Next to navigate. Same pager mirrored at the bottom.">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>← Prev</button>
          <span>Page {page} of {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      </div>
      <p className="promo-intro">
        Posts where the author is launching, building, or subtly mentioning something they made.
        Style references for our own promotional posts.
      </p>

      {/* Row 1: Sort buttons + Validation tag filters share one toolbar line, total/pager on the right */}
      <div id="tour-promo-row1" className="memory-toolbar">
        <div className="posts-toolbar" style={{ margin: 0 }}>
          <span className="posts-label">Sort by:</span>
          {(["upvotes", "comments", "date"] as const).map((k) => (
            <button
              key={k}
              className={`posts-sort ${sortBy === k ? "active" : ""}`}
              onClick={() => resetAndSet(() => {
                if (sortBy === k) setOrder((o) => (o === "desc" ? "asc" : "desc"));
                else { setSortBy(k); setOrder("desc"); }
              })}
            >
              {k === "upvotes" ? "Upvotes" : k === "comments" ? "Comments" : "Date"}
              {sortBy === k && <span> {order === "desc" ? "↓" : "↑"}</span>}
            </button>
          ))}
          <span className="posts-divider">|</span>
          <span className="posts-label">Validation tag:</span>
          {TAG_FILTERS.map((f) => (
            <button
              key={f}
              className={`posts-filter ${tagFilter === f ? "active" : ""}`}
              onClick={() => resetAndSet(() => setTagFilter(f))}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
        <span className="memory-toolbar-meta">
          {total} post{total === 1 ? "" : "s"} · page {page} of {totalPages}
        </span>
      </div>

      {/* Row 2: Subreddit dropdown (LEFT) + Promo type filters (RIGHT, smaller) + title search */}
      <div className="memory-toolbar">
        <div className="posts-toolbar" style={{ margin: 0 }}>
          <span className="posts-label">Subreddit:</span>
          <select
            id="tour-promo-subreddit"
            className="promo-sub-select"
            value={subreddit}
            onChange={(e) => resetAndSet(() => setSubreddit(e.target.value))}
          >
            {/* "All" option shows the totals across all subreddits — both unbiased + total */}
            <option value="">
              All subreddits ({subAgg.reduce((n, x) => n + x.keyword_count, 0)} unbiased ·{" "}
              {subAgg.reduce((n, x) => n + x.total_count, 0)} total)
            </option>
            {/* Per-sub options: '<unbiased> · <total>'. Backend sorts by keyword_count DESC,
                so the most organically-promoting subs lead the list. */}
            {subAgg.map((s) => (
              <option key={s.subreddit} value={s.subreddit}>
                r/{s.subreddit} ({s.keyword_count} unbiased · {s.total_count} total)
              </option>
            ))}
          </select>
          <span className="posts-divider">|</span>
          <span id="tour-promo-type" className="posts-label">Promo type:</span>
          {PROMO_TYPES.map((p) => (
            <button
              key={p}
              className={`posts-filter promo-type-btn ${promoType === p ? "active" : ""}`}
              onClick={() => resetAndSet(() => setPromoType(p))}
              title={p}
            >
              {/* Shortened display labels — canonical filter values (e.g. "subtle-mention")
                  are unchanged in the API call; only the button text shrinks. */}
              {p === "all" ? "ALL"
                : p === "launch" ? "LAUNCH"
                : p === "built-something" ? "BUILT"
                : p === "self-promo" ? "PROMO"
                : "SUBTLE"}
            </button>
          ))}
        </div>
        <input
          id="tour-promo-search"
          className="posts-search"
          value={qDraft}
          onChange={(e) => setQDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && resetAndSet(() => setQ(qDraft))}
          placeholder="Search title…"
        />
        <button onClick={() => resetAndSet(() => setQ(qDraft))}>Search</button>
      </div>

      {loading && <div className="memory-empty">Loading…</div>}
      {!loading && items.length === 0 && (
        <div className="memory-empty">
          No promotional posts archived yet. Run a workflow — Step 2.5 will detect and persist them.
        </div>
      )}

      {items.map((p) => (
        <div key={p.post_id} className="memory-post promo-post">
          <a href={p.permalink} target="_blank" rel="noopener noreferrer" className="memory-post-title">
            {p.title}
          </a>

          <div className="memory-post-meta">
            <span className={`promo-type-badge promo-type-${p.promo_type}`}>{p.promo_type}</span>
            {p.validation_tag
              ? <span className={`tag ${p.validation_tag}`}>{p.validation_tag.toUpperCase()}</span>
              : <span className="tag error">UNRATED</span>}
            {p.flair && <span className="memory-post-flair">{p.flair}</span>}
            <span>{p.upvotes} upvotes</span>
            <span>{p.num_comments} comments</span>
            {p.created_utc && <span>{new Date(p.created_utc).toLocaleDateString()}</span>}
            {p.author && <span>u/{p.author}</span>}
          </div>

          {/* All subreddits this canonical post was found in (cross-posts get one chip each) */}
          {p.subreddit_sources && p.subreddit_sources.length > 0 && (
            <div className="post-sources" style={{ marginTop: 6 }}>
              {p.subreddit_sources.map((s, i) => (
                <span key={s.subreddit + i} className="post-source-chip">
                  <a href={s.permalink} target="_blank" rel="noopener noreferrer">
                    [Link{p.subreddit_sources.length > 1 ? ` ${i + 1}` : ""}]
                  </a>
                  <span className="post-source-name"> r/{s.subreddit}</span>
                  <span className="post-source-subs"> {fmtK(s.subreddit_subscribers)}</span>
                </span>
              ))}
            </div>
          )}

          {p.body_excerpt && <pre className="promo-body-excerpt">{p.body_excerpt}</pre>}

          {p.promo_reasoning && (
            <div className="reasoning-box" style={{ marginTop: 8 }}>
              <strong>Why flagged:</strong> {p.promo_reasoning}
            </div>
          )}
        </div>
      ))}

      <div className="memory-pager" title="20 promo posts per page — also available at the top right of the page heading">
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>← Previous</button>
        <span>Page {page} of {totalPages}</span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage((p) => p + 1)}
        >
          Next →
        </button>
      </div>

      <Tour steps={PROMO_TOUR_STEPS} storageKey="tour_promo_seen" />
    </div>
  );
}
