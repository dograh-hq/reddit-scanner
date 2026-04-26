# CHANGES.md

## 2026-04-27 - Unbias the bank aggregates: keyword-finds counter as default sort

### The bias problem
Per-subreddit counts in both Memory Bank and Promo Bank were inflated by URL-mode runs. `r/SaaS: 50 promos` could mean "r/SaaS is genuinely promo-heavy" OR "the user fetched r/SaaS 5 times" — indistinguishable. Keyword-mode runs are bias-free (Reddit's keyword search has no subreddit pre-selection); URL-mode runs are biased by fetch frequency.

### Fix
Maintain a separate counter — posts discovered via keyword fetches only — alongside the existing total. Surface this UNBIASED counter as the default sort on both dashboards. Show both numbers side-by-side in subreddit labels: `5 unbiased · 12 total`.

### Backend
- **Schema migration** (`backend/storage.py:_init_db`): `ALTER TABLE memory_posts ADD COLUMN source_input_type TEXT` and same for `promotional_posts`. Wrapped in `try/except OperationalError` so re-runs are no-ops. New indices: `idx_mp_sub_source`, `idx_pp_source`.
- **One-time backfill** (`_backfill_source_input_type`): walks the in-memory `_tasks` cache after `_load_all()` runs, populates `source_input_type` for bank rows whose `source_task_id` is still cached. Older rows (source task aged out) stay NULL → counted in `total` but NOT `unbiased`. Verified live: backfilled 35 memory_posts + 32 promotional_posts on first restart.
- **`save_memory_posts(rows, source_input_type)` / `save_promotional_posts(rows, source_input_type)`** — required new arg. `source_input_type` is intentionally OMITTED from the promo UPSERT's `DO UPDATE SET` (first-seen mode wins, matching `detected_at` / `source_task_id` preservation).
- **`list_memory_subreddits(..., sort_by="keyword_finds")`** — new default. Whitelist is now `keyword_finds | posts | members`. Always LEFT JOINs a derived per-sub keyword count from `memory_posts WHERE source_input_type='keywords'` so EVERY response row carries both `post_count` (total) and `keyword_count` (unbiased) regardless of the active sort.
- **`list_promotional_subreddits()`** — response shape changed from `[{subreddit, count}]` to `[{subreddit, keyword_count, total_count}]`. Single query with `SUM(CASE WHEN source_input_type = 'keywords' ...)`. Sorted by `keyword_count DESC, total_count DESC, sub ASC`.
- **`backend/workflow.py`**: `_collect_memory_bank` and the Step 2.5 promo persistence call both pass `task.input_type` through to the new `source_input_type` arg.
- **`backend/main.py`**: `/memory/subreddits` default `sort_by` is now `"keyword_finds"`; `/promotional/subreddits` returns the new shape.

### Frontend
- **`/memory`**: sort buttons array becomes `["keyword_finds", "posts", "members"]` with `keyword_finds` first + default. Active label: `Keyword finds (unbiased)`. Per-sub row meta line changed from `12 posts · last <date>` to `<bold>5</bold> unbiased · 12 total · last <date>` (unbiased on the LEFT).
- **`/promo`**: subreddit dropdown options now show `r/SaaS (7 unbiased · 35 total)`, sorted server-side by unbiased count desc. The `All subreddits` option likewise shows summed `unbiased · total`.
- **Tours**: `/memory` and `/promo` tour steps rewritten to explain the unbiased / "blind fetch" concept and why the default sort exists.

### No backward-compatibility concerns
This project is in dev — old API param values + response shapes were replaced cleanly without legacy aliases. Per user preference: "no need to do anything for backward compatibility."

### Verification
- Backend smoke: 5-row hermetic test inserted SmokeKw (keywords mode) + SmokeUrl (urls mode); `list_memory_subreddits(sort_by="keyword_finds")` returned SmokeKw above SmokeUrl as expected. Promo aggregate same — SmokeKw with keyword_count=1 sorted above SmokeUrl with keyword_count=0. All checks passed.
- Frontend `npx tsc --noEmit`: clean.

---

## 2026-04-27 - Tour text trimmed + input-control tooltips + pagination tooltips + results-area placeholder + post-run walkthrough toast

### Tour gating (verified — no changes needed)
Audited the auth + sessionStorage flow. Tours fire **once per login** thanks to:
- `tour_*` flags in sessionStorage (auto-cleared on tab close, manually cleared on `handleLogin` + `handleLogout` via `resetTourFlags`)
- Auto-verify on mount calls `setIsAuthenticated(true)` WITHOUT touching tour flags, so refresh + navigation don't re-trigger
- The Tour component reads its flag once on mount; if "1" it returns early and never re-fires for the lifetime of the component
- All new flags use the `tour_*` prefix so `resetTourFlags()` (which loops sessionStorage and removes anything starting with `tour_`) catches them automatically
- No backend / JWT involvement — gating is purely browser-side

### Frontend
- **All tour step text shortened** — dropped verbose phrasing (e.g. "the 7-day cleanup never touches them"), kept the punchy core. Each step now ~1–2 short sentences.
- **Native title-attr tooltips on input controls**: every keyword-mode and URL-mode dropdown (Sort, Time frame, Posts per keyword) plus their wrapping `<label>` carries a hover tooltip explaining what the option does.
- **Pagination tooltips** on top + bottom pagers in `/memory` and `/promo` (e.g. `20 promo posts per page — also available at the top right of the page heading`).
- **Verified `/memory` top-right pagination**: confirmed in `memory/page.tsx:173-187` — wrapped in `.page-header-row`, only renders when `subTotal > PAGE_SIZE`. Bottom pager retained for redundancy.
- **`<ResultsExample>` placeholder** (new file): annotated example layout shown when `!results && !status`. Mirrors the real Selected / Suggestions / Rejected sections with explainer captions baked into the JSX (post-card with dashed border, callout strips after each anchor element). Replaced by real results the moment the workflow produces data.
- **Post-run results-tour toast**: 3 seconds after `results.status` becomes `"complete"` for the first time this session, a fixed-position toast (`.results-toast`) prompts the user with `Yes, show me` / `No thanks`. Yes mounts `<Tour>` over the actual rendered sections (`tour-results-section-1` / `-section-2` / `-rejected` / `tour-prompt-debugger`). Both decisions persist via `tour_results_toast_seen` + `tour_results_seen` so neither fires again this session. Both flags cleared on next login/logout.

---

## 2026-04-27 - Promo refinements (round 2): top pagination, expandable-row cue, login tour, idempotency-counter fix

### Backend fix
- **`storage.save_promotional_posts` idempotency counter** was overcounting re-inserts because SQLite's UPSERT (`INSERT ... ON CONFLICT DO UPDATE`) reports `cur.rowcount = 1` for both INSERT and UPDATE paths. The actual DB state was correct (no duplicate rows because `post_id` is the PK), but the returned count and the workflow log line `archived N new PASS/UNSURE posts` was misleading. Fix: SELECT-probe each `post_id` BEFORE the UPSERT to determine `is_new`. Verified: re-insert now correctly returns 0.

### Backend verified
- **Subreddit aggregate + filter cross-post correctness** — comprehensive 5-row test fixture exercising 3-way crossposts, 1-source posts, idempotent re-inserts, case-insensitive filter, empty `subreddit_sources`, and empty-string source names. All checks pass: a single post crossposted to 3 subreddits contributes +1 to each subreddit's count AND appears in each subreddit's filter result. Empty/null sources are correctly excluded by the WHERE clause. Combined `subreddit + promo_type` filter returns the correct intersection.

### Frontend
- **Count badge text** now reads `6 Posts ≥5 upvotes  9 Posts with <5 ↓` (was `6 ≥5 upvotes · 9 with <5 ↓`); separator dot dropped.
- **Promotional/Launch Bank button** changed to amber (`#d97706`) so the two banks are visually distinct from the main page header.
- **Subreddit Memory Bank rows** got a much more obvious accordion affordance: 4px indigo left-border accent, indigo subreddit name (link-blue), italic "Click to view posts" / "Click to collapse" hint next to the chevron, hover state with deeper indigo + 1px translateX, focus-visible outline. The chevron is now a circular indigo pill.
- **Top pagination** added to both `/memory` and `/promo` — sits to the right of the page title (`<div class="page-header-row">` wrapper). Compact variant (`memory-pager-top`) of the existing pager. Bottom pagination kept for redundancy.
- **`PAGE_SIZE` reduced from 25 → 20** on both bank dashboards (per user preference; backend accepts whatever the frontend sends).
- **Promo type filter buttons further shrunk** (font 9px, padding 2px 5px) AND display labels shortened: `BUILT-SOMETHING` → `BUILT`, `SELF-PROMO` → `PROMO`, `SUBTLE-MENTION` → `SUBTLE`. Canonical filter values sent to the API are unchanged. `title` attribute exposes the full label on hover. The 5 buttons now fit on one line with the subreddit dropdown.
- **Guided login tour** (`Tour.tsx` + per-page step lists). Spotlight effect via huge `box-shadow` cutout + indigo pulsing ring around the highlighted element. Popup card with Step N of M / title / body / Skip / Back / Next controls. Steps whose target IDs aren't on the page are auto-skipped. Per-page sessionStorage flags (`tour_main_seen` / `tour_memory_seen` / `tour_promo_seen`) cleared on every login + logout via `resetTourFlags()`. Main-page tour highlights banks row → history dropdown → input section. /memory tour explains the toolbar + clickable rows. /promo tour pays special attention to the **subreddit filter** (cross-post-aware counting), then promo-type and search.

---

## 2026-04-27 - Comments collapsed by default + low-score jump badge + section rename

### Frontend
- **Section 1 renamed**: `Selected Posts with Comments` → `Selected Posts with Suggested Comments`.
- **Comment suggestions now collapsed by default for ALL Selected cards** (not just <5 upvote ones). Header — title, sources, meta, tag, summary, "Why selected" — stays visible; the comment-box list expands on demand. Suggestions section (Section 2) is unchanged: high-score expanded, low-score collapsed.
- **`<LowScoreJump>` badge** rendered on the RIGHT of each section's filter-tab row, e.g. `8 ≥5 upvotes · 12 with <5 ↓`. The `<5` half is a click-to-scroll-anchor that lands on the section's `low-score-banner` div (`sel-low-banner` / `sug-low-banner`). Surfaces the low-signal count without disturbing the high-signal hierarchy. New `.filter-tabs-row` wrapper + `.low-score-counts*` styles.

---

## 2026-04-27 - Promo dashboard refinements + Keywords-default

### Frontend
- **Simpler chip text** on the run results page: `Promotional/Launch` always (no subcategory in the chip, smaller font). The subcategory + LLM reasoning still surface on hover via the title attribute, AND remain visible as colored badges on the `/promo` dashboard cards.
- **Removed `detected` sort** from `/promo` — it just reflected workflow run time; not meaningful for a style-reference bank. `Date` (the post's `created_utc`) covers freshness.
- **Toolbar consolidated**: validation tag filters now share the sort row; subreddit dropdown (LEFT) + smaller promo-type buttons (RIGHT) share a second row with the title search.
- **Subreddit filter dropdown** populated from the new `GET /promotional/subreddits` endpoint. Options sorted by promo-post count DESC, formatted as `r/SaaS (12 Promotions)`. Works across cross-posts (a post matches if ANY of its `subreddit_sources` equals the picked subreddit).
- **Main page radio order swapped**: Keywords first and now the default mode (most common use).

### Backend
- `storage.list_promotional_posts(..., subreddit=...)` adds an `EXISTS … json_each(subreddit_sources)` subquery for case-insensitive cross-post matching.
- `storage.list_promotional_subreddits()` aggregates promo-post counts per subreddit by expanding the `subreddit_sources` JSON via SQLite's `json_each`, GROUP BY subreddit, ORDER BY count DESC.
- `GET /promotional` accepts `subreddit` param; new `GET /promotional/subreddits` returns the dropdown source.

---

## 2026-04-27 - Promotional / Launch detection (Step 2.5) + dedicated archive dashboard

### Reason
Self-promotion and launch posts on Reddit follow specific subtle styles (founders rarely write outright "buy my product" — the high-performing ones are stories with name-drops, "I built X" posts, or feedback asks where the project URL slips in). The user wants a permanent collection of these as style references for our own promotional posts. Capture happens BEFORE any filtering so the archive includes posts that later get rejected by comment/post validation gates.

### Backend
- **New prompt** `prompts/promotional_detection.txt`: returns `[{post_id, is_promotional, promo_type, reasoning}]` with `promo_type` ∈ `launch | built-something | self-promo | subtle-mention | none`. Generous detection bias — better to over-flag than miss subtle plugs.
- **New LLM helper** `llm_client.detect_promotional_posts_batch(posts)`: one batched call, mapped back by `post_id` (drops hallucinated/missing ids per the existing `id_to_index` pattern). Body excerpt capped at 800 chars per post — promo signals usually surface in opening lines.
- **New workflow Step 2.5** in `workflow.py`: runs right after dedup (Step 2) and BEFORE the score filter pass-through (Step 3). Persists `is_promotional=true` rows to the new `promotional_posts` SQLite table with `validation_tag=NULL`. After Steps 6 + 9 finish, `_backfill_promo_validation_tags()` upgrades each row's `validation_tag` to the BEST available verdict (PASS > UNSURE > FAIL) drawn from `comment_validations` + `post_validations`.
- **New SQLite table** `promotional_posts` (PK `post_id`; one row per canonical post; `subreddit_sources` stored as JSON to keep cross-post info in one row). Indexes on upvotes / num_comments / created_utc / validation_tag / promo_type for the dashboard sort+filter combinations. **Permanent** — cleanup loop never touches it (mirrors Memory Bank invariant).
- **New storage helpers**: `save_promotional_posts(rows)` (idempotent on `post_id`, UPSERTs metadata so re-runs refresh upvote counts), `update_promotional_validation(post_id, tag)`, `list_promotional_posts(...)` paginated/sorted/filtered.
- **New API endpoint** `GET /promotional?page&page_size&sort_by&order&filter&promo_type&q` — drives the dashboard. `filter`: `all|pass|unsure|fail|unrated`. `promo_type`: `all|launch|built-something|self-promo|subtle-mention`.
- **Existing `/results` endpoint** now also returns `promotional_detections: [...]` so the main page can render the chip on every card.

### Frontend
- **New `<PromoChip>` component** in `page.tsx`: small purple chip rendered inside a new `.tag-group` container next to PASS/UNSURE/FAIL on Selected, Suggestions, AND Rejected cards. Tooltip surfaces the LLM's reasoning. Color-coded by `promo_type` on the dashboard but a single purple chip on the run results (where it just signals "promotional, click through to /promo for details").
- **New header button** `🚀 Promotional / Launch Bank` next to `📚 Subreddit Memory Bank`.
- **New route** `/promo/page.tsx` (mirrors `/memory` structure): paginated list, sort by upvotes/comments/date/detected, separate filter rows for validation_tag and promo_type, title text-search, expandable card showing first 3 lines of the body excerpt + all subreddit sources (with member counts) + LLM reasoning. Auth flow reuses sessionStorage password from main page.
- **CSS additions** in `globals.css`: `.tag-group`, `.promo-chip` (violet pill), and `/promo` dashboard styles incl. four color-coded `.promo-type-*` badges.

### Why SQLite (not Mongo)
Same shape as Memory Bank — bounded growth, single-writer, JSON columns for nested data, simple indexed queries. Mongo would only matter for sharding / cross-region replication, neither of which apply.

### Cost impact
+1 batched LLM call per workflow run (~5–10K tokens for typical 35-post batch). Step 2.5 is non-fatal — failures are logged to `error_log` and the workflow continues without promo detection.

---

## 2026-04-24 - Removed score filter; UI partitions low-score posts into collapsed sub-section

### Reason
Backend was dropping ~60% of canonical posts at Step 3 via `min_score=5` (a recent keyword run produced 35 deduped posts → only 14 reached the LLM). User wants every canonical post to flow through the full pipeline regardless of upvote count, with low-signal posts visually demoted in the UI rather than discarded server-side.

### Backend
- **`workflow.py` Step 3**: removed the `filter_posts_by_score(...)` call; `filtered = all_posts` now passes everything downstream. Removed unused `min_score` config read and the `filter_posts_by_score` import. Step log now reads `Step 3: N posts (no score filter)`. The helper itself is left in `apify_client.py` (zero callers now, but harmless and avoids extra churn).

### Frontend
- **`page.tsx` — partition + collapse for low-score posts**: added `LOW_SCORE_THRESHOLD = 5`. New `partitionByScore()` helper splits both `selectedPostsWithComments` and `postSuggestions` into `{ high, low }` by the underlying `filtered_posts[i].score`. Inside each of the two results sections, high-score cards render at top exactly as before; below them an italic banner — *"↓ Below posts have lower upvotes (less than 5)"* — introduces the low-score group. Low-score cards keep their header (title, sources, meta, tag, summary, "Why selected" / "Why it scores well" reasoning) always visible; the secondary content (comment-box list for Section 1, strategy-box for Section 2) sits behind a click-to-expand `<CollapsibleBody>` toggle.
- **Refactored card render into closures**: extracted `renderSelectedCard(gc, lowScore)` and `renderSuggestionCard(ls, lowScore)` so both groups share one definition and only the `lowScore` flag changes. Closures live inside `Home` to keep access to `results`, `getCommentTag`, `getPostTag`, `getPostSummary`, `getEvaluationReasoning`.
- **`globals.css`**: added `.post-card.low-score` (slate-100 background, slate-300 border — clearly demoted but readable with the same fonts), `.low-score-banner` (small italic muted slate divider), and `.collapsible-toggle` (chevron button styling).

### Out of scope
- Rejected Posts section unchanged.
- `filter_posts_by_score` helper kept in place to minimize diff.
- Memory Bank archiving is unaffected; low-score posts that earn PASS/UNSURE during validation will now land in the bank — desirable side-effect.

---

## 2026-04-26 - Memory Bank UI fixes (visibility / labels / sort by members / Invalid Date)

### Fixed
- **Subreddit name invisible** (`globals.css`): `.sub-row` is a `<button>` and inherited the global `button { color: white }` rule, making `r/SubredditName` text white-on-white. Added explicit `color: #1f2937` on `.sub-row`.
- **"Invalid Date"** in post rows (`memory/page.tsx`): Apify returns `created_utc` as ISO 8601 string (`"2026-04-20T19:51:08.000Z"`), not a Unix epoch number. `new Date(p.created_utc * 1000)` was multiplying a string by 1000 → `NaN` → "Invalid Date". Changed to `new Date(p.created_utc)`. Updated `PostRow.created_utc` type from `number | null` → `string | null`.

### Added
- **Sort by members** for the subreddit list. New `subSort: "posts" | "members"` state in `memory/page.tsx`; backend `list_memory_subreddits` accepts a whitelisted `sort_by` param and `GET /memory/subreddits?sort_by=members` is exposed. Toolbar replaced with a labeled 2-button strip (`Sort by: [Posts ↓] [Members ↓]`) — clicking the active button toggles asc/desc.
- **"Sort By:" / "Filter Posts:" labels** added to the per-subreddit posts toolbar so the buttons are no longer ambiguous. New `.posts-label` CSS class.

---

## 2026-04-26 - Hidden-drops audit fixes (output truncation, JSON salvage, dedup hardening)

### Fixed (root causes of "all posts not getting evaluated")
- **Bedrock output truncation**: `_call_llm` now sets `inferenceConfig.maxTokens=32000` in the Converse payload. Without it Bedrock applied the model default (~4K), causing batches over ~30 posts to truncate mid-array and silently drop posts via JSON parse failure. Opus 4.7's ceiling is 128K; 32K covers our worst-case batch (5 keywords × 20 posts × ~200 tok/entry ≈ 20K) with safe headroom.
- **Silent `id_to_index` drops surfaced**: `workflow.py` now logs to `task.error_log` after step 4 and step 7 when the LLM returns fewer entries than input ("Step 4: LLM returned X/Y posts; Z silently dropped"). Previously these only hit `logger.warning` which never reached the UI.
- **Dedup max-score merge** (`apify_client._dedupe_and_merge`): when collapsing duplicates / crossposts, the canonical now keeps MAX `score`, MAX `num_comments`, and the LONGER `body` across all copies. Previously the first-seen copy's metadata won — a popular crosspost surfaced first via a low-score sub could be filtered out by `score >= min_score`.
- **Dedup length guard** (`apify_client._canonical_key`): `(title, author)` merging only kicks in when `len(title) >= 20`. Short generic titles like "Help" or "Question" by frequent authors no longer false-merge into a single canonical entry.

### Fixed (UI bug from screenshot — "Comment Suggestion 1 broken, Comment 2 empty")
- **Hardened JSON parser** (`_parse_json_response`): tries 4 candidates in order — ```json fence, bare ``` fence, raw response, slice from first `{` to last `}`. Returns the first that parses. Previously only handled ```json fences.
- **Regex salvage in `generate_comments`**: when JSON parse fails entirely, scope a regex search to the `"comments": [...]` array region (handles both closed-bracket and truncation cases), pull double-quoted strings, JSON-decode escapes, take the longest 2 as the comment bodies. If even salvage finds nothing, returns `["[LLM output could not be parsed — see Prompt Debugger panel]", ""]` instead of dumping the entire raw blob into comment 1. Two-stage scoping prevents the salvage from ever falling back to "any quoted string in the whole response."

### Audit
- Two parallel audit agents + one top-level reviewer ran against the recent dedup work.
- Auditor 1 (dedup re-read) flagged the first-seen-score risk as "most impactful." Fixed via max-score merge.
- Auditor 2 (hidden truncation) identified missing `maxTokens` and silent `id_to_index` drops as the most likely cause of the user's "posts not getting evaluated" symptom. Both fixed.
- Reviewer pushed back on the original `maxTokens=16000` (only 1K headroom for 100-post batches) — bumped to 32000. Also pushed back on the regex salvage's failure mode when `]` is truncated — added explicit two-stage scoping.

---

## 2026-04-26 - Cross-post dedup w/ multi-subreddit attribution + subscriber counts + bullet strategies

### Backend
- **Smarter dedup** (`apify_client._dedupe_and_merge`): canonical key is `(title, author)` (lowercased) which collapses both exact-id duplicates AND Reddit cross-posts into one canonical post. Each canonical post carries a new `subreddit_sources: list[{subreddit, subreddit_subscribers, permalink}]` field listing every subreddit it appeared in. Replaces the old per-source `seen_ids` dedup loops in `fetch_multiple_subreddits` / `fetch_multiple_keywords`.
- **`subreddit_subscribers` propagation**: read from each Apify post and stored on every `subreddit_sources` entry, then used downstream for Memory Bank + UI display.
- **Memory Bank schema migration** (project pre-production; user explicitly waived backward compat):
  - `memory_posts` PK changed from `post_id` (singular) to **composite `(post_id, subreddit)`** so the same canonical post can be saved against every subreddit it crossposted to.
  - Added `subreddit_subscribers` column on both `memory_posts` and `memory_subreddits`.
  - `_init_db` detects the OLD single-PK schema (no `subreddit_subscribers` column) and DROPs + recreates both memory tables on first startup. One-time, prints a migration log line.
- **`save_memory_posts`** rewritten: writes one row per (post_id, subreddit) pair; always refreshes the rollup's `subreddit_subscribers` (latest known value wins) but only increments `post_count` on first-save for that pair.
- **`_collect_memory_bank` in workflow**: iterates each qualifying canonical post's `subreddit_sources` and emits one row per subreddit. Cross-posted PASS/UNSURE posts are now credited to ALL subreddits they appeared in.
- **`prompts/post_rewrite.txt`** rewritten: strategy is now a JSON-array of items where each `strategy` is a markdown bullet list of short phrases (Channel / Tone / Hook / Angle / Body / CTA), under ~12 words per bullet. Optimized for scannability.

### Frontend
- **New `Post.subreddit_sources` field** on the `Post` type. Powers a new compact `<PostSourcesLine>` component shown under every Selected/Suggestions card title: `[Link 1] r/SaaS 21k  [Link 2] r/Entrepreneur 5k`. Each `[Link N]` opens that subreddit's specific permalink in a new tab. Single-source posts render as `[Link] r/AI_Agents 50k` (no number).
- **Strategy rendered as `<ul>`** of phrases (parsed from the prompt's markdown bullets). New `.strategy-bullets` class with small font + tight line-height.
- **Memory Bank dashboard** (`/memory`): subreddit row now shows `r/SaaS · 21k members` next to the name. Subscriber count comes from the rollup table, refreshed on every save.
- **`fmtK` helper**: rounds to thousands; sub-1000 counts render as `0k` per spec. Duplicated in `memory/page.tsx` to keep the route self-contained.
- New CSS: `.post-sources`, `.post-source-chip`, `.post-source-name`, `.post-source-subs`, `.strategy-bullets`, `.sub-subscribers`.

### Why
User feedback: (a) duplicate posts (cross-posts) were being treated as separate items; (b) when a post was crossposted, the UI only showed one subreddit; (c) subreddit "size" was missing from the Memory Bank — couldn't tell `r/SaaS` (~250k) apart from `r/tinysub` (~500); (d) post-suggestion strategy paragraphs were hard to scan and the user wanted bullet phrases. Project is pre-production so this also took the chance to migrate Memory Bank schema cleanly without backward-compat shims.

---

## 2026-04-26 - Prompt Debugger UI + Subreddit Memory Bank + comment/suggestion font polish

### Added — Prompt Debugger (debug panel)
- **Backend capture**: `LLMClient` now keeps a per-instance `call_log` list and instruments `_call_llm` to record `{seq, call_type, step_name, group_id, prompt, response, input_tokens, output_tokens, total_tokens, started_at, finished_at, success, error}` for every call (including failed ones). `step_name` and `group_id` are passed by each batched method; for Step 5 the workflow mints a single `uuid` so all parallel comment-generation calls share one `group_id`.
- **TaskData**: new `llm_calls: list[dict]` field; `_log_step` snapshots `llm.call_log` at every step boundary so progressive polling sees the debugger data populate live.
- **API**: `GET /results/{task_id}` now returns `llm_calls`.
- **Frontend `<PromptDebugger>`** component: 100%-width fixed bar at the bottom of the page, collapsed by default (36px high). Expanding reveals a multi-level accordion: Step → (Parallel batch | single batched call) → leaf with full prompt + response. Newlines render literally (`<pre white-space: pre-wrap>`). Each leaf shows in/out/total tokens; bar shows grand totals.
- **CSS**: new `.prompt-debugger`, `.pd-step`, `.pd-group`, `.pd-leaf`, `.pd-prompt`, `.pd-response` classes. Page bottom padding reserves room for the collapsed bar.

### Added — Subreddit Memory Bank
- **Schema**: 2 new SQLite tables — `memory_posts` (PK `post_id`, indexed by `(subreddit, num_comments DESC)`, `(subreddit, upvotes DESC)`, `(subreddit, created_utc DESC)`, `(subreddit, tag)`) and `memory_subreddits` (PK `subreddit`, denormalized `post_count` + `last_saved_at`, indexed by `post_count DESC`). Permanent — no expiry.
- **Collector**: `workflow._collect_memory_bank(task)` runs in Step 10. Walks `comment_validations` and `post_validations`; archives every post whose validation tag is PASS or UNSURE on either gate. Idempotent on `post_id` (re-saving from a future run is a silent no-op). Records the best tag (PASS beats UNSURE) and which gate qualified it (`comment` | `post` | `both`). Failure is logged but never fails the run.
- **Endpoints**:
  - `GET /memory/subreddits?page=1&page_size=25&order=desc|asc` — paginated subreddit list.
  - `GET /memory/subreddits/{name}/posts?page=1&page_size=25&sort_by=comments|upvotes|date&order=desc|asc&filter=all|pass|unsure&q=<title-search>` — paginated posts within a subreddit, with sort, filter, and title text-search.
- **New frontend route `/memory`** (`frontend/app/memory/page.tsx`): standalone dashboard with paginated subreddit accordions (default sort: most posts first; toggleable). Click a subreddit → fires `/memory/subreddits/{name}/posts` (only on click, never preloaded). Inside: sort buttons (Comments / Upvotes / Date — toggleable asc/desc), filter (All / Pass / Unsure), title search box, paginated list. Each post: clickable title opens permalink in new tab (`rel="noopener noreferrer"`), tag chip, flair, upvotes, comments, date, qualifying-gate label, summary.
- **Header restructure on main page**: new `.header-actions` row — **"📚 Subreddit Memory Bank"** button on the left (links to `/memory`), History dropdown moved to the right. Removed the standalone `.history-section` row.
- **SQLite vs MongoDB verdict**: SQLite is more than enough. Single user, single writer, paginated reads with simple sorts/filters; the new tables are properly indexed. Mongo would add infra and zero queryability gain at this volume.

### Changed — comment + suggestion typography (per user)
- `.comment-text`: 13 → **10px** ("smaller by 3").
- `.comment-score`: 12 → **10px** ("smaller by 2"), color `#666` → **`#6b46c1`** (muted purple, visible on both white card and the light-blue strategy-box bg), italic for additional differentiation. Same class is reused by the suggestion validation reasoning at the bottom of each strategy card, fixing the user's "getting mixed up" complaint.

### Reason
User wanted (a) a debug surface to see the exact prompts sent to Bedrock (debug + future prompt refinement), (b) a permanent index of high-signal subreddits/posts that survives any single run, (c) visible delineation between a comment's body and its score line. All four UX changes shipped together because they share the storage / endpoint / page layer touch-points.

---

## 2026-04-26 - Dedup + scoring threshold + UI side-by-side + history-input

### Fixed
- **Cross-source duplicate posts**: `apify_client.fetch_multiple_subreddits` and `fetch_multiple_keywords` previously did `all_posts.extend(result)` with no dedup, so cross-posted submissions and posts matching multiple keywords appeared multiple times. Now we dedupe by `post.id` while preserving first-seen order, and log the drop count. Root cause behind the user-reported "same post in both Selected and Rejected" bug.
- **Frontend rejected-posts collision**: `rejectedPosts` previously used `filtered_posts.indexOf(post)` to look up evaluations — this returned the first occurrence's index when duplicates existed, causing duplicate posts to appear in BOTH Selected and Rejected. Replaced with a `Set` of `post_id`s from `generated_comments`; rejected = `filtered_posts` whose id is not in that set. Defensive even after backend dedup.
- **`filter_posts_by_score` boundary**: was strict `>`, now `>=` so posts at exactly `min_score` are kept (matches the function name's intent).
- **History-click clobber**: clicking a previous run from the History dropdown now restores the input box (`inputText`) and the Subreddits/Keywords radio (`inputType`) to that run's original `inputs`. Previously the input stayed showing whatever the user had typed for the next run, making the displayed cards look like they belonged to the wrong query. (`frontend/app/page.tsx:handleHistorySelect`)

### Changed
- **SELECT threshold lowered**: `prompts/post_scoring.txt` SELECT criteria changed from "BOTH virality ≥ 7 AND fit ≥ 7" → "BOTH virality ≥ 6 AND fit ≥ 6". Now mirrors the PASS gate in `post_validation.txt` (the previous mismatch made scoring stricter than validation, which produced 0 / 1 suggestions per run with Opus 4.7's conservative fit calibration).
- **`<PRODUCT_CONTEXT>` injected into post scoring** as well: `score_posts` now accepts and substitutes `product_context`, so SELECT decisions consider product fit rather than only generic profile match. `post_scoring.txt` updated with the `ADDITIONAL CONTEXT:` block.
- **Results layout**: "Selected Posts with Comments" (left) and "Reddit and LinkedIn Suggestions" (right) now sit **side-by-side at 50% width each** in a CSS grid `.results-row`. "Rejected Posts" remains full-width below. Stacks on screens narrower than 900px. (`frontend/app/globals.css`)
- **`isinstance(result, Exception)` → `isinstance(result, BaseException)`** in `fetch_multiple_*` for correct type narrowing of `asyncio.gather(return_exceptions=True)` output.

### Reason
User-reported regressions from a real run with 2 subreddits + 3 keywords: posts vanishing (18 → 14), duplicates appearing in both selected/rejected sections, zero post-suggestions despite obviously relevant content. Investigated by 2 sub-agents in parallel; root causes traced to (a) missing dedup at the Apify merge step cascading through stale `indexOf` lookups in the frontend, and (b) an unintentionally strict SELECT threshold combined with no product context in the scoring prompt.

---

## 2026-04-26 - Subreddit name input + unified mode-controls layout

### Added
- **Subreddit input accepts any shape**: `n8n`, `/n8n`, `r/n8n`, `/r/n8n`, `SaaS`, `reddit.com/r/Foo`, `https://www.reddit.com/r/Foo/top/?t=day`, `old.reddit.com/r/Bar/hot/`, etc. Backend normalizes with `apify_client.normalize_subreddit_name` (strips protocol, host, leading slashes, `r/` prefix, trailing path) and constructs the canonical URL via `apify_client.build_subreddit_url(name, sub_type, sub_timeframe)`.
- **Subreddit-mode dropdowns** (frontend, same row as radio buttons):
  - **Sort** — Top posts (default) · Hot now · Newest · Best · Rising
  - **Time frame** — Past hour · Today (default) · This week · This month · This year · All time. Only shown when Sort = Top (Reddit only honours `?t=` for `/top`).
- **Backend `RunRequest`**: optional `sub_type`, `sub_timeframe`. Forwarded through `run_workflow` to `apify.fetch_multiple_subreddits(inputs, sub_type, sub_timeframe)`.

### Changed
- **Layout refactor**: radio buttons (Subreddits / Keywords) now share a row with mode-specific dropdowns — radios on the left, dropdowns on the right. New CSS classes `.input-header` (flex container, `space-between`) and `.mode-controls` (renamed from `.keyword-controls`). Saves the entire row that the keyword-controls block previously consumed.
- **Subreddits radio label**: "Subreddit URLs" → "Subreddits" (since users can now type names, not just URLs).
- **Subreddit textarea placeholder**: simplified to "Enter subreddit names … any of these formats works: n8n  •  /SaaS  •  r/AI_Agents  •  https://www.reddit.com/r/selfhosted/  •  reddit.com/r/help".
- **Textarea size**: now consistently `rows={3}` / `min-height: 60px` for both modes (was 8/100 for URL mode).

### Reason
URL entry was painful — users had to hand-construct `/top/?t=day` paths and remember which sort takes a timeframe. Backend now does that work; frontend exposes the same options as compact dropdowns colocated with the radios so they don't take a separate row.

---

## 2026-04-26 - Keyword-mode UI controls (timeframe / sort / posts per keyword)

### Added
- **Frontend (keywords mode only)**: three new dropdowns under the keyword textarea — Time frame (Last 24 hours, Past week [default], Past month, Past year, All time), Sort (Most relevant [default], Most upvoted), Posts per keyword (10, 20 [default], 30, 50). Smaller textarea (3 rows / 60px min-height) when in keywords mode; URL mode unchanged. New CSS class `.keyword-controls` in `globals.css`.
- **Backend `RunRequest`**: optional `timeframe: str | None`, `sort: str | None`, `max_posts: int | None`. Ignored in URL mode.
- **`workflow.run_workflow`**: accepts the three optional kwargs and forwards to `apify.fetch_multiple_keywords`.
- **`apify_client.fetch_keyword`**: now accepts `timeframe`, `sort`, `max_posts` with the prior hardcoded values as defaults (week / relevance / 20).
- **`apify_client.fetch_multiple_keywords`**: forwards overrides only when provided so `fetch_keyword`'s defaults remain authoritative.

### Reason
User wanted runtime control over Reddit search scope without code changes — particularly to expand the time window for niche keyword phrases that don't have many recent posts. Defaults preserve current behavior.

---

## 2026-04-26 - post_id mapping fix, UI run-blink fix, Apify exact-phrase + limit bumps

### Fixed
- **Post/LLM card mix-up (data-flow drift)**: The LLM was occasionally returning 1-based `post_index` values when prompts displayed posts as `Post 1:`, `Post 2:`. Mapping by index then surfaced wrong title/summary/reasoning combinations on some cards. Fix: every batched prompt now includes the post's stable `post_id` and the LLM is required to echo it back; `llm_client.py` maps results by `post_id` and re-attaches the correct `post_index`. Affects `evaluate_posts_for_comments`, `score_posts`, `validate_comments_batch`, `generate_post_strategies_batch`, `validate_posts_batch`. Hallucinated/missing post_ids are logged and dropped.
- **UI run-blink**: Clicking "Run Now" briefly displayed the previous run's results before snapping to the new run. Root cause was a stale closure: `setTimeout(() => pollStatus(), 1000)` captured the pre-`setTaskId` closure with the previous `taskId`. Fix: `pollStatus(tidOverride?: string)` now accepts an explicit tid; `handleRun` passes `data.task_id` directly into the immediate poll. (`frontend/app/page.tsx`)
- **Apify keyword search returning partial-phrase matches**: Searching `voice ai` matched posts containing only `voice` or `retelling`. Fix: each keyword is now wrapped in escaped double quotes (`"voice ai"`) before being sent to Apify, which Reddit treats as an exact-phrase query.

### Changed
- **Apify limits bumped**: subreddit `maxPosts 10 → 15`, keyword `maxPosts 10 → 20`. Mission Critical Rule #12 in root `CLAUDE.md` rewritten accordingly.
- **Apify keyword payload**: `sort: "top" → "relevance"` (more accurate for phrase queries), added `strictSearch: false`. Both verified against the actor's docs except `strictSearch` which is undocumented (added per user request; harmless if no-op).

### Added
- `backend/CLAUDE.md` Apify section + multi-input fan-out table (1/3/5 inputs × URL/keyword → posts fetched, wall-time).
- `backend/prompts/CLAUDE.md` cross-reference rule documenting post_id contract.
- `.claude/skills/project-gotchas/SKILL.md` gotchas: per-mode maxPosts, keyword quoting, post_id cross-ref.

### Note
- Both Apify URLs in `apify_client.py:13-14` point to the **same** actor: `fatihtahta/reddit-scraper-search-fast` (actor ID `TwqHBuZZPHJxiQrTU`). The two distinct URLs are just different invocation styles (sync vs async runs API).

---

## 2026-04-26 - Bedrock + batching + SQLite + post_* unification

### Changed
- **LLM provider**: OpenAI GPT-5-nano → **Claude Opus 4.7 via AWS Bedrock Converse API** (bearer auth via `BEDROCK_API_KEY`). `httpx` only — no `boto3`.
- **Performance**:
  - Step 5 (comment generation) now runs in parallel via `asyncio.gather` with `Semaphore(5)`.
  - Step 6 (comment validation) collapsed from N sequential calls into **1 batched call**.
  - Step 8 (post strategy) collapsed into **1 batched call**.
  - Step 9 (post validation) collapsed into **1 batched call**.
  - Total LLM calls per typical run dropped from ~25 to ~10.
- **Storage**: In-memory dict → **SQLite** at `backend/data/tasks.db`, with in-memory cache for cheap polling. Survives server restart.
- **Retention**: 24h → **7 days**, configurable via `config.json:retention_days`.
- **Naming**: All `linkedin_*` fields/types/methods renamed to `post_*` (Reddit + LinkedIn now treated as one repurposing channel).
  - Backend: `linkedin_scores/strategies/validations` → `post_*`
  - Backend: `score_posts_for_linkedin/generate_linkedin_strategy/validate_linkedin` → `score_posts/generate_post_strategies_batch/validate_posts_batch`
  - Frontend: `LinkedInScore/Strategy/Validation` → `PostScore/Strategy/Validation`; `linkedinFilter`/`getLinkedinTag` → `postFilter`/`getPostTag`
  - Logs: `linkedin_scoring_result/strategy_result/validation_result` → `post_*`
- **Section title**: "LinkedIn Suggestions" → **"Reddit and LinkedIn Suggestions"** (single section, single set of filters).

### Prompts
- Renamed `linkedin_scoring.txt` → `post_scoring.txt`, `linkedin_rewrite.txt` → `post_rewrite.txt`, `linkedin_validation.txt` → `post_validation.txt`.
- All three rewritten to treat Reddit-repurposing and LinkedIn-repurposing as one fit judgment; strategy paragraphs now call out best channel.
- `comment_validation.txt` rewritten to accept a batch and return a JSON array.
- `post_rewrite.txt` and `post_validation.txt` likewise batched.
- All batched prompts must preserve input order; `llm_client` maps results by index with graceful degradation.

### Added
- `.claude/skills/project-gotchas/SKILL.md` — failure-points checklist (4-8 word lines), invoked before code changes.
- `backend/data/` directory (gitignored) for SQLite DB.
- Bedrock concurrency cap (`Semaphore(5)`) shared across all calls in a workflow run.

### Removed
- `openai` from `requirements.txt` and all imports.
- Old per-item validation/strategy methods (`validate_comment`, `generate_linkedin_strategy`, `validate_linkedin`).
- `OPENAI_API_KEY` from `.env.example`.

### Why
- User wanted significantly faster runs (was 6-8 min, now ~1-2 min projected), Claude Opus quality for all calls, and persistent run history that survives EC2/PM2 restart. Channel unification (Reddit + LinkedIn) is minimal change since the same scoring/strategy applies.

### Audit fixes (post-ship sweep)
- **`<PRODUCT_CONTEXT>` re-wired post-rename**: Substitution restored in 3 prompts (`comment_evaluation.txt`, `comment_validation.txt`, `post_validation.txt`) and 3 `llm_client.py` methods (`evaluate_posts_for_comments`, `validate_comments_batch`, `validate_posts_batch`) now accept `product_context: str = ""` and `.replace("<PRODUCT_CONTEXT>", ...)`. `workflow.py` loads `product_context` from `config.json` and passes it through to all three calls.
- **Removed hardcoded "dograh" mentions**: The product-specific name that had survived in `comment_validation.txt` and `post_validation.txt` was replaced by generic references to the `<PRODUCT_CONTEXT>` block, keeping prompts portable across users.
- **`main.py` retention copy**: Audited for stale "24h" docstrings/log lines; none remained — `/history` already documents the configurable retention window and the lifespan log already prints `retention_days` from storage.

---

## 2026-04-24 - Public Repo Prep & Config-Driven Product Context

### Added
- **`<PRODUCT_CONTEXT>` placeholder**: New prompt placeholder parallel to `<USER_CONTEXT>`. Injected into 3 prompts (`comment_evaluation`, `comment_validation`, `linkedin_validation`) via an `ADDITIONAL CONTEXT:` block.
- **`product_context` config field**: New field in `config.json` that carries optional product-promotion bias. Decouples product-specific logic from prompt templates.
- **`backend/config.example.json`**: Public, generic template for `config.json`. Users copy this on first setup.
- **`LICENSE`**: MIT license added at project root.
- **`README.md`**: Configuration section references `config.example.json` and the new `product_context` field; added Responsible Use and License sections; removed stale "internal tool" framing.

### Changed
- **`.gitignore`**: Expanded with env variants, venv, IDE dirs, editor files, test/coverage, `.claude/settings.local.json`, and `backend/config.json` (personal context stays local).
- **3 prompt files** (`comment_evaluation.txt`, `comment_validation.txt`, `linkedin_validation.txt`): Removed hardcoded product-specific references from prompt bodies; replaced with generic `<PRODUCT_CONTEXT>` injection.
- **`llm_client.py`**: Added optional `product_context: str = ""` parameter to `evaluate_posts_for_comments`, `validate_comment`, `validate_linkedin`. Added `.replace("<PRODUCT_CONTEXT>", ...)` substitution in each.
- **`workflow.py`**: Loads `product_context` from config, passes it into the 3 affected LLM calls.

### Reason
Publishing the repo on public GitHub while keeping personal/product context local-only. `config.json` is now gitignored; any personalized content lives there. The public copy stays generic but structurally identical — behavior unchanged for the primary user.

---

## 2026-02-15 - Password Protection & Deployment Prep

### Added
- **Backend auth**: `verify_password` dependency checks `X-Access-Password` header on protected routes (`/run`, `/status`, `/results`, `/history`)
- **`/auth/verify` endpoint**: Unprotected POST endpoint for frontend login flow
- **Frontend password screen**: Centered login card shown before app access
- **`authFetch()` wrapper**: All API calls include password header, auto-logout on 401
- **sessionStorage auth**: Password persists across page reloads, clears on tab close
- **Logout button**: Added to header bar
- **`.gitignore`**: Created at project root to prevent `.env`, `node_modules`, `__pycache__`, `.next`, `logs/` from being committed
- **`ACCESS_PASSWORD`**: Added to `backend/.env` and `backend/.env.example`
- **Dynamic API_BASE**: Frontend uses `NEXT_PUBLIC_API_BASE` env var with localhost fallback

### Security
- Uses `secrets.compare_digest` for timing-safe password comparison
- `/health` and `/auth/verify` remain unprotected

---

## 2025-11-23 - LinkedIn Selection Criteria Update

### Changed
- LinkedIn scoring now includes `decision: "SELECT" | "IGNORE"` field
- Selection criteria: BOTH virality >= 7 AND fit >= 7 (was: either >= 5)
- Only SELECT posts proceed to LinkedIn strategy generation
- Updated logging metrics to track posts_selected vs posts_ignored

---

## 2025-11-23 - Display LLM Reasoning on Results Page

### Added
- "Why selected" reasoning shown for each post in Comments section (from comment_evaluation)
- "Why it scores well" reasoning shown for each post in LinkedIn section (from linkedin_scoring)
- New `.reasoning-box` CSS style with purple left border accent

---

## 2025-11-23 - Detailed Workflow Metrics Logging

### Added
- Workflow-level event logging with `log_workflow_event()` function
- Per-step metrics logged to `logs/api_calls.log`:
  - `comment_evaluation_result`: posts_evaluated, posts_selected, posts_rejected, selection_rate, llm_calls
  - `comment_generation_result`: posts_with_comments, comments_generated, llm_calls
  - `comment_validation_result`: comments_validated, pass_count, llm_calls
  - `linkedin_scoring_result`: posts_scored, posts_qualifying, llm_calls
  - `linkedin_strategy_result`: strategies_generated, llm_calls
  - `linkedin_validation_result`: strategies_validated, pass/unsure/fail counts, llm_calls
  - `workflow_summary`: Complete run totals including total_llm_calls

---

## 2025-11-23 - Progressive Results Display

### Changed
- Results now populate as data is generated, not waiting for workflow completion
- Poll interval reduced from 15s to 5s for faster updates
- First poll triggers 1 second after run starts
- Frontend fetches results on every poll instead of only at completion

---

## 2025-11-23 - Post Summary Generation

### Added
- LLM now generates a 1-line summary (max 100 chars) for each post during evaluation
- Summary field added to `comment_evaluation.txt` prompt output
- Frontend displays LLM-generated summaries instead of truncated body text
- Summary shown in all 3 sections: Comments, LinkedIn, and Rejected Posts

---

## 2025-11-23 - API Logging & LinkedIn Validation Fix

### Added
- `api_logger.py` - New module for logging all API calls to `logs/api_calls.log`
- Token consumption tracking for every LLM call (input/output/total tokens)
- Apify call logging with post counts and result summaries

### Fixed
- LinkedIn validation logic: Now correctly marks as UNSURE when one threshold passes but other fails
  - PASS: Both virality >= 6 AND fit >= 6
  - UNSURE: Mixed results (one >= 6, other < 6) OR mid-range scores (4-5.9)
  - FAIL: Either score < 4

---

## 2025-11-23 - Model Update

### Changed
- LLM model: gpt-4o-mini → gpt-5-nano
- Removed temperature and max_tokens parameters (not supported by gpt-5-nano)
- Using model defaults for reasoning effort and verbosity

---

## 2025-11-23 - Port Configuration Update

### Changed
- Backend port: 8000 → 8007 (to avoid common port conflicts)
- Frontend port: 3000 → 3007 (to avoid common port conflicts)
- Updated all documentation and CLAUDE.md files

---

## 2025-11-23 - Initial Implementation

### Backend
- Created FastAPI backend with 4 endpoints: `/run`, `/status/{task_id}`, `/results/{task_id}`, `/history`
- Implemented 11-step workflow in `workflow.py`
- Added in-memory storage with 24hr auto-cleanup
- Integrated Apify client for Reddit scraping (URLs + keywords)
- Integrated OpenAI GPT-4o-mini for all LLM operations
- Created 6 prompt template files for comment/LinkedIn workflows

### Frontend
- Created Next.js 15 single-page app
- Implemented input section with URL/keyword toggle
- Added 15-second polling for task status
- Built results dashboard with 3 sections:
  - Selected Posts with Comments
  - LinkedIn Suggestions
  - Rejected Posts
- Added PASS/FAIL/UNSURE filtering for both comment and LinkedIn sections
- Implemented run history dropdown

### Documentation
- Created CLAUDE.md files for root, backend, frontend, and prompts folders
- Added requirements.txt and .env.example
- Created config.json template with user profile
