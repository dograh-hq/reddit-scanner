# summary.md — Research & Strategy Discussion

_No code changes yet. This is a decision-prep doc. Pick the strategies you want, then we implement._

> **Note (2026-04-26):** Sections 1 and 2 below describe the **pre-fix** state. The performance work (parallel step 5 + batched steps 6/8/9) and the channel unification have since shipped — actual call counts and timings differ from the analysis below. Section 3 is post-ship and current. Section 4 (SQLite Strategy I) also shipped as designed.

---
## 1. Why every run feels slow

### Timing from the run you shared (`07a04e8f…`)

| Step | What | Start | End | Duration |
|---|---|---|---|---|
| 4 | Comment eval (1 batch LLM call over 10 posts) | 10:27:~ | 10:27:29 | ~15–30 s |
| 5 | Comment generation (5 sequential calls, one per YES post) | 10:27:29 | 10:29:04 | **~1 m 35 s** |
| 6 | Comment validation (10 sequential calls, one per comment) | 10:29:04 | 10:31:53 | **~2 m 49 s** |
| 7 | LinkedIn scoring (1 batch call over 10 posts) | 10:31:53 | 10:32:41 | ~48 s |
| 8 | LinkedIn strategies (4 sequential calls) | 10:32:41 | ~10:33:30 | ~50 s–1 m (est.) |
| 9 | LinkedIn validation (4 sequential calls) | ~10:33:30 | ~10:34:30 | ~1 m (est.) |
| — | Apify fetch (parallel across URLs) | before step 4 | | ~10–30 s |

**End-to-end today: ~6–8 minutes for 3 subreddits × 10 posts.**

### Root causes (ranked by impact)

1. **Sequential LLM calls inside Python `for` loops.** Steps 5, 6, 8, 9 iterate one post/comment at a time with `await` inside the loop — they never run in parallel even though the client is async. For 10 filtered / 5 YES / 4 SELECT, that is **23 sequential calls** out of 25 total.
2. **gpt-5-nano generates a lot of reasoning tokens.** Looking at your log: each call outputs **2,000–5,000 output tokens** (reasoning + final answer). At nano's throughput that is 15–40 s per call. You removed `temperature`/`max_tokens` when you swapped to gpt-5-nano because the model rejected them, so output is unbounded and `reasoning_effort` defaults to medium.
3. **Validation is per-comment, not per-post.** You validate comment 1, then comment 2, serially — doubling step 6 latency.
4. **LLM batch calls still do a lot of work in one prompt.** Steps 4 and 7 are "one call" but each returns a long JSON array (Step 7 = 4,732 output tokens / 48 s). When one of the batches is on the critical path, it's still expensive.
5. **Apify keyword scraper polls for up to 60 s.** Irrelevant for URL runs, but on keyword runs it's an extra tax.

### Strategies to speed this up — pick any combo

**Strategy A — Parallelize the per-item loops (biggest win, smallest change).**
Wrap steps 5, 6, 8, 9 in `asyncio.gather()`. Sequential → "as slow as the slowest item." Rough projection:
- Step 5: 1 m 35 s → ~25–30 s
- Step 6: 2 m 49 s → ~30–40 s
- Step 8 + 9: ~2 m → ~30 s each

**Expected total: ~2.5–3 min instead of 6–8 min.** Pure Python change, no prompt changes, no model change. Add a semaphore (e.g. 10 concurrent) to avoid hammering OpenAI rate limits.

**Strategy B — Batch the validations (and strategies) in one LLM call each.**
Collapse:
- Step 6 (10 calls) → 1 batched validation call returning an array.
- Step 8 (4 calls) → 1 batched strategy call.
- Step 9 (4 calls) → 1 batched validation call.

**Total LLM calls drops from ~25 → ~6.** Trade-off: one long output, one big JSON to parse, higher risk of a single bad JSON blowing up multiple items. Good mitigation: combine with Strategy A so each "batch" still has a graceful-degradation path.

**Strategy C — Cut reasoning token budget.**
gpt-5-nano supports `reasoning_effort` ("minimal" | "low" | "medium" | "high"). Setting `"minimal"` or `"low"` on the mechanical steps (validation, scoring) typically cuts latency 3–5×. Keep `"medium"` only for generation (step 5) where reasoning actually helps. Can also cap `max_completion_tokens` to stop runaway outputs.

**Strategy D — Model mix.**
Keep gpt-5-nano for generation (step 5). Switch validation/scoring/strategy to `gpt-4o-mini` (no reasoning tokens, ~2–3 s/call, much cheaper per call). That alone cuts steps 6, 7, 8, 9 dramatically without any parallelism work.

