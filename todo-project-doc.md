# Reddit Comment & LinkedIn Content Discovery - Project Documentation

## 1. Project Overview

**Purpose**: Internal tool to automate Reddit engagement (karma building) and LinkedIn content discovery by scanning subreddits, generating comment suggestions, and identifying viral posts for repurposing.

**Philosophy**: Minimal, hacky, flexible. Single workflow file with linear steps. Clear separation between prompts/context and code for easy open-sourcing.

**Tech Stack**:
- Backend: FastAPI (Python)
- Frontend: Next.js (React)
- LLM: Claude Opus 4.7 via AWS Bedrock
- Reddit: Apify Reddit Scraper API
- Storage: In-memory (24hr retention)

---

## 2. Core Features

### 2.1 Reddit Post Fetching

**Input Options** (mutually exclusive per run):
- **Subreddit URLs**: Multiple URLs allowed (e.g., `https://www.reddit.com/r/AI_Agents/top/?t=day`)
- **Keywords**: Multiple keywords allowed (e.g., "voice ai", "startup growth")

**Fetching Logic**:
- **Per Subreddit URL**: Fetch 10 posts using Apify scraper
  - API params: `maxPosts=10`, `scrapeComments=false`
  - URL timeframe parameter (e.g., `?t=day`) controlled by user input
  
- **Per Keyword**: Fetch 10 posts using Apify keyword search
  - API params: `maxPosts=10`, `scrapeComments=false`, `sort="top"`, `timeframe="week"` (fixed)

**Data Extracted** (store all):
- `score` (upvotes)
- `upvote_ratio`
- `title`
- `body`
- `num_comments`
- `subreddit`
- `created_utc`
- `url`
- `flair`
- `domain`
- `is_video`
- `author`
- `kind`

**Initial Filter**: Posts with `score > 5` only

---

### 2.2 Comment Generation Workflow

**Step 1: Batch Evaluation (Per Source)**
- **Input**: All filtered posts from one subreddit URL OR one keyword (single LLM call)
- **Prompt Context**:
  - Post: title, body, subreddit, upvotes, comments count, created_utc, flair
  - User profile injected from `config.json: user_context` (role, expertise, interests)
- **LLM Task**: Evaluate which posts are worth commenting on
- **Output**: YES/NO decision + reasoning for each post

**Step 2: Comment Generation (Per Selected Post)**
- **For each YES post**: Generate 2 comment suggestions
- **Prompt Requirements**:
  - Post summary (1-2 lines)
  - Expert value-add question: "What unique insights can I provide as an expert + contemporary developments?"
  - Style guidelines: Long, high-value, positive/nice, casual, can use bullet points, critical but polite
  - Include the 3 sample comments in prompt

**Step 3: Comment Validation**
- **Scoring System** (0-10 scale, 100 points total):
  1. **Post Virality** (40 points max): upvotes, engagement, trending potential
  2. **Post Relevance** (20 points max): fit with profile, expertise alignment
  3. **Comment Quality** (30 points max): value-add, tone, helpfulness
  4. **Community Fit** (10 points max): subreddit norms, appropriateness

- **Thresholds**:
  - PASS: ≥7.0
  - UNSURE: 5.0-6.9
  - FAIL: <5.0

- **Output**: Tag (PASS/FAIL/UNSURE) + score + reasoning

---

### 2.3 LinkedIn Content Discovery Workflow

**Runs sequentially after comment workflow on same posts**

**Step 1: Score Calculation (Batch Evaluation)**
- **Input**: Same filtered posts (batch per source)
- **LLM Task**: Calculate two scores for each post:
  
  **Virality Score (1-10)**:
  - High weightage on upvotes
  - Comments count
  - Trending velocity
  - Insight novelty
  - Value density
  
  **Fit Score (1-10)**:
  - Alignment with user profile (from `config.json: user_context`)
  - LinkedIn platform norms
  - Authenticity potential
  - Personalization feasibility

- **Output**: `virality_score`, `fit_score`, reasoning

**Step 2: Rewrite Strategy Generation (Per Post)**
- **For posts with scores ≥5**: Generate rewrite strategy paragraph (3-4 sentences)
- **Include**:
  - Tone/voice adjustments
  - Structural notes (hook, body, CTA)
  - Key insight to preserve
- **DO NOT**: Write the actual LinkedIn post

**Step 3: LinkedIn Validation**
- **Independent validator** (separate from comment validator)
- **Key Principle**: LinkedIn rewards NEW INSIGHTS and GENUINE VALUE, not generic advice

