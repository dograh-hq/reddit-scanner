"""
Bedrock LLM client - Claude Opus 4.7 via AWS Bedrock Converse API.
All workflow LLM calls (evaluation, generation, batched validation/scoring/strategy) go through here.
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import httpx

from api_logger import log_llm_call

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Bedrock Converse API endpoint - cross-region inference profile for Opus 4.7
BEDROCK_REGION = "us-east-1"
BEDROCK_MODEL_ID = "us.anthropic.claude-opus-4-7"
BEDROCK_URL = f"https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com/model/{BEDROCK_MODEL_ID}/converse"

# Cap concurrent Bedrock calls so step 5 fan-out doesn't trip rate limits
CONCURRENCY = 5


class LLMClient:
    """Claude Opus 4.7 client. Wraps Bedrock Converse with token logging + JSON parsing."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = BEDROCK_MODEL_ID
        # Single semaphore shared across all calls from one workflow run
        self.sem = asyncio.Semaphore(CONCURRENCY)
        self.timeout = httpx.Timeout(300.0)  # 5 min - Opus reasoning can be slow
        # Per-instance debug log of every prompt/response, in finish order. Workflow snapshots this
        # into task.llm_calls at every step boundary so the Prompt Debugger UI can render it.
        # NOTE: `_seq` read/modify/write is NOT atomic across `asyncio.gather` await points — but
        # `_call_llm` only mutates it after `await`s complete inside a single event-loop tick (no
        # interleaving), so under asyncio (single-threaded) parallel calls still get unique seq values.
        self.call_log: list[dict] = []
        self._seq = 0

    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file."""
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text()
        logger.warning(f"[LLM] Prompt file not found: {filename}")
        return ""

    async def _call_llm(self, prompt: str, call_type: str = "unknown",
                        step_name: str = "Unknown",
                        group_id: str | None = None) -> str:
        """Bedrock Converse API call with bearer auth. Logs tokens, raises on HTTP error.
        `step_name` and `group_id` populate the per-instance call_log so the Prompt Debugger
        UI can group calls by workflow step and parallel-fan-out group.
        BACKWARD-COMPAT INVARIANT: `step_name` and `group_id` are appended AFTER the existing
        positional args and have safe defaults. All in-tree callers pass them as kwargs, so
        no existing call site breaks.
        """
        # 32K output tokens — Opus 4.7 supports up to 128K, but 32K is comfortably above
        # our worst-case batch size (5 keywords × 20 posts × ~200 tok/entry ≈ 20K) without
        # being wasteful. Without an explicit cap, Bedrock applies the model default (~4K)
        # and large batches silently truncate mid-array, causing parse failures and post drops.
        payload = {
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ],
            "inferenceConfig": {"maxTokens": 32000}
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        started_at = datetime.utcnow().isoformat()
        async with self.sem:
            try:
                # httpx async client - non-blocking HTTP
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # POST to Bedrock Converse endpoint
                    r = await client.post(BEDROCK_URL, json=payload, headers=headers)
                    r.raise_for_status()  # raise on 4xx/5xx
                    data = r.json()  # parse JSON body

                # Converse response: output.message.content is a list of blocks
                content_blocks = data["output"]["message"]["content"]
                content = "".join(b.get("text", "") for b in content_blocks)

                usage = data.get("usage", {})
                input_tokens = usage.get("inputTokens", 0)
                output_tokens = usage.get("outputTokens", 0)
                total_tokens = usage.get("totalTokens", input_tokens + output_tokens)

                log_llm_call(
                    call_type=call_type,
                    prompt_length=len(prompt),
                    response_length=len(content),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    model=self.model,
                    success=True,
                    result_summary=content[:100],
                )
                logger.info(f"[LLM] {call_type}: {input_tokens} in / {output_tokens} out / {total_tokens} total tokens")
                # Append debug record (full prompt + response) for the Prompt Debugger
                self.call_log.append({
                    "seq": self._seq, "call_type": call_type, "step_name": step_name,
                    "group_id": group_id, "prompt": prompt, "response": content,
                    "input_tokens": input_tokens, "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "started_at": started_at, "finished_at": datetime.utcnow().isoformat(),
                    "success": True, "error": None,
                })
                self._seq += 1
                return content
            except Exception as e:
                log_llm_call(
                    call_type=call_type,
                    prompt_length=len(prompt),
                    response_length=0,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    model=self.model,
                    success=False,
                    error=str(e),
                )
                logger.error(f"[LLM] API call failed ({call_type}): {e}")
                # Capture failed call too so the debugger shows what was sent
                self.call_log.append({
                    "seq": self._seq, "call_type": call_type, "step_name": step_name,
                    "group_id": group_id, "prompt": prompt, "response": "",
                    "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                    "started_at": started_at, "finished_at": datetime.utcnow().isoformat(),
                    "success": False, "error": str(e),
                })
                self._seq += 1
                raise

    def _parse_json_response(self, response: str, context: str = "") -> dict | list | str:
        """Parse JSON from LLM response. Returns raw string on failure (caller handles fallback).
        Tolerates: ```json fences, bare ``` fences, leading/trailing prose, and the raw response.
        """
        candidates: list[str] = []
        # 1) ```json … ```
        if "```json" in response:
            try:
                candidates.append(response.split("```json", 1)[1].split("```", 1)[0])
            except IndexError:
                pass
        # 2) bare ``` … ``` (no language tag)
        if "```" in response:
            try:
                candidates.append(response.split("```", 1)[1].split("```", 1)[0])
            except IndexError:
                pass
        # 3) raw response
        candidates.append(response)
        # 4) prose-prefixed: slice from the first { or [ to the matching last } or ]
        for opener, closer in (("{", "}"), ("[", "]")):
            i, j = response.find(opener), response.rfind(closer)
            if 0 <= i < j:
                candidates.append(response[i:j + 1])

        for c in candidates:
            try:
                return json.loads(c.strip())
            except (json.JSONDecodeError, ValueError):
                continue

        logger.error(f"[LLM] Invalid JSON in {context}. Pushing raw text forward.")
        return response

    # ----- Step 2.5: batched promotional / launch detection -----
    async def detect_promotional_posts_batch(self, posts: list[dict]) -> list[dict]:
        """One call: tag each canonical post with promo_type.
        Returns [{post_id, is_promotional, promo_type, reasoning}] aligned to input via post_id.
        Posts the LLM omits or hallucinates are silently skipped (not promo by default).
        """
        if not posts:
            return []
        template = self._load_prompt("promotional_detection.txt")
        # Show first 800 chars of body — promo signals usually surface in the opening lines
        # (links, "I built", project names) and we don't want to balloon prompt size for 35+ posts.
        posts_text = "\n\n".join([
            f"Post (post_id={p.get('id')}):\nTitle: {p.get('title', '')}\n"
            f"Body: {(p.get('body') or '')[:800]}\n"
            f"Subreddit: r/{p.get('subreddit', '')}\nAuthor: {p.get('author', '')}\n"
            f"Flair: {p.get('flair', 'None')}"
            for p in posts
        ])
        prompt = template.replace("<LIST_OF_POSTS>", posts_text)
        response = await self._call_llm(prompt, call_type="promotional_detection",
                                        step_name="Step 2.5: Promotional Detection")
        result = self._parse_json_response(response, "promotional_detection")

        if not isinstance(result, list):
            return []
        valid_ids = {p.get("id") for p in posts}
        out: list[dict] = []
        for entry in result:
            if not isinstance(entry, dict):
                continue
            pid = entry.get("post_id")
            if pid not in valid_ids:
                logger.warning(f"[LLM] promotional_detection: unknown post_id={pid!r}; skipping")
                continue
            out.append({
                "post_id": pid,
                "is_promotional": bool(entry.get("is_promotional", False)),
                "promo_type": str(entry.get("promo_type") or "none"),
                "reasoning": str(entry.get("reasoning") or "")[:500],
            })
        return out

    # ----- Step 4: batched comment evaluation -----
    async def evaluate_posts_for_comments(self, posts: list[dict], user_context: str,
                                          product_context: str = "") -> list[dict]:
        """One call: decide YES/NO per post.
        Returns [{post_index, post_id, summary, decision, reasoning}] aligned to input posts via post_id.
        """
        template = self._load_prompt("comment_evaluation.txt")
        # Display each post with its stable post_id so the LLM can echo it back unambiguously
        posts_text = "\n\n".join([
            f"Post (post_id={p.get('id')}):\nTitle: {p.get('title', '')}\nBody: {p.get('body', '')[:500]}...\n"
            f"Subreddit: r/{p.get('subreddit', '')}\nUpvotes: {p.get('score', 0)}\n"
            f"Comments: {p.get('num_comments', 0)}\nFlair: {p.get('flair', 'None')}"
            for p in posts
        ])
        prompt = (template
                  .replace("<USER_CONTEXT>", user_context)
                  .replace("<PRODUCT_CONTEXT>", product_context)
                  .replace("<LIST_OF_POSTS>", posts_text))
        response = await self._call_llm(prompt, call_type="comment_evaluation",
                                        step_name="Step 4: Comment Evaluation")
        result = self._parse_json_response(response, "comment_evaluation")

        if isinstance(result, str):
            return [{"post_index": i, "post_id": p.get("id"), "decision": "ERROR", "reasoning": result}
                    for i, p in enumerate(posts)]
        if not isinstance(result, list):
            result = [result]
        # Re-attach correct post_index by looking up post_id in input posts (authoritative)
        id_to_index = {p.get("id"): i for i, p in enumerate(posts)}
        normalized = []
        for entry in result:
            if not isinstance(entry, dict):
                continue
            pid = entry.get("post_id")
            idx = id_to_index.get(pid)
            if idx is None:
                # LLM hallucinated or omitted post_id — drop with a warning
                logger.warning(f"[LLM] comment_evaluation entry has unknown post_id={pid!r}; skipping")
                continue
            entry["post_index"] = idx
            entry["post_id"] = pid
            normalized.append(entry)
        return normalized

    # ----- Step 5: per-post comment generation (called in parallel by workflow) -----
    async def generate_comments(self, post: dict, user_context: str,
                                _debug_group_id: str | None = None) -> list[str]:
        """Generate 2 comment suggestions for a single post.
        `_debug_group_id` is forwarded to `_call_llm` so the Prompt Debugger groups
        all parallel Step 5 calls under one expandable accordion."""
        template = self._load_prompt("comment_generation.txt")
        prompt = template.replace("<TITLE>", post.get("title", ""))
        prompt = prompt.replace("<BODY>", post.get("body", "")[:1500])
        prompt = prompt.replace("<SUBREDDIT>", post.get("subreddit", ""))
        prompt = prompt.replace("<SCORE>", str(post.get("score", 0)))
        prompt = prompt.replace("<NUM_COMMENTS>", str(post.get("num_comments", 0)))
        prompt = prompt.replace("<USER_CONTEXT>", user_context)

        response = await self._call_llm(prompt, call_type="comment_generation",
                                        step_name="Step 5: Comment Generation (parallel)",
                                        group_id=_debug_group_id)
        result = self._parse_json_response(response, "comment_generation")

        # LLM sometimes wraps the dict in an array: [{"comments": [...]}]
        if isinstance(result, list):
            if result and isinstance(result[0], dict) and "comments" in result[0]:
                return [c for c in result[0]["comments"][:2] if isinstance(c, str)]
            return [c for c in result[:2] if isinstance(c, str)]
        if isinstance(result, dict) and "comments" in result:
            return [c for c in result["comments"][:2] if isinstance(c, str)]
        if isinstance(result, str):
            # JSON parse failed entirely. Try a regex salvage on the raw text:
            # pull the longest 2 quoted strings inside the `"comments": [...]` array.
            # This rescues the screenshot scenario where the JSON wrapper was malformed
            # but the comment values themselves were intact.
            #
            # Two-stage scoping so we never fall back to "match any quoted string in the
            # whole response" — that would pick up stray field labels or echoed prompt text.
            m_closed = re.search(r'"comments"\s*:\s*\[(.*?)\]', result, re.DOTALL)
            m_open = re.search(r'"comments"\s*:\s*\[(.*)', result, re.DOTALL)  # truncation: missing ]
            block = m_closed.group(1) if m_closed else (m_open.group(1) if m_open else None)
            decoded: list[str] = []
            if block:
                quoted = re.findall(r'"((?:[^"\\]|\\.)*)"', block)
                for s in quoted:
                    # Convert JSON-style escapes (\n \" \\ etc.) back to real characters
                    try:
                        decoded.append(json.loads(f'"{s}"'))
                    except json.JSONDecodeError:
                        decoded.append(s)
                decoded.sort(key=len, reverse=True)
            top2 = decoded[:2]
            if top2:
                return [top2[0], top2[1] if len(top2) > 1 else ""]
            # Last-ditch: the legacy `---` separator path
            if "---" in result:
                return result.split("---")[:2]
            # Truly nothing salvageable — surface a short error instead of dumping the whole blob
            logger.error(f"[LLM] generate_comments: could not salvage from raw response (len={len(result)})")
            return ["[LLM output could not be parsed — see Prompt Debugger panel]", ""]
        return ["", ""]

    # ----- Step 6: batched comment validation -----
    async def validate_comments_batch(self, items: list[dict], user_context: str,
                                      product_context: str = "") -> list[dict]:
        """
        items: [{post_id, title, body, upvotes, comments: [c1, c2]}]
        Returns: [{post_id, validations: [{score/total_score, tag, reasoning}, ...]}]
        """
        if not items:
            return []
        template = self._load_prompt("comment_validation.txt")
        items_text = "\n\n".join([
            f"Item {i+1} (post_id={it['post_id']}):\n"
            f"Title: {it['title']}\nBody snippet: {it['body'][:500]}\n"
            f"Upvotes: {it['upvotes']}\n"
            f"Comment A: {it['comments'][0] if len(it['comments']) > 0 else ''}\n"
            f"Comment B: {it['comments'][1] if len(it['comments']) > 1 else ''}"
            for i, it in enumerate(items)
        ])
        prompt = (template
                  .replace("<USER_CONTEXT>", user_context)
                  .replace("<PRODUCT_CONTEXT>", product_context)
                  .replace("<ITEMS>", items_text))
        response = await self._call_llm(prompt, call_type="comment_validation",
                                        step_name="Step 6: Comment Validation (batched)")
        result = self._parse_json_response(response, "comment_validation")

        # Fallback if batch returns non-list
        if not isinstance(result, list):
            err = {"score": 0, "tag": "ERROR", "reasoning": str(result)[:200]}
            return [{"post_id": it["post_id"], "validations": [err, err]} for it in items]

        # Map results back by post_id (authoritative); position is unreliable across LLM reorderings
        by_id = {r.get("post_id"): r for r in result if isinstance(r, dict)}
        output = []
        for it in items:
            r = by_id.get(it["post_id"])
            validations = r.get("validations") if isinstance(r, dict) else None
            if isinstance(validations, list):
                output.append({"post_id": it["post_id"], "validations": validations})
            else:
                err = {"score": 0, "tag": "ERROR",
                       "reasoning": "Missing in batch response" if r is None else str(r)[:200]}
                output.append({"post_id": it["post_id"], "validations": [err, err]})
        return output

    # ----- Step 7: batched post scoring (Reddit + LinkedIn fit) -----
    async def score_posts(self, posts: list[dict], user_context: str,
                          product_context: str = "") -> list[dict]:
        """One call: virality + fit + SELECT/IGNORE for each post.
        Returns [{post_index, post_id, virality_score, fit_score, decision, reasoning}] aligned via post_id.
        """
        template = self._load_prompt("post_scoring.txt")
        # Display each post with its stable post_id so the LLM can echo it back unambiguously
        posts_text = "\n\n".join([
            f"Post (post_id={p.get('id')}):\nTitle: {p.get('title', '')}\nBody: {p.get('body', '')[:500]}...\n"
            f"Upvotes: {p.get('score', 0)}\nComments: {p.get('num_comments', 0)}"
            for p in posts
        ])
        prompt = (template
                  .replace("<USER_CONTEXT>", user_context)
                  .replace("<PRODUCT_CONTEXT>", product_context)
                  .replace("<LIST_OF_POSTS>", posts_text))
        response = await self._call_llm(prompt, call_type="post_scoring",
                                        step_name="Step 7: Post Scoring (Reddit + LinkedIn fit)")
        result = self._parse_json_response(response, "post_scoring")

        if isinstance(result, str):
            return [{"post_index": i, "post_id": p.get("id"), "virality_score": 0, "fit_score": 0, "reasoning": result}
                    for i, p in enumerate(posts)]
        if not isinstance(result, list):
            result = [result]
        # Re-attach correct post_index by looking up post_id in input posts (authoritative)
        id_to_index = {p.get("id"): i for i, p in enumerate(posts)}
        normalized = []
        for entry in result:
            if not isinstance(entry, dict):
                continue
            pid = entry.get("post_id")
            idx = id_to_index.get(pid)
            if idx is None:
                logger.warning(f"[LLM] post_scoring entry has unknown post_id={pid!r}; skipping")
                continue
            entry["post_index"] = idx
            entry["post_id"] = pid
            normalized.append(entry)
        return normalized

    # ----- Step 8: batched rewrite strategies -----
    async def generate_post_strategies_batch(self, items: list[dict], user_context: str) -> list[dict]:
        """
        items: [{post_id, title, body, virality_score, fit_score}]
        Returns: [{post_id, strategy: str}]
        """
        if not items:
            return []
        template = self._load_prompt("post_rewrite.txt")
        items_text = "\n\n".join([
            f"Item {i+1} (post_id={it['post_id']}):\n"
            f"Title: {it['title']}\nContent: {it['body'][:1500]}\n"
            f"Virality: {it['virality_score']}/10\nFit: {it['fit_score']}/10"
            for i, it in enumerate(items)
        ])
        prompt = template.replace("<USER_CONTEXT>", user_context).replace("<ITEMS>", items_text)
        response = await self._call_llm(prompt, call_type="post_strategy",
                                        step_name="Step 8: Post Strategy (batched)")
        result = self._parse_json_response(response, "post_strategy")

        if not isinstance(result, list):
            fallback = str(result)[:500] if isinstance(result, str) else ""
            return [{"post_id": it["post_id"], "strategy": fallback} for it in items]

        # Map results back by post_id (authoritative); position is unreliable across LLM reorderings
        by_id = {r.get("post_id"): r for r in result if isinstance(r, dict)}
        output = []
        for it in items:
            r = by_id.get(it["post_id"])
            if isinstance(r, dict) and "strategy" in r:
                output.append({"post_id": it["post_id"], "strategy": r["strategy"]})
            else:
                output.append({"post_id": it["post_id"], "strategy": ""})
        return output

    # ----- Step 9: batched post strategy validation -----
    async def validate_posts_batch(self, items: list[dict], user_context: str,
                                   product_context: str = "") -> list[dict]:
        """
        items: [{post_id, title, virality_score, fit_score, strategy}]
        Returns: [{post_id, validation: {tag, reasoning}}]
        """
        if not items:
            return []
        template = self._load_prompt("post_validation.txt")
        items_text = "\n\n".join([
            f"Item {i+1} (post_id={it['post_id']}):\n"
            f"Title: {it['title']}\nVirality: {it['virality_score']}/10\nFit: {it['fit_score']}/10\n"
            f"Strategy: {it['strategy']}"
            for i, it in enumerate(items)
        ])
        prompt = (template
                  .replace("<USER_CONTEXT>", user_context)
                  .replace("<PRODUCT_CONTEXT>", product_context)
                  .replace("<ITEMS>", items_text))
        response = await self._call_llm(prompt, call_type="post_validation",
                                        step_name="Step 9: Post Validation (batched)")
        result = self._parse_json_response(response, "post_validation")

        if not isinstance(result, list):
            err = {"tag": "ERROR", "reasoning": str(result)[:200]}
            return [{"post_id": it["post_id"], "validation": err} for it in items]

        # Map results back by post_id (authoritative); position is unreliable across LLM reorderings
        by_id = {r.get("post_id"): r for r in result if isinstance(r, dict)}
        output = []
        for it in items:
            r = by_id.get(it["post_id"])
            if isinstance(r, dict):
                output.append({"post_id": it["post_id"], "validation": {
                    "tag": r.get("tag", "ERROR"),
                    "reasoning": r.get("reasoning", ""),
                }})
            else:
                output.append({"post_id": it["post_id"], "validation": {"tag": "ERROR", "reasoning": "Missing in batch response"}})
        return output
