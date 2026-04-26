---
name: project-gotchas
description: Recurring failure points in this Reddit/LinkedIn discovery repo. Read before writing or reviewing code in backend/* or frontend/* — these are mistakes the codebase has actually been bitten by.
---

# Project gotchas

- All LLM calls go through Bedrock Opus 4.7 (no OpenAI)
- Bedrock auth is bearer key, not SigV4 / boto3
- Apify maxPosts: 15 subreddit, 20 keyword
- Apify keyword must wrap in quotes for exact phrase
- Cross-reference posts by post_id, not post_index
- Dedupe Apify results by post.id at merge
- Frontend rejected = filtered minus generated_comments ids
- SELECT threshold is 6+6, mirrors PASS gate
- product_context goes to 4 prompts incl. post_scoring
- llm_client.call_log captures every prompt/response for debugger
- Step 5 parallel calls share one group_id for accordion grouping
- Memory Bank tables are permanent — no retention cleanup
- memory_posts is idempotent on post_id; re-saves are no-ops
- /memory route reads sessionStorage password set on /
- Apify dedup canonical key is (title, author) — handles crossposts
- Each canonical post carries subreddit_sources list of all sources
- memory_posts PK is composite (post_id, subreddit) — cross-post safe
- Cross-posted PASS/UNSURE counts in EVERY source subreddit
- Strategy prompt outputs bullet phrases, not paragraphs
- Subscriber count formatted as 21k via fmtK helper
- Bedrock payload MUST set inferenceConfig.maxTokens (default 4K truncates batches)
- Dedup canonical key requires title length >= 20 to use (title, author)
- Dedup merge keeps MAX score / num_comments across copies
- Step 4 / 7 silent drops surface to task.error_log
- generate_comments has regex salvage when JSON parse fails
- LLM may wrap JSON output in an extra array
- _parse_json_response falls back to raw string — handle it
- Sequential await loops kill latency — gather with semaphore
- Validation/strategy prompts are batched, one call returns array
- SQLite is single-writer — concurrent runs may briefly contend
- Retention lives in config.json:retention_days, default 7
- Section title is "Reddit and LinkedIn Suggestions" (not "LinkedIn")
- Internal field name is post_* (renamed from linkedin_*)
- Graceful degradation: continue on per-item failure, log it
- PRODUCT_CONTEXT lives in 3 prompts, 3 methods
- Prompts must stay generic — no hardcoded product names