- **Scoring Logic**:
  - PASS: Virality ≥6 AND Fit ≥6
  - UNSURE: Either score 4-5.9
  - FAIL: Either score <4

- **Additional Checks**:
  - Does this bring NEW insights (not generic startup advice)?
  - Can this be authentically reframed from my voice?
  - Is there tangible value for LinkedIn audience?

- **Output**: Tag (PASS/FAIL/UNSURE) + reasoning

---

### 2.4 Data Storage & Run History

**In-Memory Storage (24hr retention)**:
- Store EVERYTHING per run:
  - Raw Apify API responses
  - All filtered posts
  - LLM evaluation decisions + reasoning
  - Generated comments (all 2 suggestions per post)
  - Comment validator scores + tags + reasoning
  - LinkedIn virality/fit scores + rewrite strategies
  - LinkedIn validator tags + reasoning
  - Timestamps for each step

**Run Management**:
- Each run gets unique `task_id`
- No timeouts - async task polling every 15 secs
- Run history accessible for 24 hours
- After 24h: Automatic cleanup of task mappings and data

---

### 2.5 Frontend UI (Minimal Next.js)

**Single Page Layout**:

**Input Section**:
- Radio toggle: "Subreddit URLs" OR "Keywords"
- Dynamic text input field (multi-line, comma/newline separated)
- "Run Now" button (triggers backend workflow)
- Default links in config loaded if input empty

**Results Dashboard** (3 sections, data dynamically inserted-  streaming like progressive filling):

1. **Selected Posts with Comments**
   - Post title + URL + other meta data in one line
   - post summary in 1 line
   - Subreddit
   - Upvotes, comments count
   - 2 comment suggestions
   - Comment validator tag (PASS/FAIL/UNSURE) + score
   
2. **LinkedIn Suggestions**
   - Post title + URL + other meta data in one line
   - post summary in 1 line
   - Virality score (X/10) + Fit score (X/10)
   - Rewrite strategy paragraph
   - LinkedIn validator tag (PASS/FAIL/UNSURE)
   
3. **Rejected Posts**
   - Post title + URL + other meta data in one line

**Filtering**:
- Filter by tag: PASS / FAIL / UNSURE (applies to both comment and LinkedIn sections independently)

**Run History**:
- Dropdown/list of last 24h runs (show task_id + timestamp)
- Click to load that run's dashboard

---

### 2.6 Slack Integration (Phase 2 - Future)

**Planned Features**:
- Send validated comment suggestions per post to Slack
- Send LinkedIn suggestions with metadata to Slack
- Display only - no action/approval automation needed
- Manual posting by user after Slack review

---

## 3. Configuration & Extensibility

### 3.1 Configuration Isolation

**Folder Structure** (simplified):
```
/backend
  /prompts
    - comment_evaluation.txt
    - comment_generation.txt
    - comment_validation.txt
    - post_scoring.txt
    - post_rewrite.txt
    - post_validation.txt
  - workflow.py (central linear workflow)
  - config.json (gitignored, user profile context)
  - .env (API keys)

/frontend
  /components
  /pages
```

**config.json** (gitignored; copy from `config.example.json`):
- `user_context` — user profile (role, expertise, interests)
- `product_context` — optional product-promotion bias
- Default subreddit URLs
- Threshold values (upvote filter, validator scores)

**All prompts** in `/prompts/` folder:
- Easy customization without touching code
- Include user context dynamically from config
- Sample comments embedded in generation prompts

---

### 3.2 Minimal Code Principles

**DO**:
- Single `workflow.py` with all steps linearly visible
- Basic FastAPI setup (no complex middleware)
- Simple Next.js components (no state management libs)
- Direct API calls (no unnecessary caching/queuing)
- In-memory storage only

**DON'T**:
- Authentication (internal tool)
- Rate limiting on backend (Apify handles Reddit limits)
- Complex error recovery (fail fast, log clearly using levels 4-5 levels like INFO DEBUG etc )
- Websockets (polling is fine)
- Docker (run locally)

---

### 3.3 Error Handling & Logging

**Required**:
- Proper error handling for LLM API failures
- Retry logic for Apify API calls
- Clear logging at each workflow step
- Graceful degradation (continue processing other posts if one fails)

**Memory Cleanup**:
- Cron job or scheduled task to clear 24h+ old data
- Clear task_id mappings
- Log cleanup actions

