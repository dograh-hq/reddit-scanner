<system_context>
Prompt templates for LLM calls in the Reddit comments + Reddit/LinkedIn post repurposing workflow.
Each file contains a prompt template with placeholders for dynamic content. 4 of 6 prompts are batched (one LLM call returns an array).
</system_context>

<file_map>
## FILE MAP
- `comment_evaluation.txt` - BATCHED YES/NO decisions for commenting (per-post)
- `comment_generation.txt` - Per-post: generate 2 comments with sample references
- `comment_validation.txt` - BATCHED: score + tag both comments per post (0-100)
- `post_scoring.txt` - BATCHED: virality + fit scores (1-10) + SELECT/IGNORE for Reddit AND LinkedIn repurposing
- `post_rewrite.txt` - BATCHED: 3-4 sentence strategy per post (NOT the actual post). Calls out best channel (Reddit / LinkedIn / both)
- `post_validation.txt` - BATCHED: independent PASS/FAIL/UNSURE per post
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

### Placeholder Pattern
All prompts use `<PLACEHOLDER>` style markers:
- `<USER_CONTEXT>` - User profile from config.json
- `<PRODUCT_CONTEXT>` - Optional product-promotion bias from config.json (used in 3 prompts: comment_evaluation, comment_validation, post_validation; empty string = inert)
- `<LIST_OF_POSTS>` - Batch of posts (post_scoring, comment_evaluation)
- `<ITEMS>` - Generic batch payload for batched validation/strategy prompts
- `<TITLE>`, `<BODY>`, `<SUBREDDIT>` - Single post fields (comment_generation only)
- `<SCORE>`, `<NUM_COMMENTS>` - Engagement metrics (comment_generation only)

### Output Formats
- All batched prompts: JSON array, one entry per item; **each entry MUST echo the input `post_id`** — `llm_client.py` maps results back by `post_id`, not by array position
- comment_generation: JSON object `{"comments": ["...", "..."]}` (per-post call, no batching)
- All validation/scoring prompts: JSON with `tag` + `reasoning` fields

### Cross-reference rule
- Per-item display blocks always include `post_id=<apify post id>` so the LLM can echo it back unambiguously.
- `comment_evaluation` and `post_scoring` historically returned `post_index` — that field is now derived from `post_id` lookup in `llm_client.py` (LLM was sometimes returning 1-based indices that confused the frontend display). LLM only sees `post_id` now.
</paved_path>

<critical_notes>
## CRITICAL NOTES
- **Batched prompts must preserve input order** - llm_client maps results back by index
- **Keep samples** - comment_generation.txt includes 3 sample comments
- **JSON output** - All prompts expect JSON; ```json fences are stripped by parser
- **User context injection** - All prompts include user expertise
- **post_rewrite.txt must NOT write the actual post** - strategy paragraph only
- **Channels are unified** - post_* prompts treat Reddit-repurposing and LinkedIn-repurposing as one judgment; strategies should call out the best channel
</critical_notes>