**My recommendation:** A + B + C together. That's ~1 min end-to-end and keeps the model family consistent. D is a fallback if A+B+C still isn't fast enough.

---

## 2. Full map of every LLM call and which prompt it uses

### Per run, in workflow order

| # | Step | Prompt file | # LLM calls | Fan-out shape | Called from |
|---|---|---|---|---|---|
| 4 | Comment evaluation (batch YES/NO) | `prompts/comment_evaluation.txt` | **1** | One call, all filtered posts in `<LIST_OF_POSTS>` | `llm_client.evaluate_posts_for_comments` |
| 5 | Comment generation | `prompts/comment_generation.txt` | **N_yes** (one per YES post) | Sequential, one post at a time | `llm_client.generate_comments` |
| 6 | Comment validation | `prompts/comment_validation.txt` | **2 × N_yes** (one per comment) | Sequential, one comment at a time | `llm_client.validate_comment` |
| 7 | LinkedIn scoring (batch virality + fit) | `prompts/linkedin_scoring.txt` | **1** | One call, all filtered posts | `llm_client.score_posts_for_linkedin` |
| 8 | LinkedIn strategy | `prompts/linkedin_rewrite.txt` | **N_select** (one per SELECT post) | Sequential | `llm_client.generate_linkedin_strategy` |
| 9 | LinkedIn validation | `prompts/linkedin_validation.txt` | **N_select** | Sequential | `llm_client.validate_linkedin` |

**Total per run:** `2 + N_yes + 2·N_yes + N_select + N_select = 2 + 3·N_yes + 2·N_select`.
For your typical run (10 filtered / 5 YES / 4 SELECT) = **25 LLM calls** today.

### Placeholders injected into each prompt

| Prompt | Placeholders |
|---|---|
| `comment_evaluation.txt` | `<USER_CONTEXT>`, `<LIST_OF_POSTS>` (+ `<PRODUCT_CONTEXT>` per new plan) |
| `comment_generation.txt` | `<USER_CONTEXT>`, `<TITLE>`, `<BODY>`, `<SUBREDDIT>`, `<SCORE>`, `<NUM_COMMENTS>` |
| `comment_validation.txt` | `<USER_CONTEXT>`, `<POST_TITLE>`, `<POST_BODY>`, `<COMMENT>`, `<UPVOTES>` (+ `<PRODUCT_CONTEXT>`) |
| `linkedin_scoring.txt` | `<USER_CONTEXT>`, `<LIST_OF_POSTS>` |
| `linkedin_rewrite.txt` | `<USER_CONTEXT>`, `<TITLE>`, `<BODY>`, `<VIRALITY_SCORE>`, `<FIT_SCORE>` |
| `linkedin_validation.txt` | `<USER_CONTEXT>`, `<POST_TITLE>`, `<VIRALITY_SCORE>`, `<FIT_SCORE>`, `<STRATEGY>` (+ `<PRODUCT_CONTEXT>`) |

### Per-call token observations from your log

| Call type | Avg input tokens | Avg output tokens |
|---|---|---|
| comment_evaluation (batch) | ~1,600 | ~4,900 |
| comment_generation | ~1,000 | ~2,000–4,000 |
| comment_validation | ~650 | ~2,000–3,800 |
| linkedin_scoring (batch) | ~1,400 | ~4,700 |

Output tokens ≫ input tokens — this is the signature of reasoning overhead, not prompt bloat.

---

## 3. Reddit + LinkedIn rewrite strategies — DECIDED (minimal unification)

**Status: shipped 2026-04-26.**

You picked the "minimal" path: treat Reddit and LinkedIn repurposing as a **single judgment**, not two parallel tracks. Same scoring, same strategy, same validation. The strategy paragraph just calls out which channel(s) it suits best.

### What was actually changed
- Prompts `linkedin_scoring.txt` / `linkedin_rewrite.txt` / `linkedin_validation.txt` renamed to `post_scoring.txt` / `post_rewrite.txt` / `post_validation.txt`. Copy broadened so "fit" means fit for either Reddit or LinkedIn, and the strategy paragraph names the best channel.
- All three new prompts are now **batched** (one LLM call returns an array, in input order).
- Backend fields/types renamed `linkedin_*` → `post_*` everywhere (storage, results endpoint, log events, frontend types/state).
- Frontend section heading: **"Reddit and LinkedIn Suggestions"**. Cards, tabs, and filters unchanged.
- Internal data shape: still one `virality_score` + one `fit_score` + one `decision` + one `strategy` + one `validation` per post — exactly like before, just relabeled.

### Why the discarded options were dropped
- Two parallel strategy prompts per post (formerly "Strategy 1") doubled the call count for marginal benefit when the user only needs a single recommendation.
- One combined prompt outputting both channels (formerly "Strategy 2") — the unified post-style strategy already does this implicitly.
- Full content-discovery redesign (formerly "Strategy 3") — out of scope; needed a UI overhaul.