---

## 4. Workflow Execution Flow

**Linear Steps** (in `workflow.py`):

1. **Input Parsing**: URLs or Keywords
2. **Reddit Fetch**: Call Apify per source (parallel if multiple sources)
3. **Filter Posts**: `score > 5`
4. **Batch Comment Evaluation**: Per source, identify worth-commenting posts
5. **Comment Generation**: 2 suggestions per selected post
6. **Comment Validation**: Score + tag each comment
7. **Batch LinkedIn Scoring**: Virality + Fit scores per source
8. **LinkedIn Rewrite Strategy**: For posts with scores ≥4
9. **LinkedIn Validation**: Independent scoring + tagging
10. **Store Results**: In-memory with task_id
11. **Return to Frontend**: task_id for polling

**Task Polling**:
- Frontend polls backend with task_id - every 15 seconds
- Backend returns current progress + partial results
- No timeout - poll until complete or user cancels

---

## 5. API Specifications

### 5.1 Apify Reddit Scraper
-always keep maxPosts as 10 (not more, not less)
- scrapeComments must be false always

**Subreddit URL Call**:
```bash
curl -X POST "https://api.apify.com/v2/acts/fatihtahta~reddit-scraper-search-fast/run-sync-get-dataset-items?token=<TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "includeNsfw": false,
    "maxComments": 1,
    "maxPosts": 10,
    "scrapeComments": false,
    "urls": ["<REDDIT_URL>"]
  }'
```

**Keyword Search Call**:
```bash
curl -X POST "https://api.apify.com/v2/acts/TwqHBuZZPHJxiQrTU/runs?token=<TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["<KEYWORD>"],
    "sort": "top",
    "timeframe": "week",
    "maxPosts": 10,
    "maxComments": 1,
    "scrapeComments": false,
    "includeNsfw": false
  }'
```

**sample output**

[
  {
    "kind": "post",
    "query": "https://www.reddit.com/r/AI_Agents/top/?t=day",
    "id": "1p3kc7s",
    "title": "Stop burning money sending JSON to your agents.",
    "body": "I've been building agents for a while now as a freelancer, and there's this silent budget killer that nobody talks about. You're paying for punctuation.\n\nEvery time you send a JSON payload to an LLM, you're getting charged for every single brace, bracket, quote, and comma. And if you're sending lists of stuff, like user records, product catalogs, or transaction histories, you're repeating the same field names over and over.\n\n\"id\": 1, \"name\": \"Alice\"... \"id\": 2, \"name\": \"Bob\"...\n\nIt's wasteful. And frankly, it's kind of dumb when you're doing it at scale.\n\nI started messing around with this thing called TOON (Token-Oriented Object Notation) recently. It’s basically JSON on a diet. It strips out all the noise and structures data more like a table.\n\nInstead of repeating \"id\" and \"name\" fifty times, you define the header once and then just list the values. Clean. Simple.\n\nI ran a test on a support agent I'm building. We were feeding it customer order history. Switching from JSON to TOON cut the token count by like 45%.\n\nForty five percent.\n\nThat's almost half the cost gone, just by changing how we format the text.\n\nAnd the crazy part? The models actually seem to prefer it. I think because there's less noise, they hallucinate less on the structure. GPT-4 had zero issues parsing it.\n\nIf you're just sending a couple of fields, stick with JSON. It's fine. But if you're building RAG pipelines or agents that process heavy structured data, you are literally setting money on fire by not optimizing your format.\n\nIt’s a small tweak. But when you're running thousands of calls a day, those brackets add up fast.\n\nWorth a look if you care about your margins.\n\nAnyone else playing with this? Or are we all still married to curly braces?",
    "author": "Warm-Reaction-456",
    "score": 364,
    "upvote_ratio": 0.8,
    "num_comments": 121,
    "subreddit": "AI_Agents",
    "created_utc": "2025-11-22T04:40:12.000Z",
    "url": "https://www.reddit.com/r/AI_Agents/comments/1p3kc7s/stop_burning_money_sending_json_to_your_agents/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.AI_Agents",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "https://www.reddit.com/r/AI_Agents/top/?t=day",
    "id": "1p3m0ni",
    "title": "LangGraph vs CrewAI for Customer Support AI Agents: Which one is better for real tool-calling workflows?",
    "body": "I’m building a customer-support AI agent that needs **real tool calling**, not just chat.\n\nTypical workflows:\n\n* Fetching **order status**\n* **Rescheduling** an order\n* Pulling **pricing info**\n* Triggering backend APIs\n* Multi-step flows with memory & error handling\n\nI’m trying to decide between **LangGraph** and **CrewAI** for this.\n\nFrom your experience:\n\n* Which one handles structured tool-calling more reliably?\n* How do they behave in real production-like workflows?\n* Any issues with state management, retries, or deterministic execution?\n* Is one clearly better for long-running support flows vs short tasks?\n\nWould love to hear what others have built and what worked (or didn’t).  \n",
    "author": "Federal-Song-2940",
    "score": 7,
    "upvote_ratio": 1,
    "num_comments": 15,
    "subreddit": "AI_Agents",
    "created_utc": "2025-11-22T06:14:22.000Z",
    "url": "https://www.reddit.com/r/AI_Agents/comments/1p3m0ni/langgraph_vs_crewai_for_customer_support_ai/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.AI_Agents",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  }]

