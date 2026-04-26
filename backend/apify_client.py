"""
Apify client for Reddit scraping - handles both subreddit URLs and keyword searches.
"""
import httpx
import asyncio
import logging
import re

from api_logger import log_apify_call

logger = logging.getLogger(__name__)

# Apify endpoints for Reddit scraping (both URLs resolve to the same actor)
SUBREDDIT_SCRAPER_URL = "https://api.apify.com/v2/acts/fatihtahta~reddit-scraper-search-fast/run-sync-get-dataset-items"
KEYWORD_SCRAPER_URL = "https://api.apify.com/v2/acts/TwqHBuZZPHJxiQrTU/runs"

# Reddit /top is the only sort that takes ?t=<timeframe>; the others ignore it
TYPES_WITH_TIMEFRAME = {"top"}


def normalize_subreddit_name(raw: str) -> str:
    """
    Extract just the subreddit name from any input shape.
    Handles: 'n8n', '/n8n', 'r/n8n', '/r/n8n', 'reddit.com/r/Foo',
    'https://www.reddit.com/r/Foo/', 'https://www.reddit.com/r/Foo/top/?t=day', etc.
    Preserves the user's case (Reddit URL routing is case-insensitive but display matters).
    """
    s = raw.strip()
    # Strip protocol + host prefixes
    s = re.sub(r"^https?://", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^(www\.|m\.|old\.|new\.)?reddit\.com", "", s, flags=re.IGNORECASE)
    # Strip leading slashes and any 'r/' prefix
    s = s.lstrip("/")
    s = re.sub(r"^r/", "", s, flags=re.IGNORECASE)
    # Take only the segment up to the next slash (drops /top, /?t=day, etc.)
    name = s.split("/", 1)[0].strip()
    return name


def _canonical_key(p: dict) -> tuple:
    """
    Pick a stable key that identifies the same canonical Reddit post even when surfaced
    via different Apify result objects:
      - exact-link duplicates from multi-keyword search → collapse by post.id
      - cross-posts in different subreddits → collapse by (title, author)
        (Reddit crossposts duplicate both fields)
    Length guard: title must be >=20 chars to use (title, author) — short generic titles
    like "Help" or "Question" by frequent authors would otherwise false-merge.
    Falls back to post.id when title/author missing or title too short.
    """
    title = (p.get("title") or "").strip().lower()
    author = (p.get("author") or "").strip().lower()
    if title and author and len(title) >= 20:
        return ("ta", title, author)
    return ("id", p.get("id"))


def _dedupe_and_merge(posts: list[dict]) -> tuple[list[dict], int]:
    """
    Collapse duplicates / crossposts into one canonical post each.
    On the canonical post, attach `subreddit_sources: list[{subreddit, subreddit_subscribers, permalink}]`
    listing every subreddit the post was found in (preserving first-seen order, no duplicates).
    Returns (canonical_posts, count_of_dropped_duplicates).
    """
    by_key: dict[tuple, dict] = {}
    order: list[tuple] = []
    dropped = 0
    for p in posts:
        key = _canonical_key(p)
        source = {
            "subreddit": p.get("subreddit") or "",
            "subreddit_subscribers": int(p.get("subreddit_subscribers") or 0),
            "permalink": p.get("url") or "",
        }
        if key in by_key:
            dropped += 1
            existing = by_key[key]
            # Keep MAX score / num_comments across copies — a popular crosspost surfaced first
            # via a low-score subreddit shouldn't be filtered out by `score >= min_score` later.
            if int(p.get("score") or 0) > int(existing.get("score") or 0):
                existing["score"] = p.get("score")
            if int(p.get("num_comments") or 0) > int(existing.get("num_comments") or 0):
                existing["num_comments"] = p.get("num_comments")
            # If the canonical post has empty body but this copy has one, prefer the longer body
            if len(p.get("body") or "") > len(existing.get("body") or ""):
                existing["body"] = p.get("body")
            # Append this subreddit-source if we haven't already recorded it
            if not any(s["subreddit"] == source["subreddit"] for s in existing["subreddit_sources"]):
                existing["subreddit_sources"].append(source)
        else:
            merged = dict(p)
            merged["subreddit_sources"] = [source]
            by_key[key] = merged
            order.append(key)
    return [by_key[k] for k in order], dropped


def build_subreddit_url(name: str, sort_type: str = "top", timeframe: str = "day") -> str:
    """
    Build a canonical Reddit subreddit listing URL.
    sort_type: top | hot | new | best | rising  (only 'top' uses timeframe)
    timeframe: day | hour | week | month | year | all
    """
    base = f"https://www.reddit.com/r/{name}/{sort_type}/"
    if sort_type in TYPES_WITH_TIMEFRAME and timeframe:
        base = f"{base}?t={timeframe}"
    return base


class ApifyClient:
    """Client for fetching Reddit posts via Apify API."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.timeout = httpx.Timeout(120.0)  # 2 min timeout for API calls

    async def fetch_subreddit(self, url: str, max_retries: int = 2) -> list[dict]:
        """
        Fetch posts from a subreddit URL.
        Fetches up to 15 posts per subreddit, no comments.
        """
        payload = {
            "includeNsfw": False,
            "maxComments": 1,
            "maxPosts": 15,
            "scrapeComments": False,
            "urls": [url]
        }

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{SUBREDDIT_SCRAPER_URL}?token={self.api_token}",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    posts = response.json()

                    # Log successful API call
                    titles = [p.get("title", "")[:50] for p in posts[:3]]
                    log_apify_call(
                        call_type="subreddit",
                        endpoint=SUBREDDIT_SCRAPER_URL,
                        input_params={"url": url, **payload},
                        success=True,
                        posts_returned=len(posts),
                        result_summary=f"Posts: {titles}"
                    )

                    logger.info(f"[APIFY] Fetched {len(posts)} posts from {url}")
                    return posts
            except httpx.HTTPError as e:
                logger.warning(f"[APIFY] Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                else:
                    log_apify_call(
                        call_type="subreddit",
                        endpoint=SUBREDDIT_SCRAPER_URL,
                        input_params={"url": url, **payload},
                        success=False,
                        error=str(e)
                    )
                    logger.error(f"[APIFY] All retries failed for {url}")
                    return []

    async def fetch_keyword(self, keyword: str, max_retries: int = 2,
                            timeframe: str = "week", sort: str = "relevance",
                            max_posts: int = 20) -> list[dict]:
        """
        Fetch posts for a keyword search.
        Wraps keyword in double quotes for Reddit exact-phrase match.
        Defaults: sort=relevance, timeframe=week, strictSearch=false, 20 posts, no comments.
        Per-call overrides come from the frontend dropdowns via the /run request.
        """
        # Wrap in double quotes so Reddit treats it as an exact phrase, not OR-of-words
        quoted_keyword = f'"{keyword}"'
        payload = {
            "queries": [quoted_keyword],
            "sort": sort,
            "timeframe": timeframe,
            "strictSearch": False,
            "maxPosts": max_posts,
            "maxComments": 1,
            "scrapeComments": False,
            "includeNsfw": False
        }

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Start the run
                    run_response = await client.post(
                        f"{KEYWORD_SCRAPER_URL}?token={self.api_token}",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    run_response.raise_for_status()
                    run_data = run_response.json()

                    # Get dataset items (poll until ready)
                    dataset_id = run_data.get("data", {}).get("defaultDatasetId")
                    if not dataset_id:
                        log_apify_call(
                            call_type="keyword",
                            endpoint=KEYWORD_SCRAPER_URL,
                            input_params={"keyword": keyword, **payload},
                            success=False,
                            error="No dataset ID returned"
                        )
                        logger.error(f"[APIFY] No dataset ID for keyword: {keyword}")
                        return []

                    # Wait and fetch results
                    await asyncio.sleep(5)  # initial wait
                    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={self.api_token}"

                    for _ in range(12):  # max 1 minute polling
                        items_response = await client.get(dataset_url)
                        if items_response.status_code == 200:
                            posts = items_response.json()
                            if posts:
                                # Log successful API call
                                titles = [p.get("title", "")[:50] for p in posts[:3]]
                                log_apify_call(
                                    call_type="keyword",
                                    endpoint=KEYWORD_SCRAPER_URL,
                                    input_params={"keyword": keyword, **payload},
                                    success=True,
                                    posts_returned=len(posts),
                                    result_summary=f"Posts: {titles}"
                                )
                                logger.info(f"[APIFY] Fetched {len(posts)} posts for keyword: {keyword}")
                                return posts
                        await asyncio.sleep(5)

                    log_apify_call(
                        call_type="keyword",
                        endpoint=KEYWORD_SCRAPER_URL,
                        input_params={"keyword": keyword, **payload},
                        success=False,
                        error="Timeout waiting for results"
                    )
                    logger.warning(f"[APIFY] Timeout waiting for keyword results: {keyword}")
                    return []

            except httpx.HTTPError as e:
                logger.warning(f"[APIFY] Attempt {attempt + 1} failed for keyword {keyword}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    log_apify_call(
                        call_type="keyword",
                        endpoint=KEYWORD_SCRAPER_URL,
                        input_params={"keyword": keyword, **payload},
                        success=False,
                        error=str(e)
                    )
                    logger.error(f"[APIFY] All retries failed for keyword: {keyword}")
                    return []

    async def fetch_multiple_subreddits(self, inputs: list[str],
                                        sub_type: str = "top",
                                        sub_timeframe: str = "day") -> list[dict]:
        """
        Fetch posts from multiple subreddit inputs in parallel.
        `inputs` may be raw subreddit names or URLs in any common shape — we normalize and build the canonical URL.
        """
        # Normalize each input to a name and build the canonical URL ourselves
        urls = [build_subreddit_url(normalize_subreddit_name(s), sub_type, sub_timeframe)
                for s in inputs]
        tasks = [self.fetch_subreddit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten then dedupe (handles both exact-id duplicates AND title/author-matching crossposts);
        # canonical posts get a `subreddit_sources` list of every subreddit they appeared in.
        raw: list[dict] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                logger.error(f"[APIFY] Error fetching {urls[i]} (input='{inputs[i]}'): {result}")
                continue
            if result:
                raw.extend(result)
        canonical, dropped = _dedupe_and_merge(raw)
        if dropped:
            logger.info(f"[APIFY] Merged {dropped} duplicate/crosspost subreddit posts into canonical entries")
        return canonical

    async def fetch_multiple_keywords(self, keywords: list[str],
                                      timeframe: str | None = None,
                                      sort: str | None = None,
                                      max_posts: int | None = None) -> list[dict]:
        """Fetch posts for multiple keywords in parallel; per-call overrides forwarded if provided."""
        # Build kwargs only for overrides the caller actually set, so fetch_keyword's defaults remain authoritative
        kw: dict = {}
        if timeframe is not None:
            kw["timeframe"] = timeframe
        if sort is not None:
            kw["sort"] = sort
        if max_posts is not None:
            kw["max_posts"] = max_posts
        tasks = [self.fetch_keyword(k, **kw) for k in keywords]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Same dedupe behavior as the subreddit path — collapse exact-id repeats AND crossposts
        raw: list[dict] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                logger.error(f"[APIFY] Error fetching keyword {keywords[i]}: {result}")
                continue
            if result:
                raw.extend(result)
        canonical, dropped = _dedupe_and_merge(raw)
        if dropped:
            logger.info(f"[APIFY] Merged {dropped} duplicate/crosspost keyword posts into canonical entries")
        return canonical


def filter_posts_by_score(posts: list[dict], min_score: int = 5) -> list[dict]:
    """Filter posts with score >= min_score."""
    filtered = [p for p in posts if p.get("score", 0) >= min_score]
    logger.info(f"[FILTER] {len(filtered)}/{len(posts)} posts passed score >= {min_score}")
    return filtered
