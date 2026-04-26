# Reddit Comment & Reddit/LinkedIn Content Discovery

Toolkit for Reddit engagement and content repurposing (Claude Opus 4.7 via AWS Bedrock + Apify).
Scans Reddit for relevant posts to comment on and makes suggestions for comments. Also collects posts that can be replicated on Reddit or LinkedIn. Also collects the list of subreddits with domain relevant posts over lifetime. Also collects promotional/launch posts that can be replicated.

## Features
- Scans Reddit for relevant posts to comment on and makes suggestions for comments. 
- Also collects posts that can be replicated on Reddit or LinkedIn. 
- Also collects the list of subreddits with domain relevant posts over lifetime. 
- Also collects promotional/launch posts that can be replicated.

- **Reddit Post Fetching**: Scan subreddits by URL or keywords via Apify
- **Comment Generation**: Claude Opus 4.7 (Bedrock) generates 2 comment suggestions per post in parallel
- **Comment Validation**: Single batched LLM call scores and tags (PASS/UNSURE/FAIL) all comments
- **Reddit + LinkedIn Repurposing**: Identifies viral posts I can repurpose as my own Reddit or LinkedIn content
- **Rewrite Strategies**: Single batched call generates strategy paragraphs (not actual posts), calling out best channel
- **Run History**: SQLite-backed storage with 7-day retention (configurable), survives server restart

## Quick Start

### 1. Backend adn Frontend Setup

```bash
python3.13 -m venv .venv && source .venv/bin/activate 
cd backend
pip install -r requirements.txt

# Create .env file with your API keys and access password
cp .env.example .env
# Edit .env and add:
# BEDROCK_API_KEY=your-bedrock-bearer-api-key
# APIFY_API_TOKEN=apify_api_your-token
# ACCESS_PASSWORD=your-strong-password-here
Similarly config.json

# Start the server
uvicorn main:app --port 8007
```

#### 1.2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
add .env.production file:  NEXT_PUBLIC_API_BASE=http://${EC2_IP}:8007
### 2. Quick internal deployment on IP:Port ec2:
create logs and data directory inside backend
  cd backend && mkdir -p data logs

Add files backend/.env backend/config.json and frontend/.env.production
frontend/.env.production to have NEXT_PUBLIC_API_BASE=http://IP:8007
**Start backend with PM2 (uses the venv's uvicorn)**
  pm2 start "/home/ubuntu/app/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8007"  --name reddit-scanner-backend --cwd /home/ubuntu/app/backend

**Start Frontend**
  cd ~/app/frontend
  EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
  echo "NEXT_PUBLIC_API_BASE=http://${EC2_IP}:8007" > .env.production
  npm install
  npm run build
  pm2 start "npm run start" --name reddit-scanner-frontend --cwd /home/ubuntu/app/frontend


### What you need to do (post-pull checklist)

- Add BEDROCK_API_KEY to .env
- Drop OPENAI_API_KEY from .env
- pip install -r requirements.txt
- Restart backend (creates SQLite DB)
- Smoke-test Bedrock curl
- Run single subreddit
- Confirm ~10 LLM calls
- Verify history persists after restart

### 3. Use the App

1. Open http://localhost:3007
2. Enter the access password (from `ACCESS_PASSWORD` in backend `.env`)
3. Select "Subreddit URLs" or "Keywords"
4. Enter your inputs (one per line or comma-separated)
5. Click "Run Now"
6. Wait for results (auto-polls every 5 seconds)

## Configuration

Copy `backend/config.example.json` to `backend/config.json` and edit:

```json
{
  "user_context": "Your professional background, expertise, interests...",
  "product_context": "Optional: product/project you want to promote. The LLM will favor relevant posts. Leave as empty string if not applicable.",
  "default_urls": ["https://www.reddit.com/r/AI_Agents/top/?t=day"],
  "min_score": 5,
  "comment_pass_threshold": 70,
  "post_score_threshold": 5,
  "retention_days": 7
}
```

`config.json` is gitignored, so your personal details stay local.

## LLM (Bedrock)

All LLM calls go through Claude Opus 4.7 on AWS Bedrock via the Converse API:

- Endpoint: `https://bedrock-runtime.us-east-1.amazonaws.com/model/us.anthropic.claude-opus-4-7/converse`
- Auth: `Authorization: Bearer ${BEDROCK_API_KEY}` (Bedrock API key, not SigV4 / boto3)
- Concurrency cap: `Semaphore(5)` per workflow run

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/verify` | POST | No | Verify password (login) |
| `/health` | GET | No | Health check |
| `/run` | POST | Yes | Start a new workflow run |
| `/status/{task_id}` | GET | Yes | Get task status and progress |
| `/results/{task_id}` | GET | Yes | Get full results |
| `/history` | GET | Yes | List all runs from last `retention_days` (default 7) |

Protected endpoints require `X-Access-Password` header.

## Deployment

Recommended path: AWS EC2 + PM2 (single uvicorn worker), with `backend/data/tasks.db` on the instance disk for SQLite persistence across deploys.

```bash
# On EC2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8007" --name reddit-scanner-backend --cwd /path/to/backend
pm2 save
```

**Key production steps:**
1. Set `NEXT_PUBLIC_API_BASE` to your backend URL
2. Restrict CORS in `main.py` to your frontend domain
3. Use a strong `ACCESS_PASSWORD` (20+ characters)
4. Ensure `backend/data/` is writable and persists across deploys

## Tech Stack

- **Backend**: FastAPI, Python 3.13
- **Frontend**: Next.js 15, React 19
- **LLM**: Claude Opus 4.7 via AWS Bedrock Converse API
- **Reddit API**: Apify Reddit Scraper
- **Storage**: SQLite at `backend/data/tasks.db` with in-memory cache (7-day retention)

## Responsible Use

This tool generates AI-assisted suggestions for manual review. Do not use it for spam, impersonation, or mass-automated posting. Respect Reddit and LinkedIn Terms of Service.

## License

MIT — see [LICENSE](LICENSE).


Okay, so now I want you to separately maintain counts from keyword runs only, both for the subreddit memory bank as well as the promotional bank. In the subreddit memory bank, the score_by should add one more criterion, which is posts from keyword searches, and make this criterion default. Feel free to name it properly. 
And for context of the promotional bank, keep a counter (say X)  which is promotional posts fetched from keyword searches only. In the subreddit filter, the brackets can have the numbers that denotes how many unbiased and how many total  promotional posts exist in that subreddit, but they should be sorted in order of counts from the unbiased counter X e.g. r/SaaS (7 unbiased, 35 total) . feel free to use a different or better fitting word than unbiased if you want. (Note: name the counter properly and dont call it X - X is just for reference in this instruction)
The guided tour tip should highlight that these are in descending order of unbiased criteria and hence in descending order of occurrence of promotional posts in blind fetch. 
Similarly, guided tour tip in subreddit memory bank also should highlight this fact. 