---

## 4. History persistence — where it lives today, and how to fix it

### Current state
- `backend/storage.py` defines `InMemoryStorage`, a singleton that holds `self._tasks: dict[str, TaskData]` entirely in the Python process's heap.
- Nothing is ever written to disk. `api_calls.log` is a separate log file and does not reconstruct task state.
- `cleanup_old_tasks()` deletes entries older than 24 h, run every 30 min by `start_cleanup_loop`.
- **On `uvicorn --reload`, any crash, or a redeploy: the entire `_tasks` dict is wiped.** That's what you're seeing.

### Requirements you stated
- Retention: 24 h → **7 days**.
- Must survive server restart (persistent).

### Three strategies

**Strategy I — SQLite (recommended for this project).**
- One file: `backend/data/tasks.db`.
- Schema: `tasks(task_id TEXT PK, created_at TEXT, input_type TEXT, inputs JSON, status TEXT, data JSON)` — store the whole `TaskData` as a JSON blob in one column, plus indexed columns for listing/filtering.
- `storage.py` becomes a thin wrapper that reads/writes rows on `get_task`, `create_task`, `update_task`, `get_history`; keeps a small in-memory LRU cache for the active task to avoid hammering SQLite during polling.
- Cleanup cron: `DELETE FROM tasks WHERE created_at < now() - 7 days`.
- **Pros:** zero infra, single file to back up, works on Railway/Render volumes, ACID, concurrent readers. Mature Python stdlib (`sqlite3` or `aiosqlite` for async).
- **Cons:** single writer — fine for your concurrency (1 user, polling at 5 s).

**Strategy II — JSON file per task in `backend/data/tasks/`.**
- `tasks/<task_id>.json` containing the full dump of `TaskData`.
- `history` is built by scanning the directory and reading file mtimes or a small `index.json` that's updated on create/finish.
- Cleanup: delete files older than 7 days.
- **Pros:** simplest possible approach, human-readable, trivially greppable, no dependency.
- **Cons:** scan cost grows with task count (negligible at your scale for a week). Atomic writes need care (write-then-rename) so progressive polling doesn't read half-written JSON.

**Strategy III — Pickle / single snapshot file.**
- Dump `self._tasks` to `tasks.pickle` every N seconds or on every `update_task`. Load on startup.
- **Pros:** almost no code change. Just add save/load hooks.
- **Cons:** binary format tied to Python class layout — any schema change breaks old snapshots. Not great as a long-lived store. I'd only use this as a 30-minute hack, not the real answer.

**Deployment note.** Today you plan to host backend on Railway/Render. Both provide persistent volumes but only if you explicitly mount one. Whichever strategy you pick, decide upfront whether state lives in the repo's working dir (simplest, but ephemeral on Railway's default filesystem) or on a mounted volume (durable across deploys). Strategy I + a Railway volume is the clean production path.

**My recommendation:** **Strategy I (SQLite).** It's the smallest code change that actually solves the "lost on restart" problem, fits single-user in-memory-cached polling, and is boring/reliable. Strategy II is acceptable if you want zero dependencies; Strategy III is not worth shipping.

### Retention knob
Whichever storage we pick, make `RETENTION_DAYS = 7` a config value (env var or `config.json`) so you can turn it up to 30 or down to 1 without a code change.

---

## 5. Suggested order of execution (once you pick strategies)

1. **Ship the fix for the current crash** (the `{comments}` rendering bug we identified earlier) — unblocks you today.
2. **Performance: Strategy A (parallelize) first**, measure, then add B (batch validations) if needed.
3. **Persistence: Strategy I (SQLite) + 7-day retention** — isolated change, low risk.
4. **Reddit+LinkedIn discovery expansion: Strategy 1** — bigger refactor; do this last once steps 1–3 are stable so we're not debugging three things at once.

---

## Open questions for you before we write code

1. For the performance fixes: are you OK with a concurrency cap of ~10 parallel OpenAI calls, or do you want to stay more conservative (5)?
2. For the Reddit/LinkedIn redesign: Strategy 1 (two parallel strategies per post) or Strategy 2 (one combined prompt)?
3. For persistence: SQLite or JSON files? And will you mount a Railway volume in prod, or is "persistent-for-the-dev-box only" fine for now?
4. Should failed / error runs also be kept for 7 days, or pruned aggressively (e.g. 24 h)?
5. Do you want per-channel filter tabs in the UI (Reddit-pass / LinkedIn-pass / either) or one unified filter?

Tell me your picks and we'll turn this into a concrete implementation plan.
