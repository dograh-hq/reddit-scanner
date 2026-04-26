"""
SQLite-backed task storage with configurable retention (default 7 days).
In-memory cache fronts SQLite so progressive polling stays cheap; SQLite is the source of truth across restarts.
"""
import asyncio
import json
import sqlite3
import threading
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# DB lives in backend/data/tasks.db (gitignored)
DB_PATH = Path(__file__).parent / "data" / "tasks.db"
CONFIG_PATH = Path(__file__).parent / "config.json"


@dataclass
class TaskData:
    """Container for all data related to a single workflow run."""
    task_id: str
    created_at: datetime
    input_type: str  # 'urls' or 'keywords'
    inputs: list[str]
    status: str = "running"  # running, complete, failed
    progress: dict = field(default_factory=dict)

    # Raw data
    raw_apify_responses: list[dict] = field(default_factory=list)
    filtered_posts: list[dict] = field(default_factory=list)

    # Step 2.5: per-post LLM verdict on whether the author is promoting / launching something they built
    # [{post_id, is_promotional, promo_type, reasoning}]
    promotional_detections: list[dict] = field(default_factory=list)

    # Comment workflow data
    comment_evaluations: list[dict] = field(default_factory=list)
    generated_comments: list[dict] = field(default_factory=list)
    comment_validations: list[dict] = field(default_factory=list)

    # Post-repurposing workflow data (Reddit + LinkedIn)
    post_scores: list[dict] = field(default_factory=list)
    post_strategies: list[dict] = field(default_factory=list)
    post_validations: list[dict] = field(default_factory=list)

    # Timestamps per step
    step_timestamps: dict = field(default_factory=dict)
    error_log: list[str] = field(default_factory=list)

    # Per-call LLM debug log (populated progressively during the run; consumed by the Prompt Debugger UI)
    llm_calls: list[dict] = field(default_factory=list)


def _task_to_json(t: TaskData) -> str:
    """Serialize TaskData to JSON string (datetime -> isoformat)."""
    d = asdict(t)  # dataclass -> dict deep copy
    d["created_at"] = t.created_at.isoformat()
    return json.dumps(d)  # dict -> JSON string


def _json_to_task(s: str) -> TaskData:
    """Deserialize TaskData from JSON string.
    Forward-compat: filter to currently-known dataclass fields so removed/renamed columns from
    older rows don't crash the load (`TaskData(**d)` would raise on unexpected kwargs).
    Missing keys are already tolerated via `default_factory=`.
    """
    d = json.loads(s)  # JSON string -> dict
    d["created_at"] = datetime.fromisoformat(d["created_at"])
    valid = {f.name for f in fields(TaskData)}
    return TaskData(**{k: v for k, v in d.items() if k in valid})


def _load_retention_days() -> int:
    """Read retention_days from config.json (default 7)."""
    try:
        if CONFIG_PATH.exists():
            return int(json.loads(CONFIG_PATH.read_text()).get("retention_days", 7))
    except Exception:
        pass
    return 7


