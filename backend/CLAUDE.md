<system_context>
FastAPI backend for Reddit comment generation and Reddit/LinkedIn post repurposing.
Fetches Reddit posts via Apify API, evaluates them with Claude Opus 4.7 (Bedrock), generates comments (parallel), and scores/strategizes/validates posts in single-batch LLM calls.
</system_context>

<file_map>
## FILE MAP
- `main.py` - FastAPI app with 5 endpoints: /run, /status, /results, /history, /auth/verify
- `workflow.py` - 11-step linear workflow orchestrator (parallel step 5; batched 6/8/9)
- `storage.py` - SQLite-backed storage with in-memory cache, 7-day retention (configurable)
- `apify_client.py` - Reddit scraping via Apify (URLs + keywords)
- `llm_client.py` - Bedrock Converse client for Claude Opus 4.7 (bearer auth via httpx)
- `api_logger.py` - API call logging with token consumption and workflow metrics tracking
- `config.example.json` - Public template for user/product context and defaults (committed)
- `config.json` - User's real config; gitignored, copied from `config.example.json` on first setup
- `requirements.txt` - Python dependencies (no openai SDK)
- `/prompts/` - 6 prompt template files (4 are batched: comment_validation, post_scoring, post_rewrite, post_validation)
- `/data/tasks.db` - SQLite store, gitignored
- `/logs/api_calls.log` - Auto-generated log of all API calls
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

### API Endpoints
- `POST /auth/verify` - Verify password (unprotected)
- `GET /health` - Health check (unprotected)
- `POST /run` - Start workflow, returns task_id (protected)
- `GET /status/{task_id}` - Poll for progress (protected)
- `GET /results/{task_id}` - Get full results incl. `llm_calls` (protected)
- `GET /history` - List runs from last RETENTION_DAYS (protected)
- `GET /memory/subreddits` - Memory Bank: paginated subreddit list (protected)
- `GET /memory/subreddits/{name}/posts` - Memory Bank: paginated posts in a subreddit, with sort/filter/title-search (protected)

### Auth
- Protected routes require `X-Access-Password` header matching `ACCESS_PASSWORD` env var
- Uses `secrets.compare_digest` for timing-safe comparison
- `/auth/verify` accepts JSON body `{password}` for frontend login flow

### LLM (Bedrock)
- Endpoint: `https://bedrock-runtime.us-east-1.amazonaws.com/model/us.anthropic.claude-opus-4-7/converse`
- Auth: `Authorization: Bearer ${BEDROCK_API_KEY}` (NOT SigV4 / boto3)
- Concurrency cap: `asyncio.Semaphore(5)` shared per workflow run

### Workflow Steps (workflow.py)
1. Parse inputs (URLs or keywords)
2. Fetch from Reddit via Apify (10 posts per source, parallel across sources)
3. Filter posts (score > min_score)
4. Batch evaluate for comments (YES/NO) - 1 LLM call
5. Generate 2 comments per YES post - N parallel LLM calls (Semaphore=5)
6. Batch validate all comments - 1 LLM call
7. Batch score posts for Reddit/LinkedIn repurposing (virality + fit, SELECT/IGNORE) - 1 LLM call
8. Batch generate rewrite strategies (SELECT posts only) - 1 LLM call
9. Batch validate post strategies - 1 LLM call
10. Store results
11. Mark complete

For 10/5/4 typical run: 1 + 5 + 1 + 1 + 1 + 1 = **10 LLM calls** (was 25 before batching).

### Storage Pattern
- TaskData dataclass holds all per-run data (incl. `llm_calls` powering the Prompt Debugger)
- `SqliteStorage` singleton: in-memory dict cache, SQLite is source of truth
- Persist on `_log_step` checkpoints (every workflow step boundary). `_log_step` also snapshots `llm.call_log` into `task.llm_calls` so the debugger sees prompts populate progressively.
- On startup, load all non-expired tasks into cache
- Background cleanup every 30 min, retention from `config.json:retention_days` (default 7)
- **Memory Bank tables are PERMANENT** — `memory_posts` (PK `post_id`, idempotent inserts) and `memory_subreddits` (denormalized rollup). Cleanup loop never touches them. Populated by `workflow._collect_memory_bank` after step 9.

### Config Placeholders
Prompts consume two config-injected placeholders:
- `<USER_CONTEXT>` - identity/expertise (from `config.json: user_context`)
- `<PRODUCT_CONTEXT>` - optional product-promotion bias (from `config.json: product_context`)

Used by `comment_evaluation`, `comment_validation`, `post_validation` under an `ADDITIONAL CONTEXT:` section. Empty `product_context` makes the block inert.

