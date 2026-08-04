"""
FastAPI application with 5 endpoints (+ /health) for Reddit comments and Reddit/LinkedIn post repurposing.
"""
import asyncio
import os
import uuid
import logging
import secrets  # timing-safe password comparison
from contextlib import asynccontextmanager
from dataclasses import asdict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from storage import storage
from workflow import run_workflow

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# --- Pydantic Models ---
class RunRequest(BaseModel):
    """Request body for POST /run endpoint."""
    input_type: str  # 'urls' or 'keywords'
    inputs: list[str]
    # Keyword-mode overrides (ignored when input_type='urls')
    timeframe: str | None = None  # day | week | month | year | all
    sort: str | None = None       # relevance | top
    max_posts: int | None = None  # per-keyword cap, frontend offers 10/20/30/50
    # Subreddit-mode overrides (ignored when input_type='keywords')
    sub_type: str | None = None        # top | hot | new | best | rising
    sub_timeframe: str | None = None   # day | hour | week | month | year | all (only used with sub_type='top')


class RunResponse(BaseModel):
    """Response for POST /run endpoint."""
    task_id: str


class StatusResponse(BaseModel):
    """Response for GET /status/{task_id} endpoint."""
    status: str
    progress: dict
    error_log: list[str] = []


class VerifyRequest(BaseModel):
    """Request body for POST /auth/verify endpoint."""
    password: str


# --- Auth Dependency ---
def verify_password(x_access_password: str = Header(None)) -> None:
    """Check X-Access-Password header against ACCESS_PASSWORD env var."""
    expected = os.getenv("ACCESS_PASSWORD")
    if not expected:
        raise HTTPException(500, "ACCESS_PASSWORD not configured")
    if not x_access_password or not secrets.compare_digest(x_access_password, expected):
        raise HTTPException(401, "Invalid or missing password")


# --- Lifespan for startup/shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start cleanup background task on startup."""
    cleanup_task = asyncio.create_task(storage.start_cleanup_loop(30))
    logger.info(f"[APP] Started cleanup background task (retention={storage.retention_days}d)")
    yield
    cleanup_task.cancel()
    logger.info("[APP] Cleanup task cancelled on shutdown")


