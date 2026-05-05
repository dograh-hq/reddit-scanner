# Principles to remember:
		Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.
		Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.
		A. Think Before Coding
		Don't assume. Don't hide confusion. Surface tradeoffs.
		Before implementing:
			• State your assumptions explicitly. If uncertain, ask.
			• If multiple interpretations exist, present them - don't pick silently.
			• If a simpler approach exists, say so. Push back when warranted.
			• If something is unclear, stop. Name what's confusing. Ask.
		B. Simplicity First
		Minimum code that solves the problem. Nothing speculative.
			• No features beyond what was asked.
			• No abstractions for single-use code.
			• No "flexibility" or "configurability" that wasn't requested.
			• No error handling for impossible scenarios.
			• If you write 200 lines and it could be 50, rewrite it.
		Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
		C. Surgical Changes
		Touch only what you must. Clean up only your own mess.
		When editing existing code:
			• Don't "improve" adjacent code, comments, or formatting.
			• Don't refactor things that aren't broken.
			• Match existing style, even if you'd do it differently.
			• If you notice unrelated dead code, mention it - don't delete it.
		When your changes create orphans:
			• Remove imports/variables/functions that YOUR changes made unused.
			• Don't remove pre-existing dead code unless asked.
		The test: Every changed line should trace directly to the user's request.
		D. Goal-Driven Execution
		Define success criteria. Loop until verified.
		Transform tasks into verifiable goals:
			• "Add validation" → "Write tests for invalid inputs, then make them pass"
			• "Fix the bug" → "Write a test that reproduces it, then make it pass"
			• "Refactor X" → "Ensure tests pass before and after"
		For multi-step tasks, state a brief plan:
		  1. [Step] → verify: [check]
      2. [Step] → verify: [check]
      3. [Step] → verify: [check]
		Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
		E. Always create a skill which contains  and checks against all the major failure points (failure points arise due to subtle nuances, or arise due to major changes int he code base and/or approach , or are typically pointed out by the user e.g. the user might have said that "gpt5.4 is the latest model, use it even if you are not aware of it"  or ") . you must maintain the major failure points in one short line each in a skill . and  check this skill everytime you make a change or a suggestion. All your claude.md should point to invooke this skill on changes as well as add small pointers for failure points after every change. the points should be really short and crisp (4-8 words each) . Note that your understanding on how to create skills is most likely outdated and wrong, here's how to create skill: https://code.claude.com/docs/en/skills (quick summary - need to create a sub directory under .claude and add a SKILL.md file there like this structure on project level "./.claude/skills/check-failures/SKILL.md" and the SKILL.md will have 2 parts in the file - a YAML frontmatter(name and description between --- markers) and markdown content (with instructions)  below that frontmatter - and you can invoke the skill with the skill name /check-failures 



<system_context>
Reddit Comment & Reddit/LinkedIn Content Discovery - Internal automation tool.
Scans Reddit for posts, generates comment suggestions via Claude Opus (Bedrock; model ID via `BEDROCK_MODEL_ID` env), and identifies viral content for repurposing as Reddit or LinkedIn posts.

Failure-points skill: invoke `/project-gotchas` before any code change in this repo. Append new gotchas to `.claude/skills/project-gotchas/SKILL.md` (4-8 word lines) when surprises surface.
</system_context>

<file_map>
## FILE MAP
- `/backend/` - FastAPI Python backend
  - `main.py` - API endpoints
  - `workflow.py` - 11-step workflow (parallel step 5; batched 6/8/9)
  - `storage.py` - SQLite-backed storage with in-memory cache (7-day retention)
  - `apify_client.py` - Reddit fetching
  - `llm_client.py` - Bedrock (Claude Opus; model ID via `BEDROCK_MODEL_ID` env) integration
  - `/prompts/` - 6 LLM prompt templates (4 of which are batched)
  - `/data/tasks.db` - SQLite task store (gitignored)
- `/frontend/` - Next.js React frontend
  - `/app/page.tsx` - Single page app
- `/.claude/skills/project-gotchas/SKILL.md` - failure-points checklist
- `todo-project-doc.md` - Full project documentation
- `must_follow_rules.md` - Coding rules
- `sample API response.md` - Apify response examples
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

### Tech Stack
- Backend: FastAPI (Python 3.13)
- Frontend: Next.js 15, React 19
- LLM: Claude Opus via AWS Bedrock Converse API (bearer auth, no boto3); model ID from `BEDROCK_MODEL_ID` env
- Reddit: Apify scraper API
- Storage: SQLite at `backend/data/tasks.db`, in-memory cache, 7-day retention (configurable via `config.json:retention_days`)

### Auth
- Shared password gate via `ACCESS_PASSWORD` env var
- Backend: `X-Access-Password` header checked on protected routes
- Frontend: Password screen → sessionStorage → `authFetch` wrapper
- Unprotected: `/health`, `/auth/verify`

### Key Flows
1. User enters password on login screen
2. User enters URLs or keywords
3. Backend fetches 10 posts per source via Apify (parallel)
4. Filter posts with score > min_score
5. LLM evaluates batch, generates comments in parallel (Semaphore=5), validates in one batched call
6. LLM scores all posts (one batched call) for Reddit/LinkedIn repurposing, generates strategies in one batched call, validates in one batched call
7. Frontend polls and displays results progressively
</paved_path>

<must_follow_rules>
## MISSION CRITICAL RULES
1. **Code with elegance** - Write clean and minimal code. Do not write anything extra or extra fetures.
2. **Clarify ambiguity** - Favor asking follow-up questions to ensure clear understanding of requirements before implementation.
3. **Preserve existing functionality** - NEVER reduce the scope of existing features/behaviors unless explicitly instructed to do so.
4. **create nested CLAUDE.md**
 - ULTRA CRITICAL: cladue.md files shall be created in every folder and subfolder where you have written any code. It should contain an updated context and overview of the code in that subfolder. Keep updating it if any code changes are made. 
5. **keep updating all CLAUDE.md files- it is a living documentation**
 - ULTRA CRITICAL: Treat all CLAUDE.md files as living API documentation for your future self. Always check for relevant CLAUDE.md files and DEFINITELY UPDATE them when changes impact their accuracy.
6. **Add good comments everywhere** -  add comments in your code to make it better documented. definitely add a one line comment in each file saying what it does and another comment on each function or class saying what it does. when using  external functions and  external libraries , then add a small 4-5 word comment on what it does as well
7. **Output user's next steps and testing instructions** -at every step make sure to output the next steps for the user like adding details in env file or setting up a supabase account etc.  And also share clear instructions on how the user can test the work so far.
8. **Write minimal code** -at every step make sure to write as little code as possible, do not write code for the sake of writing and defeintely dont write a lit of code - only write code thats enough to serve the given use case.
9.  **NEVER use `any` types** - Request user approval if tempted
10. **Update on change** - If code changes affect docs, update immediately- update and create claude.md for folders and subfolders. also update readme.md for context and any updates. When making updates , remove any old context that got changed.
11. **Maintain CHANGES.md** :- maintain a changes.md where you keep logging in the changes you make along with the reason why 
12. **Apify maxPosts varies by mode** - subreddit URL: 15 per source; keyword: 20 per query. Never change without explicit user ask.
13. **Graceful degradation** - Continue on failures, log clearly

</must_follow_rules>

<workflow>
## RUNNING THE APP

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn main:app --reload --port 8007
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Testing
1. Open http://localhost:3007
2. Enter the access password (set in backend `.env`)
3. Enter subreddit URLs or keywords
4. Click "Run Now"
5. Wait for results (polls every 5s)
</workflow>