### Apify (Reddit fetching)
- **One actor for both modes**: `fatihtahta/reddit-scraper-search-fast` (actor ID `TwqHBuZZPHJxiQrTU`). Both URLs in `apify_client.py:13-14` resolve to this actor.
- **Subreddit URL mode** (`fetch_subreddit`): `maxPosts=15`, sync endpoint, posts return in the same HTTP response (~5–15s). Frontend accepts subreddit names in any shape (`n8n`, `r/n8n`, `/r/n8n`, full URL, etc.); `apify_client.normalize_subreddit_name` strips prefixes and `apify_client.build_subreddit_url(name, sub_type, sub_timeframe)` constructs the canonical Reddit URL. Defaults: `sub_type="top"`, `sub_timeframe="day"`. Other sort types (`hot`, `new`, `best`, `rising`) ignore timeframe (Reddit only honours `?t=` for `/top`).
- **Keyword mode** (`fetch_keyword`): defaults `maxPosts=20`, `sort=relevance`, `timeframe=week`, `strictSearch=false`. Each keyword is **wrapped in escaped double quotes** before being sent to Apify so Reddit treats it as an exact-phrase search (otherwise Reddit OR's the words and matches partials like `voice` or `retelling` for `voice ai`). Async endpoint: kicks a run, polls dataset for up to 60s. Frontend exposes per-run overrides for timeframe, sort, and posts-per-keyword via `RunRequest.timeframe / .sort / .max_posts`; URL mode ignores them.
- **Cross-reference contract**: every batched LLM prompt receives the post's stable `post_id` (Apify-given) and must echo it back. Mapping is by `post_id`, never by array position. See `prompts/CLAUDE.md` for details.
- **Cross-post / multi-keyword dedup** (`apify_client._dedupe_and_merge`): canonical key is `(title.lower(), author.lower())` — collapses both exact-id duplicates AND Reddit crossposts into one canonical entry with a `subreddit_sources: [{subreddit, subreddit_subscribers, permalink}]` list. Downstream (LLM pipeline, frontend cards, Memory Bank) iterates `subreddit_sources` to credit every subreddit a canonical post appeared in.

### Multi-input fan-out
Each subreddit URL or keyword fires its own Apify call in parallel via `asyncio.gather`. `maxPosts` is **per-call**, not shared:

| Inputs | Mode | Per-call posts | Max total fetched | ~Wall time |
|---|---|---|---|---|
| 1 | URL | 15 | 15 | ~50s end-to-end |
| 3 | URL | 15 | 45 | ~60s |
| 5 | URL | 15 | 75 | ~70s |
| 1 | Keyword | 20 | 20 | ~110s |
| 5 | Keyword | 20 | 100 | ~125s |

Step 5 (comment generation) is parallel up to `Semaphore(5)`. Steps 4, 6, 7, 8, 9 are single batched LLM calls each whose latency grows ~linearly with prompt length.

### Workflow Metrics Logging
Each workflow run logs detailed metrics to `logs/api_calls.log`:
- `comment_evaluation_result` - Posts evaluated vs selected, selection rate
- `comment_generation_result` - Comments generated, LLM calls made
- `comment_validation_result` - Pass/fail counts per comment (1 batch LLM call)
- `post_scoring_result` - Posts scored, selected vs ignored counts (Reddit+LinkedIn)
- `post_strategy_result` - Strategies generated (1 batch LLM call)
- `post_validation_result` - Pass/unsure/fail breakdown (1 batch LLM call)
- `workflow_summary` - Final totals including total_llm_calls
</paved_path>

<critical_notes>
## CRITICAL NOTES
- **Bedrock only** - All LLM calls go through Claude Opus 4.7 via Bedrock; no OpenAI dependency
- **Apify maxPosts** - subreddit URL: 15; keyword: 20. `scrapeComments=false`. See "Apify" section above.
- **post_id is the cross-reference** - never trust LLM-returned `post_index`; always map results back by `post_id` echoed by the prompt
- **Password auth required** - Set ACCESS_PASSWORD in .env, sent via X-Access-Password header
- **Graceful degradation** - Continue on per-item failures, log errors; batched fallbacks insert ERROR entries
- **JSON parse fallback** - If LLM returns invalid JSON, batched callers fill ERROR entries; per-post callers push raw text forward
- **Parallel fetching** - Multiple subreddits/keywords fetched in parallel
- **SQLite single writer** - Concurrent runs may briefly contend; rare loss is acceptable per spec
- **Failure-points skill** - Invoke `/project-gotchas` before any change in this folder
</critical_notes>
