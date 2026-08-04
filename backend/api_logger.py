"""
API call logger - logs all Apify and LLM API calls to a file with token consumption.
"""
import json
import logging
from datetime import datetime
from pathlib import Path

# Log file path
LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "api_calls.log"


def _ensure_log_dir():
    """Create logs directory if it doesn't exist."""
    LOG_DIR.mkdir(exist_ok=True)


def _get_file_logger():
    """Get or create file logger for API calls."""
    logger = logging.getLogger("api_calls")
    if not logger.handlers:
        _ensure_log_dir()
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_llm_call(
    call_type: str,
    prompt_length: int,
    response_length: int,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    model: str,
    success: bool,
    result_summary: str = "",
    error: str = "",
    metadata: dict | None = None
):
    """
    Log an LLM API call with token consumption.

    Args:
        call_type: Type of call (e.g., 'comment_evaluation', 'comment_generation')
        prompt_length: Length of prompt in characters
        response_length: Length of response in characters
        input_tokens: Number of input tokens consumed
        output_tokens: Number of output tokens generated
        total_tokens: Total tokens (input + output)
        model: Model name used
        success: Whether the call succeeded
        result_summary: Brief summary of result
        error: Error message if failed
        metadata: Additional workflow-specific data (e.g., posts_evaluated, posts_selected)
    """
    logger = _get_file_logger()

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "api": "openai",
        "type": call_type,
        "model": model,
        "success": success,
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens
        },
        "chars": {
            "prompt": prompt_length,
            "response": response_length
        },
        "result_summary": result_summary[:200] if result_summary else "",
        "error": error
    }

    # Add workflow metadata if provided
    if metadata:
        log_entry["metadata"] = metadata

    logger.info(json.dumps(log_entry))


def log_apify_call(
    call_type: str,
    endpoint: str,
    input_params: dict,
    success: bool,
    posts_returned: int = 0,
    result_summary: str = "",
    error: str = ""
):
    """
    Log an Apify API call.

    Args:
        call_type: Type of call ('subreddit' or 'keyword')
        endpoint: API endpoint called
        input_params: Parameters sent to API
        success: Whether the call succeeded
        posts_returned: Number of posts returned
        result_summary: Brief summary of results
        error: Error message if failed
    """
    logger = _get_file_logger()

    # Sanitize input_params to remove token
    safe_params = {k: v for k, v in input_params.items() if k != "token"}

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "api": "apify",
        "type": call_type,
        "endpoint": endpoint,
        "params": safe_params,
        "success": success,
        "posts_returned": posts_returned,
        "result_summary": result_summary[:200] if result_summary else "",
        "error": error
    }

    logger.info(json.dumps(log_entry))


def log_workflow_event(
    event_type: str,
    details: dict
):
    """
    Log workflow-level events and metrics.

    Args:
        event_type: Type of event (e.g., 'comment_evaluation_result', 'workflow_summary')
        details: Event-specific data
    """
    logger = _get_file_logger()

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "api": "workflow",
        "type": event_type,
        **details
    }

    logger.info(json.dumps(log_entry))


def get_token_summary() -> dict:
    """Read log file and return token consumption summary."""
    if not LOG_FILE.exists():
        return {"total_tokens": 0, "total_calls": 0, "by_type": {}}

    total_tokens = 0
    total_calls = 0
    by_type: dict[str, dict] = {}

    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("api") in ("openai", "bedrock"):  # count new + historical LLM log lines
                    tokens = entry.get("tokens", {}).get("total", 0)
                    call_type = entry.get("type", "unknown")

                    total_tokens += tokens
                    total_calls += 1

                    if call_type not in by_type:
                        by_type[call_type] = {"tokens": 0, "calls": 0}
                    by_type[call_type]["tokens"] += tokens
                    by_type[call_type]["calls"] += 1
            except json.JSONDecodeError:
                continue

    return {
        "total_tokens": total_tokens,
        "total_calls": total_calls,
        "by_type": by_type
    }