class SqliteStorage:
    """SQLite-backed storage with in-memory cache. Single-writer; rare contention is acceptable per spec."""

    def __init__(self, retention_days: int = 7):
        self.retention_days = retention_days
        self._tasks: dict[str, TaskData] = {}
        self._lock = threading.Lock()  # serialize sqlite writes from background tasks
        DB_PATH.parent.mkdir(exist_ok=True)
        self._init_db()
        self._load_all()
        # Backfill source_input_type for any pre-migration bank rows whose source_task_id
        # is still in the loaded tasks. Older rows stay NULL → counted only in `total`, not `unbiased`.
        self._backfill_source_input_type()

    def _conn(self) -> sqlite3.Connection:
        # autocommit (isolation_level=None); per-call connection is simplest and thread-safe
        return sqlite3.connect(DB_PATH, isolation_level=None)

    def _init_db(self) -> None:
        """Create tasks + memory bank tables if missing.
        One-time migration: drop & recreate memory tables if their pre-multi-subreddit schema is present
        (project pre-production; user explicitly waived backward compat for this change)."""
        with self._lock, self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    input_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at)")

            # Detect old single-PK memory_posts schema and drop both memory tables for a clean recreate.
            cols = [r[1] for r in c.execute("PRAGMA table_info(memory_posts)").fetchall()]
            if cols and "subreddit_subscribers" not in cols:
                print("[STORAGE] Migrating memory_posts to composite-PK + subreddit_subscribers schema")
                c.execute("DROP TABLE IF EXISTS memory_posts")
                c.execute("DROP TABLE IF EXISTS memory_subreddits")

            # Memory Bank: permanent archive of PASS/UNSURE posts, grouped by subreddit.
            # Composite PK lets the same canonical post be saved against multiple subreddits (cross-posts).
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_posts (
                    post_id               TEXT NOT NULL,
                    subreddit             TEXT NOT NULL,
                    subreddit_subscribers INTEGER NOT NULL DEFAULT 0,
                    permalink             TEXT NOT NULL,
                    title                 TEXT NOT NULL,
                    flair                 TEXT,
                    summary               TEXT,
                    upvotes               INTEGER NOT NULL DEFAULT 0,
                    num_comments          INTEGER NOT NULL DEFAULT 0,
                    created_utc           REAL,
                    tag                   TEXT NOT NULL,
                    qualifying_gate       TEXT NOT NULL,
                    source_task_id        TEXT NOT NULL,
                    saved_at              TEXT NOT NULL,
                    PRIMARY KEY (post_id, subreddit)
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_mp_sub_comments ON memory_posts(subreddit, num_comments DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_mp_sub_upvotes  ON memory_posts(subreddit, upvotes DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_mp_sub_created  ON memory_posts(subreddit, created_utc DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_mp_sub_tag      ON memory_posts(subreddit, tag)")

            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_subreddits (
                    subreddit             TEXT PRIMARY KEY,
                    subreddit_subscribers INTEGER NOT NULL DEFAULT 0,
                    post_count            INTEGER NOT NULL DEFAULT 0,
                    last_saved_at         TEXT NOT NULL
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_ms_count ON memory_subreddits(post_count DESC)")

            # Promotional/Launch archive — permanent, like memory_posts, but ONE row per canonical
            # post (PK is post_id alone; subreddit_sources is stored as JSON to keep cross-post info).
            # validation_tag starts NULL at Step 2.5 detection time and is upgraded to
            # pass/unsure/fail by validation_hook() once the comment/post validation steps run.
            c.execute("""
                CREATE TABLE IF NOT EXISTS promotional_posts (
                    post_id            TEXT PRIMARY KEY,
                    title              TEXT NOT NULL,
                    body_excerpt       TEXT,
                    permalink          TEXT NOT NULL,
                    primary_subreddit  TEXT NOT NULL,
                    subreddit_sources  TEXT NOT NULL,
                    author             TEXT,
                    flair              TEXT,
                    upvotes            INTEGER NOT NULL DEFAULT 0,
                    num_comments       INTEGER NOT NULL DEFAULT 0,
                    created_utc        TEXT,
                    promo_type         TEXT NOT NULL,
                    promo_reasoning    TEXT,
                    validation_tag     TEXT,
                    source_task_id     TEXT NOT NULL,
                    detected_at        TEXT NOT NULL
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_pp_upvotes  ON promotional_posts(upvotes DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_pp_comments ON promotional_posts(num_comments DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_pp_created  ON promotional_posts(created_utc DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_pp_tag      ON promotional_posts(validation_tag)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_pp_type     ON promotional_posts(promo_type)")

            # ===== Migration: source_input_type column =====
            # Tags each bank row with the run's discovery mode ("urls" vs "keywords") so the
            # dashboards can compute an UNBIASED aggregate (keyword_count) alongside the total.
            # ALTERs are wrapped because re-runs against an already-migrated DB would error.
            for table in ("memory_posts", "promotional_posts"):
                try:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN source_input_type TEXT")
                    print(f"[STORAGE] Added source_input_type column to {table}")
                except sqlite3.OperationalError:
                    pass  # column already exists — re-run, no-op
            c.execute("CREATE INDEX IF NOT EXISTS idx_mp_sub_source ON memory_posts(subreddit, source_input_type)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_pp_source     ON promotional_posts(source_input_type)")

    def _backfill_source_input_type(self) -> None:
        """One-time backfill: walk loaded tasks and fill source_input_type on bank rows
        whose source_task_id matches a still-cached task. Called after _load_all().
        Older rows whose source task aged out stay NULL and are treated as "unknown".
        Safe to re-run — only updates rows where source_input_type IS NULL."""
        if not self._tasks:
            return
        try:
            with self._lock, self._conn() as c:
                total_mp, total_pp = 0, 0
                for tid, t in self._tasks.items():
                    cur = c.execute(
                        "UPDATE memory_posts SET source_input_type = ? "
                        "WHERE source_task_id = ? AND source_input_type IS NULL",
                        (t.input_type, tid),
                    )
                    total_mp += cur.rowcount
                    cur = c.execute(
                        "UPDATE promotional_posts SET source_input_type = ? "
                        "WHERE source_task_id = ? AND source_input_type IS NULL",
                        (t.input_type, tid),
                    )
                    total_pp += cur.rowcount
                if total_mp or total_pp:
                    print(f"[STORAGE] Backfilled source_input_type on {total_mp} memory_posts + {total_pp} promotional_posts rows")
        except Exception as e:
            print(f"[STORAGE] backfill failed (non-fatal): {e}")

    def _load_all(self) -> None:
        """Load all non-expired tasks into memory on startup."""
        cutoff = (datetime.utcnow() - timedelta(days=self.retention_days)).isoformat()
        with self._lock, self._conn() as c:
            rows = c.execute("SELECT data FROM tasks WHERE created_at >= ?", (cutoff,)).fetchall()
        for (data,) in rows:
            try:
                t = _json_to_task(data)
                self._tasks[t.task_id] = t
            except Exception as e:
                print(f"[STORAGE] Failed to load task: {e}")

    def create_task(self, task_id: str, input_type: str, inputs: list[str]) -> TaskData:
        """Create a new task entry and persist it."""
        task = TaskData(
            task_id=task_id,
            created_at=datetime.utcnow(),
            input_type=input_type,
            inputs=inputs,
        )
        self._tasks[task_id] = task
        self.persist(task_id)
        return task

    def get_task(self, task_id: str) -> Optional[TaskData]:
        """Retrieve task by ID from memory cache."""
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, **updates) -> bool:
        """Update task fields in memory (caller must call persist() to write through)."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return True

    def persist(self, task_id: str) -> None:
        """Write current in-memory state of a task to SQLite."""
        task = self._tasks.get(task_id)
        if not task:
            return
        try:
            with self._lock, self._conn() as c:
                c.execute(
                    "INSERT OR REPLACE INTO tasks (task_id, created_at, input_type, status, data) VALUES (?, ?, ?, ?, ?)",
                    (task.task_id, task.created_at.isoformat(), task.input_type, task.status, _task_to_json(task)),
                )
        except Exception as e:
            print(f"[STORAGE] persist failed for {task_id}: {e}")

    def get_history(self) -> list[dict]:
        """Get list of all tasks within retention window."""
        return [
            {
                "task_id": t.task_id,
                "timestamp": t.created_at.isoformat(),
                "input_type": t.input_type,
                "status": t.status,
            }
            for t in sorted(self._tasks.values(), key=lambda x: x.created_at, reverse=True)
        ]

    def cleanup_old_tasks(self) -> int:
        """Remove tasks older than retention window from memory and SQLite.
        INVARIANT: only the `tasks` table is touched here. `memory_posts` and `memory_subreddits`
        are intentionally permanent — the cleanup loop must never delete from them.
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        old_ids = [tid for tid, t in self._tasks.items() if t.created_at < cutoff]
        for tid in old_ids:
            del self._tasks[tid]
        if old_ids:
            try:
                with self._lock, self._conn() as c:
                    c.execute("DELETE FROM tasks WHERE created_at < ?", (cutoff.isoformat(),))
            except Exception as e:
                print(f"[STORAGE] cleanup delete failed: {e}")
        return len(old_ids)

    async def start_cleanup_loop(self, interval_minutes: int = 30):
        """Background task to cleanup old data every N minutes."""
        while True:
            await asyncio.sleep(interval_minutes * 60)
            count = self.cleanup_old_tasks()
            if count > 0:
                print(f"[STORAGE] Cleaned up {count} tasks older than {self.retention_days}d")

    # ---------- Memory Bank: permanent PASS/UNSURE post archive ----------

    def save_memory_posts(self, rows: list[dict], source_input_type: str) -> int:
        """
        Insert qualifying posts into memory_posts (idempotent on (post_id, subreddit)).
        Each canonical post may produce multiple rows — one per subreddit it was found in (cross-posts).
        Bumps memory_subreddits rollup only for newly-inserted rows; ALWAYS refreshes the
        subreddit_subscribers count on the rollup so the latest known value wins.
        Returns count of rows actually inserted (not duplicates).

        `source_input_type` ∈ {"urls","keywords"} tags the row with how this batch was discovered;
        powers the unbiased keyword-only count on the dashboard. INSERT OR IGNORE preserves
        first-seen value on conflict (a post first found via URL stays tagged "urls" even if
        re-discovered later via keywords).
        """
        if not rows:
            return 0
        now = datetime.utcnow().isoformat()
        inserted = 0
        try:
            with self._lock, self._conn() as c:
                for r in rows:
                    cur = c.execute(
                        """INSERT OR IGNORE INTO memory_posts
                           (post_id, subreddit, subreddit_subscribers, permalink, title, flair,
                            summary, upvotes, num_comments, created_utc, tag, qualifying_gate,
                            source_task_id, saved_at, source_input_type)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (r["post_id"], r["subreddit"],
                         int(r.get("subreddit_subscribers") or 0),
                         r["permalink"], r["title"],
                         r.get("flair"), r.get("summary"),
                         int(r.get("upvotes") or 0), int(r.get("num_comments") or 0),
                         r.get("created_utc"), r["tag"], r["qualifying_gate"],
                         r["source_task_id"], now, source_input_type),
                    )
                    is_new = cur.rowcount == 1
                    if is_new:
                        inserted += 1
                    # Always refresh the rollup (subscribers may grow/shrink over time).
                    # post_count only increments on first-save of a (post_id, subreddit) pair.
                    c.execute(
                        """INSERT INTO memory_subreddits
                               (subreddit, subreddit_subscribers, post_count, last_saved_at)
                           VALUES (?, ?, ?, ?)
                           ON CONFLICT(subreddit) DO UPDATE SET
                               subreddit_subscribers = excluded.subreddit_subscribers,
                               post_count = memory_subreddits.post_count + ?,
                               last_saved_at = excluded.last_saved_at""",
                        (r["subreddit"],
                         int(r.get("subreddit_subscribers") or 0),
                         1 if is_new else 0,
                         now,
                         1 if is_new else 0),
                    )
        except Exception as e:
            print(f"[STORAGE] save_memory_posts failed: {e}")
        return inserted

    def list_memory_subreddits(self, page: int = 1, page_size: int = 25,
                               order: str = "desc", sort_by: str = "keyword_finds") -> dict:
        """Paginated list of subreddits. Default sort: keyword_count DESC (the unbiased view —
        only counts posts discovered via keyword fetches, which have no subreddit pre-selection).
        `sort_by` ∈ {'keyword_finds' (default) | 'posts' | 'members'} — whitelisted.

        EVERY response row carries BOTH `post_count` (total) and `keyword_count` (unbiased)
        regardless of which sort is active, so the frontend can render both numbers side-by-side.
        """
        order_kw = "DESC" if order.lower() == "desc" else "ASC"
        sort_col = {
            "keyword_finds": "keyword_count",
            "posts": "post_count",
            "members": "subreddit_subscribers",
        }.get(sort_by, "keyword_count")
        offset = max(0, (page - 1)) * page_size
        # LEFT JOIN with the per-sub keyword count derived from memory_posts. COALESCE so
        # subreddits that have only URL-mode posts (and thus no row in the keyword grouping)
        # still surface with keyword_count=0, sorted last by the tiebreaker.
        sql = f"""
            SELECT s.subreddit, s.subreddit_subscribers, s.post_count, s.last_saved_at,
                   COALESCE(k.keyword_count, 0) AS keyword_count
            FROM memory_subreddits s
            LEFT JOIN (
                SELECT subreddit, COUNT(*) AS keyword_count
                FROM memory_posts
                WHERE source_input_type = 'keywords'
                GROUP BY subreddit
            ) k ON k.subreddit = s.subreddit
            ORDER BY {sort_col} {order_kw}, s.subreddit ASC
            LIMIT ? OFFSET ?
        """
        with self._lock, self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM memory_subreddits").fetchone()[0]
            rows = c.execute(sql, (page_size, offset)).fetchall()
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": [
                {"subreddit": s, "subreddit_subscribers": subs, "post_count": pc,
                 "last_saved_at": ls, "keyword_count": kc}
                for (s, subs, pc, ls, kc) in rows
            ],
        }

    def list_memory_posts(self, subreddit: str, page: int = 1, page_size: int = 25,
                          sort_by: str = "comments", order: str = "desc",
                          tag_filter: str = "all", q: str | None = None) -> dict:
        """Paginated posts within a subreddit with sort/filter/text-search."""
        # Whitelist sort_by + order to keep SQL safe
        sort_col = {"comments": "num_comments", "upvotes": "upvotes", "date": "created_utc"}.get(sort_by, "num_comments")
        order_kw = "DESC" if order.lower() == "desc" else "ASC"
        where = ["subreddit = ?"]
        params: list = [subreddit]
        if tag_filter in ("pass", "unsure"):
            where.append("tag = ?")
            params.append(tag_filter)
        if q:
            where.append("title LIKE ?")
            params.append(f"%{q}%")
        where_sql = " AND ".join(where)
        offset = max(0, (page - 1)) * page_size
        with self._lock, self._conn() as c:
            total = c.execute(f"SELECT COUNT(*) FROM memory_posts WHERE {where_sql}", tuple(params)).fetchone()[0]
            rows = c.execute(
                f"""SELECT post_id, permalink, title, flair, summary,
                           upvotes, num_comments, created_utc, tag,
                           qualifying_gate, saved_at, subreddit_subscribers
                    FROM memory_posts
                    WHERE {where_sql}
                    ORDER BY {sort_col} {order_kw}, post_id ASC
                    LIMIT ? OFFSET ?""",
                (*params, page_size, offset),
            ).fetchall()
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": [
                {"post_id": r[0], "permalink": r[1], "title": r[2], "flair": r[3],
                 "summary": r[4], "upvotes": r[5], "num_comments": r[6],
                 "created_utc": r[7], "tag": r[8], "qualifying_gate": r[9],
                 "saved_at": r[10], "subreddit_subscribers": r[11]}
                for r in rows
            ],
        }


    # ---------- Promotional/Launch archive: permanent style-reference collection ----------

    def save_promotional_posts(self, rows: list[dict], source_input_type: str) -> int:
        """Insert promo-tagged posts (idempotent on post_id). Re-detection of the same post
        UPDATES the metadata (upvotes / num_comments may have grown) but preserves the
        existing validation_tag (set later by update_promotional_validation) AND the
        existing source_input_type (first-seen wins — see comment in INSERT block).
        Returns count of NEWLY-inserted rows (not updates) — SQLite's UPSERT reports
        rowcount=1 for both INSERT and UPDATE, so we explicitly probe with a SELECT first.
        """
        if not rows:
            return 0
        now = datetime.utcnow().isoformat()
        inserted = 0
        try:
            with self._lock, self._conn() as c:
                for r in rows:
                    # Probe before the UPSERT so we can distinguish INSERT from UPDATE
                    pre = c.execute(
                        "SELECT 1 FROM promotional_posts WHERE post_id = ?",
                        (r["post_id"],),
                    ).fetchone()
                    is_new = pre is None
                    c.execute(
                        """INSERT INTO promotional_posts
                           (post_id, title, body_excerpt, permalink, primary_subreddit,
                            subreddit_sources, author, flair, upvotes, num_comments,
                            created_utc, promo_type, promo_reasoning, validation_tag,
                            source_task_id, detected_at, source_input_type)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(post_id) DO UPDATE SET
                               upvotes        = excluded.upvotes,
                               num_comments   = excluded.num_comments,
                               promo_type     = excluded.promo_type,
                               promo_reasoning= excluded.promo_reasoning,
                               subreddit_sources = excluded.subreddit_sources""",
                        # NOTE: source_input_type intentionally OMITTED from DO UPDATE SET — first-seen
                        # mode wins (matches the existing detected_at / source_task_id preservation).
                        (r["post_id"], r["title"], r.get("body_excerpt"), r["permalink"],
                         r["primary_subreddit"], json.dumps(r.get("subreddit_sources") or []),
                         r.get("author"), r.get("flair"),
                         int(r.get("upvotes") or 0), int(r.get("num_comments") or 0),
                         r.get("created_utc"), r["promo_type"], r.get("promo_reasoning"),
                         r.get("validation_tag"),  # usually None at detect time
                         r["source_task_id"], now, source_input_type),
                    )
                    if is_new:
                        inserted += 1
        except Exception as e:
            print(f"[STORAGE] save_promotional_posts failed: {e}")
        return inserted

    def update_promotional_validation(self, post_id: str, tag: str) -> bool:
        """Set validation_tag (pass/unsure/fail) on an existing promo post.
        Called once the workflow's comment/post validation steps produce a verdict.
        No-op if the post isn't in the table (e.g. wasn't detected as promo).
        """
        try:
            with self._lock, self._conn() as c:
                cur = c.execute(
                    "UPDATE promotional_posts SET validation_tag = ? WHERE post_id = ?",
                    (tag.lower(), post_id),
                )
                return cur.rowcount > 0
        except Exception as e:
            print(f"[STORAGE] update_promotional_validation failed for {post_id}: {e}")
            return False

    def list_promotional_posts(self, page: int = 1, page_size: int = 25,
                               sort_by: str = "upvotes", order: str = "desc",
                               tag_filter: str = "all", promo_type: str = "all",
                               subreddit: str | None = None,
                               q: str | None = None) -> dict:
        """Paginated list of promo posts with sort + filters + title search.
        tag_filter: all | pass | unsure | fail | unrated (=NULL — not yet validated)
        promo_type: all | launch | built-something | self-promo | subtle-mention
        subreddit: filter posts whose subreddit_sources contains the given subreddit
                   (cross-posts match if ANY source equals it). Case-insensitive.
        """
        # `detected_at` was removed as a sort option (it's just "when the workflow ran" — not
        # meaningful as a style-reference dimension); created_utc covers freshness instead.
        sort_col = {"upvotes": "upvotes", "comments": "num_comments",
                    "date": "created_utc"}.get(sort_by, "upvotes")
        order_kw = "DESC" if order.lower() == "desc" else "ASC"
        where: list[str] = []
        params: list = []
        if tag_filter == "unrated":
            where.append("validation_tag IS NULL")
        elif tag_filter in ("pass", "unsure", "fail"):
            where.append("validation_tag = ?")
            params.append(tag_filter)
        if promo_type in ("launch", "built-something", "self-promo", "subtle-mention"):
            where.append("promo_type = ?")
            params.append(promo_type)
        if subreddit:
            # Use SQLite's json_each to expand subreddit_sources and match if ANY source's
            # subreddit equals the filter value. Case-insensitive (Reddit normalizes anyway).
            where.append(
                "EXISTS (SELECT 1 FROM json_each(promotional_posts.subreddit_sources) je "
                "WHERE LOWER(json_extract(je.value, '$.subreddit')) = LOWER(?))"
            )
            params.append(subreddit)
        if q:
            where.append("title LIKE ?")
            params.append(f"%{q}%")
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        offset = max(0, (page - 1)) * page_size
        with self._lock, self._conn() as c:
            total = c.execute(f"SELECT COUNT(*) FROM promotional_posts{where_sql}", tuple(params)).fetchone()[0]
            rows = c.execute(
                f"""SELECT post_id, title, body_excerpt, permalink, primary_subreddit,
                           subreddit_sources, author, flair, upvotes, num_comments,
                           created_utc, promo_type, promo_reasoning, validation_tag,
                           source_task_id, detected_at
                    FROM promotional_posts{where_sql}
                    ORDER BY {sort_col} {order_kw}, post_id ASC
                    LIMIT ? OFFSET ?""",
                (*params, page_size, offset),
            ).fetchall()
        items = []
        for r in rows:
            try:
                sources = json.loads(r[5]) if r[5] else []
            except json.JSONDecodeError:
                sources = []
            items.append({
                "post_id": r[0], "title": r[1], "body_excerpt": r[2], "permalink": r[3],
                "primary_subreddit": r[4], "subreddit_sources": sources,
                "author": r[6], "flair": r[7], "upvotes": r[8], "num_comments": r[9],
                "created_utc": r[10], "promo_type": r[11], "promo_reasoning": r[12],
                "validation_tag": r[13], "source_task_id": r[14], "detected_at": r[15],
            })
        return {"page": page, "page_size": page_size, "total": total, "items": items}

    def list_promotional_subreddits(self) -> list[dict]:
        """Aggregate counts of promo posts per subreddit, summed across cross-post sources.
        Returns BOTH `keyword_count` (unbiased — only posts discovered via keyword fetches)
        and `total_count` (all sources). Sorted by keyword_count DESC, with total_count as
        tiebreaker, then alphabetical. Powers the /promo dashboard subreddit dropdown which
        labels each option `r/X (N unbiased · M total)`.
        """
        with self._lock, self._conn() as c:
            rows = c.execute(
                """SELECT json_extract(je.value, '$.subreddit') AS sub,
                          COUNT(*) AS total_count,
                          SUM(CASE WHEN p.source_input_type = 'keywords' THEN 1 ELSE 0 END) AS keyword_count
                   FROM promotional_posts p, json_each(p.subreddit_sources) je
                   WHERE sub IS NOT NULL AND sub != ''
                   GROUP BY sub
                   ORDER BY keyword_count DESC, total_count DESC, sub ASC"""
            ).fetchall()
        return [{"subreddit": s, "keyword_count": kc, "total_count": tc} for (s, tc, kc) in rows]


# Singleton instance with retention from config
storage = SqliteStorage(retention_days=_load_retention_days())
