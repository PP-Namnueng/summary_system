"""Lightweight runtime retrieval gate checks.

These checks are deterministic and safe for the user-facing request path. They
do not call RAGAS, DeepEval, or any LLM judge.
"""

from __future__ import annotations

import re
from typing import Any


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _context_text(context: dict[str, Any] | str) -> str:
    if isinstance(context, str):
        return context
    return str(context.get("text") or context.get("content") or "")


def _score(context: dict[str, Any] | str) -> float | None:
    if not isinstance(context, dict):
        return None
    score_type = context.get("score_type")
    if score_type in {"hybrid_rrf", "keyword_bm25"}:
        return _as_float(context.get("vector_score"))
    return _as_float(context.get("score"))


def _duplicate_ratio(contexts: list[dict[str, Any] | str]) -> float:
    if not contexts:
        return 0.0

    fingerprints = []
    for context in contexts:
        text = re.sub(r"\s+", " ", _context_text(context).strip().lower())
        fingerprints.append(text[:500])

    unique_count = len(set(fingerprints))
    return 1.0 - (unique_count / len(fingerprints))


def evaluate_retrieval_gate(
    query: str,
    contexts: list[dict[str, Any] | str],
    rag_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return pass/fail and cheap retrieval metrics for runtime policy."""
    rag_config = rag_config or {}
    usable_contexts = [context for context in contexts if _context_text(context).strip()]
    scores = [_score(context) for context in usable_contexts]
    numeric_scores = [score for score in scores if score is not None]

    top_similarity = max(numeric_scores) if numeric_scores else None
    avg_similarity = (
        sum(numeric_scores) / len(numeric_scores) if numeric_scores else None
    )
    duplicate_ratio = _duplicate_ratio(usable_contexts)

    min_context_count = int(rag_config.get("min_context_count", 1) or 0)
    min_top_similarity = rag_config.get(
        "min_top_similarity", rag_config.get("min_similarity")
    )
    min_avg_similarity = rag_config.get("min_avg_similarity")
    max_duplicate_ratio = rag_config.get("max_duplicate_ratio")

    failures: list[str] = []
    if len(usable_contexts) < min_context_count:
        failures.append("min_context_count")

    min_top = _as_float(min_top_similarity)
    if min_top is not None:
        if top_similarity is None or top_similarity < min_top:
            failures.append("min_top_similarity")

    min_avg = _as_float(min_avg_similarity)
    if min_avg is not None:
        if avg_similarity is None or avg_similarity < min_avg:
            failures.append("min_avg_similarity")

    max_dup = _as_float(max_duplicate_ratio)
    if max_dup is not None and duplicate_ratio > max_dup:
        failures.append("max_duplicate_ratio")

    passed = not failures
    reason = "passed" if passed else ", ".join(failures)

    return {
        "passed": passed,
        "reason": reason,
        "failures": failures,
        "metrics": {
            "context_count": len(usable_contexts),
            "top_similarity": top_similarity,
            "avg_similarity": avg_similarity,
            "duplicate_ratio": duplicate_ratio,
        },
        "query": query,
    }
