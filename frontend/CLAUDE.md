<system_context>
Next.js 15 frontend for Reddit comments + Reddit/LinkedIn post repurposing discovery tool.
Single page app with input form, polling, and results display.
</system_context>

<file_map>
## FILE MAP
- `/app/page.tsx` - Main page with all UI logic + bottom `<PromptDebugger>` panel
- `/app/memory/page.tsx` - Subreddit Memory Bank dashboard (paginated subreddits + posts accordion)
- `/app/promo/page.tsx` - Promotional / Launch Bank dashboard (paginated promo posts, sort + tag/promo_type filters)
- `/app/layout.tsx` - Root layout
- `/app/globals.css` - All CSS styles
- `package.json` - Dependencies (Next.js 15, React 19)
- `tsconfig.json` - TypeScript config
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

### Auth Flow
1. On mount, checks sessionStorage for stored password
2. If found, verifies against `/auth/verify` endpoint
3. If not found or invalid, shows password login screen
4. `authFetch()` wraps all API calls with `X-Access-Password` header
5. Auto-logout on 401 response

### Page Structure
1. **Password screen** - Shown when not authenticated
2. **History dropdown** - Load previous runs
3. **Input section** - Radio (URLs/Keywords) + textarea + Run button
4. **Status bar** - Shows polling progress
5. **Results sections**:
   - Selected Posts with Comments (filterable)
   - Reddit and LinkedIn Suggestions (filterable)
   - Rejected Posts

### Polling Pattern (Progressive Updates)
- Start poll 1 second after POST /run returns task_id
- Poll GET /status/{task_id} every 5 seconds
- Fetch results on EVERY poll (not just at completion)
- Stop polling when status is "complete" or "failed"
- UI shows partial results as they become available

### Filtering
- Independent filters for comments and post-repurposing suggestions
- Options: ALL, PASS, UNSURE, FAIL
- Backend field names use `post_*` prefix (was `linkedin_*` before unification)

### Low-score sub-section (within Sections 1 + 2)
- Backend no longer drops posts by upvote count — every canonical post reaches the LLM.
- `partitionByScore()` splits items into `{ high, low }` by `filtered_posts[i].score >= LOW_SCORE_THRESHOLD` (5).
- High-score cards render at top exactly as before; below them an italic banner introduces the low-score group.
- Low-score cards keep header (title/sources/meta/tag/summary/why-reasoning) always visible; secondary content (comments list / strategy-box) collapses behind a `<CollapsibleBody>` toggle. Render logic extracted into `renderSelectedCard(gc, lowScore)` and `renderSuggestionCard(ls, lowScore)` closures.

### Promotional / Launch chip + dashboard
- Backend Step 2.5 returns `promotional_detections: [{post_id, is_promotional, promo_type, reasoning}]` on `/results`.
- `<PromoChip>` (purple pill, tooltip = LLM reasoning) renders next to PASS/UNSURE/FAIL on every Selected, Suggestions, and Rejected card via the new `.tag-group` wrapper. `getPromoDetection(post.id)` returns the verdict (or null when not promotional).
- Header bar has a `🚀 Promotional / Launch Bank` button next to `📚 Subreddit Memory Bank`, both routing to their dashboards.
- `/promo` route hits `GET /promotional` with sort (upvotes/comments/date/detected) + filter (validation_tag + promo_type) + title search. Auth flow reuses sessionStorage password from main page.

### Unbiased ("keyword finds") counts on both banks
- Backend tags each bank row with `source_input_type` ("urls" or "keywords") at insert time. The `unbiased` counter = rows with `source_input_type='keywords'` (Reddit's keyword search has no subreddit pre-selection). `total` = all rows.
- `/memory`: sort dropdown defaults to `Keyword finds (unbiased)`; rows show `<unbiased> · <total>` side-by-side. `SubRow` interface has both `keyword_count` + `post_count`.
- `/promo`: subreddit dropdown options labelled `r/SaaS (7 unbiased · 35 total)`, sorted by unbiased desc. `subAgg` shape is `[{subreddit, keyword_count, total_count}]`.
</paved_path>

<critical_notes>
## CRITICAL NOTES
- **API_BASE** - Uses NEXT_PUBLIC_API_BASE env var, falls back to localhost:8007
- **Auth** - Password stored in sessionStorage (cleared on tab close), sent via X-Access-Password header
- **POLL_INTERVAL = 5000ms** - 5 second polling for progressive updates
- **Client component** - Uses "use client" directive
- **No state library** - Plain React useState/useEffect
</critical_notes>