### 5.2 Backend API Endpoints

**POST /run**:
- Body: `{ "input_type": "urls" | "keywords", "inputs": ["..."] }`
- Returns: `{ "task_id": "..." }`

**GET /status/{task_id}**:
- Returns: `{ "status": "running" | "complete", "progress": {...}, "results": {...} }`

**GET /history**:
- Returns: `[ { "task_id": "...", "timestamp": "...", "input_type": "..." }, ... ]`

**GET /results/{task_id}**:
- Returns: Full results object for that run

---

## 6. Prompt Engineering Guidelines

### 6.1 User Context (Inject from config.json)

```
Example: "Senior engineer, 10 years in distributed systems.
Expertise: OSS, databases, developer tools, automation.
Interests: startup trends, AI developments, developer productivity."
```

### 6.2 Comment Evaluation Prompt Template

```
Context about me: <USER_CONTEXT>

Posts to evaluate:
<LIST_OF_POSTS>

For each post, decide: Should I comment?
Consider:
- Relevance to my expertise (see USER_CONTEXT)
- Opportunity to add unique value
- Community engagement potential
- Alignment with my interests

Output format: JSON array with YES/NO + reasoning
```

### 6.3 Comment Generation Prompt Template

```
Post: <TITLE> | <BODY>
Subreddit: <SUBREDDIT> | Upvotes: <SCORE> | Comments: <NUM_COMMENTS>

Generate 2 comment suggestions that:
- Add fresh perspective in plain English, informal tone
- Are long, super high value, positive/nice, casual
- Can use bullet points
- Can be critical but always polite and nice
- Can provide expert insights from my areas of expertise (see USER_CONTEXT)
- Can add data or best practises from any domain
- can add generic advise or generic comments on stuff 
- Reference contemporary developments where relevant

SAMPLE COMMENTS:
 SAMPLE COMMENT 1:
        "Yes, costs can grow faster than expected when chaining multiple steps together, especially if each step involves separate LLM API calls.
         - Multi-step pipelines can indeed be harder to track and manage cost-wise due to the cumulative nature of the costs associated with each individual call.
         - The choice of model per step can significantly impact costs, as different models may have varying pricing structures and performance characteristics.
         - To keep costs predictable, it's beneficial to monitor and analyze the performance and costs of each step in the pipeline, allowing for adjustments and optimizations as needed.
        For more insights on managing costs and performance in agentic applications, you might find this resource helpful: <<LINK>>"
    SAMPLE COMMNET 2:
        "You're not wrong. On the other hand:  
        * $100k is a fairly small RFP and some clients want to work with smaller firms. Even some of the ones that don't can be convinced if you're positioning is tight. A lot of pub-sec RFPs have a scoring system that prioritizes small and/or women/minority-owned businesses.  
        * Yes, formal proposals take a lot of time. They don't take nearly as much time after you do a few and have a library of materials. It's possible to create a very solid proposal that feels custom but only has about 10-15% new content.  
        * Since OP mentioned Public Purchase, he/she is talking about the public sector. And the public sector loves nothing more than domain expertise. Get a couple of contract under your belt as a sub to a larger effort (large planning/construction projects always need public-outreach subs) and suddenly your size is less of a disadvantage because you can lean on the gov expertise."
    SAMPLE COMMENT 3:
        "Whether peopel realize it or not, everyone is a business. When you’re an employee you signed up for one indefinite customer. When you’re an entrepreneur you’re just selling more stuff.
        The question really is: will your business generate more than if you sold to one customer?
        If not, sell out"

Output: 2 distinct comments
```

