"""
Main workflow orchestrator - 11-step linear workflow for Reddit comments and Reddit/LinkedIn post repurposing.
Step 5 runs in parallel; steps 6, 8, 9 are batched into one LLM call each.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from storage import storage, TaskData
from apify_client import ApifyClient
from llm_client import LLMClient
from api_logger import log_workflow_event

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Load user config from config.json."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"user_context": "", "default_urls": [], "min_score": 5}


async def run_workflow(task_id: str, input_type: str, inputs: list[str],
                       apify_token: str, openai_api_key: str,
                       kw_timeframe: str | None = None,
                       kw_sort: str | None = None,
                       kw_max_posts: int | None = None,
                       sub_type: str | None = None,
                       sub_timeframe: str | None = None) -> None:
    """
    Main workflow execution - runs all 11 steps sequentially.
    Updates task storage with progress and results at each step.
    """
    config = load_config()
    user_context = config.get("user_context", "")
    product_context = config.get("product_context", "")

    task = storage.get_task(task_id)
    if not task:
        logger.error(f"[WORKFLOW] Task {task_id} not found")
        return

    apify = ApifyClient(apify_token)
    llm = LLMClient(openai_api_key)

    try:
        # ===== STEP 1: Parse Inputs =====
        _log_step(task, 1, "Parsing inputs", llm)
        logger.info(f"[WORKFLOW] Step 1: Parsing {len(inputs)} {input_type}")

        # ===== STEP 2: Fetch from Reddit =====
        _log_step(task, 2, "Fetching from Reddit", llm)
        logger.info(f"[WORKFLOW] Step 2: Fetching posts via Apify")

        if input_type == "urls":
            # Forward sub_type/sub_timeframe only if provided; defaults stay in apify_client
            sub_kwargs: dict = {}
            if sub_type is not None:
                sub_kwargs["sub_type"] = sub_type
            if sub_timeframe is not None:
                sub_kwargs["sub_timeframe"] = sub_timeframe
            all_posts = await apify.fetch_multiple_subreddits(inputs, **sub_kwargs)
        else:
            all_posts = await apify.fetch_multiple_keywords(
                inputs, timeframe=kw_timeframe, sort=kw_sort, max_posts=kw_max_posts
            )

        task.raw_apify_responses = all_posts
        storage.update_task(task_id, progress={"step": 2, "posts_fetched": len(all_posts)})
        storage.persist(task_id)

        # ===== STEP 2.5: Promotional / Launch detection (one batched LLM call) =====
        # Runs BEFORE any filtering / scoring so even posts that later get rejected by the
        # comment- or post-validation gates still land in the permanent promotional_posts archive.
        # Frontend shows a "Promotional/Launch" chip on every card matching one of these post_ids,
        # plus a dedicated /promo dashboard sourced from the SQLite table.
        _log_step(task, 2, "Detecting promotional / launch posts", llm)
        logger.info(f"[WORKFLOW] Step 2.5: Detecting promo/launch among {len(all_posts)} canonical posts")
        try:
            promo_detections = await llm.detect_promotional_posts_batch(all_posts)
        except Exception as e:
            logger.error(f"[WORKFLOW] Promo detection failed (non-fatal): {e}")
            task.error_log.append(f"Promotional detection batch failed: {e}")
            promo_detections = []
        task.promotional_detections = promo_detections
        promo_yes = [d for d in promo_detections if d.get("is_promotional")]
        logger.info(f"[WORKFLOW] Step 2.5: {len(promo_yes)}/{len(all_posts)} flagged as promotional/launch")

        # Persist flagged posts to the permanent archive (validation_tag stays NULL until later steps)
        if promo_yes:
            try:
                rows = _build_promo_rows(promo_yes, all_posts, task.task_id)
                storage.save_promotional_posts(rows, source_input_type=task.input_type)
            except Exception as e:
                logger.error(f"[WORKFLOW] Promo archive save failed (non-fatal): {e}")
                task.error_log.append(f"Promotional archive save failed: {e}")

        # ===== STEP 3: Pass-through (score filter removed) =====
        # Every canonical post flows into the LLM pipeline regardless of upvote count.
        # Frontend partitions score < 5 posts into a visually-demoted collapsed sub-section.
        _log_step(task, 3, "All posts retained (no score filter)", llm)
        filtered = all_posts
        task.filtered_posts = filtered
        logger.info(f"[WORKFLOW] Step 3: {len(filtered)} posts (no score filter)")

        if not filtered:
            logger.warning("[WORKFLOW] No posts to process, ending workflow")
            task.status = "complete"
            storage.persist(task_id)
            return

        # ===== STEP 4: Batch Evaluate for Comments =====
        _log_step(task, 4, "Evaluating posts for comments", llm)
        logger.info(f"[WORKFLOW] Step 4: Batch evaluating {len(filtered)} posts")

        evaluations = await llm.evaluate_posts_for_comments(filtered, user_context, product_context)
        task.comment_evaluations = evaluations
        # Surface silent LLM drops to the user — ids the LLM hallucinated/omitted are filtered out
        # by llm_client's id_to_index lookup, so a count delta means lost evaluations.
        missing_eval = len(filtered) - len(evaluations)
        if missing_eval > 0:
            task.error_log.append(
                f"Step 4 (comment evaluation): LLM returned {len(evaluations)}/{len(filtered)} posts; "
                f"{missing_eval} silently dropped (output truncation or hallucinated post_id)."
            )

        # Get YES posts (preserve order from evaluations)
        yes_indices = [e["post_index"] for e in evaluations
                       if e.get("decision", "").upper() == "YES"]
        yes_indices = [i for i in yes_indices if i < len(filtered)]
        yes_posts = [filtered[i] for i in yes_indices]
        logger.info(f"[WORKFLOW] {len(yes_posts)} posts selected for commenting")

        log_workflow_event("comment_evaluation_result", {
            "posts_evaluated": len(filtered),
            "posts_selected": len(yes_posts),
            "posts_rejected": len(filtered) - len(yes_posts),
            "selection_rate": f"{(len(yes_posts) / len(filtered) * 100):.1f}%" if filtered else "0%",
            "llm_calls": 1
        })

        # ===== STEP 5: Generate Comments (PARALLEL) =====
        _log_step(task, 5, "Generating comments", llm)
        logger.info(f"[WORKFLOW] Step 5: Generating comments for {len(yes_posts)} posts in parallel")

        # Single group_id for all parallel Step 5 calls so the Prompt Debugger groups them under one accordion
        step5_group = uuid.uuid4().hex

        async def _gen_one(idx: int, post: dict) -> dict:
            """Generate comments for a single post; degrade gracefully on error."""
            try:
                comments = await llm.generate_comments(post, user_context, _debug_group_id=step5_group)
                return {"post_id": post.get("id"), "post_index": idx, "comments": comments}
            except Exception as e:
                logger.error(f"[WORKFLOW] Error generating comments for post {post.get('id')}: {e}")
                task.error_log.append(f"Comment generation failed for {post.get('id')}: {e}")
                return {"post_id": post.get("id"), "post_index": idx, "comments": ["Error generating comment", ""]}

        generated_comments = await asyncio.gather(
            *[_gen_one(yes_indices[i], post) for i, post in enumerate(yes_posts)]
        )
        task.generated_comments = generated_comments

        log_workflow_event("comment_generation_result", {
            "posts_with_comments": len(generated_comments),
            "comments_generated": len(generated_comments) * 2,
            "llm_calls": len(yes_posts)
        })

        # ===== STEP 6: Validate Comments (BATCHED, 1 LLM call) =====
        _log_step(task, 6, "Validating comments", llm)
        logger.info(f"[WORKFLOW] Step 6: Batch-validating {len(generated_comments)} comment sets")

        val_items = []
        for gc in generated_comments:
            post = filtered[gc["post_index"]] if gc["post_index"] < len(filtered) else {}
            val_items.append({
                "post_id": gc["post_id"],
                "title": post.get("title", ""),
                "body": post.get("body", ""),
                "upvotes": post.get("score", 0),
                "comments": gc["comments"],
            })
        try:
            comment_validations = await llm.validate_comments_batch(val_items, user_context, product_context)
        except Exception as e:
            logger.error(f"[WORKFLOW] Batch comment validation failed: {e}")
            task.error_log.append(f"Comment validation batch failed: {e}")
            err = {"score": 0, "tag": "ERROR", "reasoning": str(e)[:200]}
            comment_validations = [{"post_id": it["post_id"], "validations": [err, err]} for it in val_items]
        task.comment_validations = comment_validations

        pass_count = sum(1 for cv in comment_validations for v in cv["validations"]
                         if v.get("tag", "").upper() == "PASS")
        log_workflow_event("comment_validation_result", {
            "comments_validated": sum(len(cv["validations"]) for cv in comment_validations),
            "pass_count": pass_count,
            "llm_calls": 1
        })

        # ===== STEP 7: Batch Score Posts (Reddit + LinkedIn fit) =====
        _log_step(task, 7, "Scoring posts for repurposing", llm)
        logger.info(f"[WORKFLOW] Step 7: Scoring {len(filtered)} posts for Reddit/LinkedIn repurposing")

        post_scores = await llm.score_posts(filtered, user_context, product_context)
        task.post_scores = post_scores
        missing_score = len(filtered) - len(post_scores)
        if missing_score > 0:
            task.error_log.append(
                f"Step 7 (post scoring): LLM returned {len(post_scores)}/{len(filtered)} posts; "
                f"{missing_score} silently dropped (output truncation or hallucinated post_id)."
            )

        # Get posts with SELECT decision (both virality >= 7 AND fit >= 7)
        high_score_indices = [
            s["post_index"] for s in post_scores
            if s.get("decision", "").upper() == "SELECT" and s.get("post_index", -1) < len(filtered)
        ]
        logger.info(f"[WORKFLOW] {len(high_score_indices)} posts selected for repurposing strategy")

        ignored_count = len(filtered) - len(high_score_indices)
        log_workflow_event("post_scoring_result", {
            "posts_scored": len(filtered),
            "posts_selected": len(high_score_indices),
            "posts_ignored": ignored_count,
            "selection_rate": f"{(len(high_score_indices) / len(filtered) * 100):.1f}%" if filtered else "0%",
            "llm_calls": 1
        })

        # ===== STEP 8: Generate Rewrite Strategies (BATCHED, 1 LLM call) =====
        _log_step(task, 8, "Generating rewrite strategies", llm)
        logger.info(f"[WORKFLOW] Step 8: Batch-generating strategies for {len(high_score_indices)} posts")

        strategy_items = []
        for idx in high_score_indices:
            post = filtered[idx]
            scores = next((s for s in post_scores if s.get("post_index") == idx), {})
            strategy_items.append({
                "post_id": post.get("id"),
                "post_index": idx,
                "title": post.get("title", ""),
                "body": post.get("body", ""),
                "virality_score": scores.get("virality_score", 0),
                "fit_score": scores.get("fit_score", 0),
            })

        post_strategies = []
        if strategy_items:
            try:
                batch = await llm.generate_post_strategies_batch(strategy_items, user_context)
            except Exception as e:
                logger.error(f"[WORKFLOW] Batch strategy generation failed: {e}")
                task.error_log.append(f"Strategy batch failed: {e}")
                batch = [{"post_id": it["post_id"], "strategy": ""} for it in strategy_items]
            # Re-attach post_index since the LLM doesn't see it
            for it, b in zip(strategy_items, batch):
                post_strategies.append({
                    "post_id": it["post_id"],
                    "post_index": it["post_index"],
                    "strategy": b.get("strategy", ""),
                })
        task.post_strategies = post_strategies

        log_workflow_event("post_strategy_result", {
            "strategies_generated": len(post_strategies),
            "llm_calls": 1 if strategy_items else 0
        })

        # ===== STEP 9: Validate Post Strategies (BATCHED, 1 LLM call) =====
        _log_step(task, 9, "Validating rewrite strategies", llm)
        logger.info(f"[WORKFLOW] Step 9: Batch-validating {len(post_strategies)} strategies")

        v_items = []
        for ls in post_strategies:
            if ls["post_index"] >= len(filtered):
                continue
            post = filtered[ls["post_index"]]
            scores = next((s for s in post_scores if s.get("post_index") == ls["post_index"]), {})
            v_items.append({
                "post_id": ls["post_id"],
                "title": post.get("title", ""),
                "virality_score": scores.get("virality_score", 0),
                "fit_score": scores.get("fit_score", 0),
                "strategy": ls["strategy"],
            })

        post_validations = []
        if v_items:
            try:
                post_validations = await llm.validate_posts_batch(v_items, user_context, product_context)
            except Exception as e:
                logger.error(f"[WORKFLOW] Batch post validation failed: {e}")
                task.error_log.append(f"Post validation batch failed: {e}")
                err = {"tag": "ERROR", "reasoning": str(e)[:200]}
                post_validations = [{"post_id": it["post_id"], "validation": err} for it in v_items]
        task.post_validations = post_validations

        post_pass = sum(1 for lv in post_validations if lv["validation"].get("tag", "").upper() == "PASS")
        post_unsure = sum(1 for lv in post_validations if lv["validation"].get("tag", "").upper() == "UNSURE")
        log_workflow_event("post_validation_result", {
            "strategies_validated": len(post_validations),
            "pass_count": post_pass,
            "unsure_count": post_unsure,
            "fail_count": len(post_validations) - post_pass - post_unsure,
            "llm_calls": 1 if v_items else 0
        })

        # ===== STEP 10: Store Results + Memory Bank =====
        _log_step(task, 10, "Storing results", llm)
        logger.info("[WORKFLOW] Step 10: All data stored in task")
        try:
            saved = _collect_memory_bank(task)
            if saved:
                logger.info(f"[WORKFLOW] Memory Bank: archived {saved} new PASS/UNSURE posts")
        except Exception as e:
            logger.error(f"[WORKFLOW] Memory Bank archive failed (non-fatal): {e}")
            task.error_log.append(f"Memory Bank archive failed: {e}")

        # Back-fill validation_tag on the promotional archive once both validation steps are complete.
        # PASS > UNSURE > FAIL precedence across the comment-validation and post-validation gates.
        try:
            updated = _backfill_promo_validation_tags(task)
            if updated:
                logger.info(f"[WORKFLOW] Promotional archive: back-filled validation_tag on {updated} posts")
        except Exception as e:
            logger.error(f"[WORKFLOW] Promo tag back-fill failed (non-fatal): {e}")
            task.error_log.append(f"Promotional tag back-fill failed: {e}")

        # ===== STEP 11: Mark Complete =====
        _log_step(task, 11, "Complete", llm)
        task.status = "complete"
        storage.persist(task_id)
        logger.info(f"[WORKFLOW] Step 11: Workflow complete for task {task_id}")

        total_llm_calls = (
            1 +  # step 4
            len(yes_posts) +  # step 5 (parallel but still N calls)
            (1 if generated_comments else 0) +  # step 6 batched
            1 +  # step 7
            (1 if strategy_items else 0) +  # step 8 batched
            (1 if v_items else 0)  # step 9 batched
        )
        log_workflow_event("workflow_summary", {
            "task_id": task_id,
            "total_posts_fetched": len(all_posts),
            "posts_after_filter": len(filtered),
            "posts_selected_for_comments": len(yes_posts),
            "posts_rejected": len(filtered) - len(yes_posts),
            "comments_generated": len(generated_comments) * 2,
            "posts_qualifying_for_repurpose": len(high_score_indices),
            "post_strategies_generated": len(post_strategies),
            "total_llm_calls": total_llm_calls,
            "errors_count": len(task.error_log)
        })

    except Exception as e:
        logger.error(f"[WORKFLOW] Critical error in workflow: {e}")
        task.status = "failed"
        task.error_log.append(f"Critical workflow error: {e}")
        storage.persist(task_id)


def _log_step(task: TaskData, step: int, description: str, llm: "LLMClient | None" = None) -> None:
    """Log step timestamp, update progress, snapshot llm.call_log into task, and persist.
    BACKWARD-COMPAT INVARIANT: `llm` was added as a trailing optional kwarg with default None,
    so any pre-existing 3-arg call site still works (the snapshot block is simply skipped).
    """
    task.step_timestamps[f"step_{step}"] = datetime.utcnow().isoformat()
    task.progress = {"step": step, "description": description}
    if llm is not None:
        # Snapshot per-call debug records so the Prompt Debugger UI sees them progressively
        task.llm_calls = list(llm.call_log)
    storage.persist(task.task_id)


def _collect_memory_bank(task: TaskData) -> int:
    """
    Walk validation results and archive every post that earned a PASS or UNSURE tag from
    EITHER the comment-validation gate (step 6) OR the post-validation gate (step 9).
    Persists into memory_posts (idempotent on post_id) and bumps memory_subreddits.
    Returns count of newly-inserted rows.
    """
    # Build {post_id -> {best_tag, gates}} where best_tag is PASS > UNSURE
    qualifying: dict[str, dict] = {}

    def _bump(pid: str, tag: str, gate: str) -> None:
        tag_u = tag.upper()
        if tag_u not in ("PASS", "UNSURE"):
            return
        cur = qualifying.get(pid)
        if cur is None:
            qualifying[pid] = {"best_tag": tag_u, "gates": {gate}}
            return
        # PASS beats UNSURE
        if cur["best_tag"] == "UNSURE" and tag_u == "PASS":
            cur["best_tag"] = "PASS"
        cur["gates"].add(gate)

    for cv in task.comment_validations or []:
        pid = cv.get("post_id")
        if not pid:
            continue
        for v in cv.get("validations") or []:
            _bump(pid, v.get("tag", ""), "comment")

    for pv in task.post_validations or []:
        pid = pv.get("post_id")
        if not pid:
            continue
        _bump(pid, (pv.get("validation") or {}).get("tag", ""), "post")

    if not qualifying:
        return 0

    # Index summaries by post_id from comment_evaluations
    summaries: dict[str, str] = {}
    for ev in task.comment_evaluations or []:
        pid = ev.get("post_id")
        if pid and ev.get("summary"):
            summaries[pid] = ev["summary"]

    # Look up canonical post records from filtered_posts
    posts_by_id = {p.get("id"): p for p in (task.filtered_posts or []) if p.get("id")}

    rows: list[dict] = []
    for pid, meta in qualifying.items():
        post = posts_by_id.get(pid)
        if not post:
            continue
        gates = meta["gates"]
        gate_label = "both" if len(gates) > 1 else next(iter(gates))
        body = post.get("body") or ""
        summary = summaries.get(pid) or (body[:150] + ("..." if len(body) > 150 else "")) or None
        # Emit one row per subreddit-source so cross-posted content gets credited to every subreddit
        # it appeared in. Falls back to the post's primary subreddit if sources weren't attached.
        sources = post.get("subreddit_sources") or [{
            "subreddit": post.get("subreddit") or "",
            "subreddit_subscribers": post.get("subreddit_subscribers", 0),
            "permalink": post.get("url") or "",
        }]
        for src in sources:
            rows.append({
                "post_id": pid,
                "subreddit": src.get("subreddit") or "",
                "subreddit_subscribers": src.get("subreddit_subscribers") or 0,
                "permalink": src.get("permalink") or post.get("url") or "",
                "title": post.get("title") or "",
                "flair": post.get("flair"),
                "summary": summary,
                "upvotes": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "created_utc": post.get("created_utc"),
                "tag": meta["best_tag"].lower(),
                "qualifying_gate": gate_label,
                "source_task_id": task.task_id,
            })

    return storage.save_memory_posts(rows, source_input_type=task.input_type)


def _build_promo_rows(detections: list[dict], all_posts: list[dict], task_id: str) -> list[dict]:
    """Shape Step 2.5 detections + canonical post records into rows for storage.save_promotional_posts.
    body_excerpt is the first ~3 lines (or 400 chars, whichever is shorter) so the dashboard can
    render a quick preview without exposing the full body.
    """
    posts_by_id = {p.get("id"): p for p in all_posts if p.get("id")}
    rows: list[dict] = []
    for d in detections:
        pid = d.get("post_id")
        post = posts_by_id.get(pid)
        if not post:
            continue
        body = post.get("body") or ""
        # Take first 3 non-empty lines, capped at 400 chars total
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()][:3]
        excerpt = "\n".join(lines)[:400]
        rows.append({
            "post_id": pid,
            "title": post.get("title") or "",
            "body_excerpt": excerpt,
            "permalink": post.get("url") or "",
            "primary_subreddit": post.get("subreddit") or "",
            "subreddit_sources": post.get("subreddit_sources") or [],
            "author": post.get("author"),
            "flair": post.get("flair"),
            "upvotes": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
            "created_utc": post.get("created_utc"),
            "promo_type": d.get("promo_type") or "none",
            "promo_reasoning": d.get("reasoning") or "",
            "validation_tag": None,  # filled in by _backfill_promo_validation_tags after Step 9
            "source_task_id": task_id,
        })
    return rows


def _backfill_promo_validation_tags(task: TaskData) -> int:
    """For every promo-flagged post that also has a validation verdict, push the BEST tag
    (PASS > UNSURE > FAIL) into promotional_posts.validation_tag. Returns count of rows updated.
    """
    promo_ids = {d["post_id"] for d in (task.promotional_detections or []) if d.get("is_promotional")}
    if not promo_ids:
        return 0

    def _rank(t: str) -> int:
        return {"pass": 3, "unsure": 2, "fail": 1}.get(t.lower(), 0)

    best: dict[str, str] = {}
    for cv in task.comment_validations or []:
        pid = cv.get("post_id")
        if not isinstance(pid, str) or pid not in promo_ids:
            continue
        for v in cv.get("validations") or []:
            tag = (v.get("tag") or "").lower()
            if tag in ("pass", "unsure", "fail") and _rank(tag) > _rank(best.get(pid, "")):
                best[pid] = tag
    for pv in task.post_validations or []:
        pid = pv.get("post_id")
        if not isinstance(pid, str) or pid not in promo_ids:
            continue
        tag = ((pv.get("validation") or {}).get("tag") or "").lower()
        if tag in ("pass", "unsure", "fail") and _rank(tag) > _rank(best.get(pid, "")):
            best[pid] = tag

    updated = 0
    for pid, tag in best.items():
        if storage.update_promotional_validation(pid, tag):
            updated += 1
    return updated