# --- FastAPI App ---
app = FastAPI(
    title="Reddit & LinkedIn Content Discovery",
    description="Automate Reddit engagement and LinkedIn content discovery",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth Endpoint (unprotected) ---
@app.post("/auth/verify")
async def verify_auth(request: VerifyRequest):
    """Verify a password without requiring the header. Used by frontend login screen."""
    expected = os.getenv("ACCESS_PASSWORD")
    if not expected:
        raise HTTPException(500, "ACCESS_PASSWORD not configured")
    is_valid = secrets.compare_digest(request.password, expected)
    return {"valid": is_valid}


# --- Protected Endpoints ---
@app.post("/run", response_model=RunResponse, dependencies=[Depends(verify_password)])
async def start_run(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Start a new workflow run.
    Returns task_id for polling status.
    """
    # Validate input
    if request.input_type not in ("urls", "keywords"):
        raise HTTPException(400, "input_type must be 'urls' or 'keywords'")
    if not request.inputs:
        raise HTTPException(400, "inputs list cannot be empty")

    # Get API keys
    apify_token = os.getenv("APIFY_API_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not apify_token or not openai_api_key:
        raise HTTPException(500, "Missing API keys in environment")

    # Create task
    task_id = str(uuid.uuid4())
    storage.create_task(task_id, request.input_type, request.inputs)
    logger.info(f"[API] Created task {task_id} for {request.input_type}")

    # Run workflow in background; mode-specific overrides ignored when not applicable
    background_tasks.add_task(run_workflow, task_id, request.input_type,
                              request.inputs, apify_token, openai_api_key,
                              request.timeframe, request.sort, request.max_posts,
                              request.sub_type, request.sub_timeframe)

    return RunResponse(task_id=task_id)


@app.get("/status/{task_id}", response_model=StatusResponse, dependencies=[Depends(verify_password)])
async def get_status(task_id: str):
    """
    Get current status and progress for a task.
    Frontend polls this endpoint every 5 seconds.
    """
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    return StatusResponse(
        status=task.status,
        progress=task.progress,
        error_log=task.error_log
    )


@app.get("/results/{task_id}", dependencies=[Depends(verify_password)])
async def get_results(task_id: str):
    """
    Get full results for a completed task.
    Returns all data from the workflow.
    """
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    # Build results object
    results = {
        "task_id": task.task_id,
        "status": task.status,
        "input_type": task.input_type,
        "inputs": task.inputs,
        "created_at": task.created_at.isoformat(),

        # Post data
        "filtered_posts": task.filtered_posts,
        "total_posts_fetched": len(task.raw_apify_responses),

        # Comment workflow results
        "comment_evaluations": task.comment_evaluations,
        "generated_comments": task.generated_comments,
        "comment_validations": task.comment_validations,

        # Post repurposing workflow results (Reddit + LinkedIn)
        "post_scores": task.post_scores,
        "post_strategies": task.post_strategies,
        "post_validations": task.post_validations,

        # Step 2.5: per-post promo verdicts so the frontend can render the Promotional/Launch chip
        "promotional_detections": task.promotional_detections,

        # Metadata
        "step_timestamps": task.step_timestamps,
        "error_log": task.error_log,

        # Per-call LLM debug log (powers the bottom Prompt Debugger panel)
        "llm_calls": task.llm_calls,
    }

    return results


@app.get("/history", dependencies=[Depends(verify_password)])
async def get_history():
    """
    Get list of all runs within the configured retention window (default 7 days).
    """
    return storage.get_history()


# --- Subreddit Memory Bank: permanent archive of PASS/UNSURE posts ---
@app.get("/memory/subreddits", dependencies=[Depends(verify_password)])
async def get_memory_subreddits(page: int = 1, page_size: int = 25,
                                order: str = "desc", sort_by: str = "keyword_finds"):
    """Paginated list of subreddits. sort_by = keyword_finds (default, unbiased) | posts | members.
    Each row carries BOTH `post_count` (total) and `keyword_count` (unbiased) regardless of sort."""
    return storage.list_memory_subreddits(page=page, page_size=page_size, order=order, sort_by=sort_by)


@app.get("/memory/subreddits/{name}/posts", dependencies=[Depends(verify_password)])
async def get_memory_posts(name: str, page: int = 1, page_size: int = 25,
                           sort_by: str = "comments", order: str = "desc",
                           filter: str = "all", q: str | None = None):
    """Paginated posts within a subreddit, with sort / filter / title text-search."""
    return storage.list_memory_posts(
        subreddit=name, page=page, page_size=page_size,
        sort_by=sort_by, order=order, tag_filter=filter, q=q,
    )


# --- Promotional/Launch archive: dedicated dashboard data source ---
@app.get("/promotional", dependencies=[Depends(verify_password)])
async def get_promotional_posts(page: int = 1, page_size: int = 25,
                                sort_by: str = "upvotes", order: str = "desc",
                                filter: str = "all", promo_type: str = "all",
                                subreddit: str | None = None,
                                q: str | None = None):
    """Paginated list of promo-tagged posts with sort + tag/promo_type/subreddit filters + title search.
    `filter`: all | pass | unsure | fail | unrated. `promo_type`: all | launch | built-something | self-promo | subtle-mention.
    `subreddit`: filter posts whose subreddit_sources contains the named subreddit (cross-posts match if ANY source equals it)."""
    return storage.list_promotional_posts(
        page=page, page_size=page_size, sort_by=sort_by, order=order,
        tag_filter=filter, promo_type=promo_type, subreddit=subreddit, q=q,
    )


@app.get("/promotional/subreddits", dependencies=[Depends(verify_password)])
async def get_promotional_subreddits():
    """Subreddits that have any promo posts, sorted by post count DESC. Powers the /promo dropdown."""
    return storage.list_promotional_subreddits()


# --- Health check ---
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "tasks_in_memory": len(storage._tasks)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