### 6.4 LinkedIn Scoring Prompt Template

```
My Profile: <USER_CONTEXT>

Post: <CONTENT>
Engagement: <UPVOTES> upvotes, <NUM_COMMENTS> comments

Calculate:
1. Virality Score (1-10): High weightage on upvotes, comments, trending velocity, insight novelty, value density
2. Fit Score (1-10): Alignment with my profile, LinkedIn platform norms, authenticity potential

Key principle: LinkedIn rewards NEW INSIGHTS and GENUINE VALUE, not generic advice.

Output: { "virality_score": X, "fit_score": Y, "reasoning": "..." }
```

### 6.5 LinkedIn Rewrite Strategy Prompt Template

```
Post: <CONTENT>
Virality: <SCORE>/10 | Fit: <SCORE>/10

Write a short paragraph (3-4 sentences) on how to reframe this for LinkedIn:
- Tone/voice adjustments for my authentic voice
- Structural notes (hook, body, CTA)
- Key insight to preserve from Reddit post
- How to add my personal expertise angle

DO NOT write the actual LinkedIn post.
```

---

## 7. Success Metrics & Goals

**Primary Goal**: Build Reddit karma through valuable comments

**Secondary Goal**: Identify viral LinkedIn content opportunities

**Avoid**: Self-promotion, product pushing, generic advice

**Key Principles**:
- Add genuine value to communities
- Leverage unique expertise (from USER_CONTEXT)
- Stay authentic and helpful
- Build following through quality engagement

---

## 8. Future Extensibility

**Phase 2 Features** (not in initial build):
- Slack approval workflow automation
- Auto-posting approved comments to Reddit
- Multi-platform support (HackerNews, Twitter/X)
- Advanced analytics dashboard
- A/B testing comment variations
- LLM model switching (GPT-4 vs Claude)

**Merge Considerations**:
- Modular workflow design allows integration with other automation tools
- Config-driven prompts enable easy customization for different users
- Clear separation of concerns supports future feature additions

---

## 9. Environment Variables (.env)

```
OPENAI_API_KEY=<key>
APIFY_API_TOKEN=<token>
SLACK_WEBHOOK_URL=<url>  # Phase 2
REDDIT_CLIENT_ID=<id>     # Phase 2 (for posting)
REDDIT_CLIENT_SECRET=<secret>  # Phase 2
```

---
## 10. Clairifications

**ON WORKFLOW**
- Generate comments immediately after YES evaluation, and then validator scores them.
- The initial evaluation determines IF we comment and gives selected posts .Then an LLM call to generate comments on the selected posts one by one (Generate comments immediately after YES evaluation, then validator scores them.) .  The validator then scores the POST + GENERATED COMMENT together for quality/fit. These are separate steps but validator uses evaluation output.
- LinkedIn Validator Flow: Calculate virality + fit scores . then Generate rewrite strategy. then  independent validator checks ✅

- if Apify returns <10 posts => then process the posts that were returned
- if all posts from a subreddit fail evaluation- then simply move to next batch. infac tthis might be true very often
- when LLM returns invalid JSON/format- then push a clear error log with details and remind me on the frontend UI as well and push the the text from LLM to the next step as it is

**workflow.py structure should be documented**:

def run_workflow(input_type, inputs):
    #1. Parse inputs
    #2. Fetch from Reddit (Apify)
    #3. Filter posts (>5 upvotes)
    #4. Batch evaluate for comments
    #5. Generate comments (for YES posts)
    #6. Validate comments
    #7. Batch evaluate for LinkedIn
    #8. Generate LinkedIn strategies
    #9. Validate LinkedIn suggestions
    #10. Store results
    #11. Return task_id

**Technical**:
- LLM Model Parameters to consider Temperature, max_tokens to be 20000 tokens wherever necessary
- Use python13  and latest compatible package/modules and latest nextjs
- No testing needed - purely manual for now
---

## 11. Development Priorities

**P0 (MVP)**:
- Reddit fetching (URLs + keywords)
- Comment generation + validation
- LinkedIn scoring + validation
- Basic frontend with results display
- 24hr in-memory storage
- Run history

**P1 (Near-term)**:
- Filtering by even more tags in UI
- Better error handling/logging
- Prompt optimization based on results

**P2 (Phase 2)**:
- Slack integration
- Reddit posting automation
- Advanced features

---

**End of Project Documentation**