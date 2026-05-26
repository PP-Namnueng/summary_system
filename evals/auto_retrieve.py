"""Deterministic Retry Retrieve strategies for runtime retrieval failures."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .retrieval_gate import evaluate_retrieval_gate

try:
    from summary.library.reranker import rerank_contexts
except ImportError:
    from library.reranker import rerank_contexts

try:
    from summary.library.hybrid_retriever import HybridRetriever
except ImportError:
    from library.hybrid_retriever import HybridRetriever


Retriever = Callable[[str, int], list[dict[str, Any]]]


def _rag_config_from_app_config(app_config: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    app_config = app_config or {}
    rag_config = dict(app_config.get("rag", {}))
    max_attempts_source = "rag.max_attempts"

    if "max_attempts" not in rag_config:
        rag_config["max_attempts"] = (
            app_config.get("eval", {})
            .get("behavior", {})
            .get("max_retrieve_attempts", 1)
        )
        max_attempts_source = "eval.behavior.max_retrieve_attempts"

    fail_mode = app_config.get("eval", {}).get("behavior", {}).get("fail_mode")
    if fail_mode == "block":
        rag_config["enable_auto_retrieve"] = False
    elif fail_mode == "retry":
        rag_config["enable_auto_retrieve"] = True

    return rag_config, max_attempts_source


def retrieve_with_gate_retry(
    query: str,
    vector_store: Any,
    app_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retrieve contexts, run the runtime gate, and retry deterministically.

    This helper is intentionally runtime-only and deterministic. It does not
    import or call RAGAS, DeepEval, query rewrite, or any LLM judge.
    """
    rag_config, max_attempts_source = _rag_config_from_app_config(app_config)
    top_k = int(rag_config.get("top_k", 5) or 5)
    retriever = _build_runtime_retriever(vector_store, rag_config)

    initial_contexts = retriever.search(query, top_k=top_k)
    trace = retry_retrieve(
        query=query,
        initial_contexts=initial_contexts,
        retriever=lambda retry_query, retry_top_k: retriever.search(
            retry_query,
            top_k=retry_top_k,
        ),
        rag_config=rag_config,
    )
    trace["max_attempts_source"] = max_attempts_source
    trace["initial_top_k"] = top_k
    trace["retrieval"] = _retrieval_metadata(retriever, rag_config)
    _apply_optional_reranker(query, trace, rag_config)
    return trace


def _build_runtime_retriever(vector_store: Any, rag_config: dict[str, Any]) -> Any:
    hybrid_config = rag_config.get("hybrid_search") or {}
    if hybrid_config.get("enabled", False):
        return HybridRetriever(vector_store=vector_store, rag_config=rag_config)
    return vector_store


def _retrieval_metadata(retriever: Any, rag_config: dict[str, Any]) -> dict[str, Any]:
    if isinstance(retriever, HybridRetriever):
        return dict(getattr(retriever, "last_trace", {}) or {"retriever": "hybrid"})
    return {
        "retriever": "vector",
        "keyword_enabled": False,
        "hybrid_enabled": False,
    }


def retry_retrieve(
    query: str,
    initial_contexts: list[dict[str, Any]],
    retriever: Retriever,
    rag_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retry retrieval using configured deterministic strategies.

    The first implementation intentionally supports only `increase_top_k`.
    Query rewrite remains disabled unless future code explicitly implements it.
    """
    rag_config = rag_config or {}
    initial_top_k = int(rag_config.get("top_k", 5) or 5)
    gate_result = evaluate_retrieval_gate(query, initial_contexts, rag_config)
    trace = {
        "original_query": query,
        "final_query": query,
        "retrieved_contexts": initial_contexts,
        "gate_result": gate_result,
        "retry_attempts": [],
        "selected_strategy": None,
        "pass_fail_reason": gate_result["reason"],
        "final_top_k": initial_top_k,
        "retry_exhausted": False,
    }

    if gate_result["passed"] or not rag_config.get("enable_auto_retrieve", False):
        return trace

    strategies = rag_config.get("retry_strategies") or ["increase_top_k"]
    if "increase_top_k" not in strategies:
        return trace

    strategy_config = rag_config.get("increase_top_k", {})
    max_attempts = int(rag_config.get("max_attempts") or 1)
    increment = int(strategy_config.get("increment", initial_top_k) or initial_top_k)
    max_top_k = int(strategy_config.get("max_top_k", initial_top_k + increment) or 0)
    current_top_k = initial_top_k

    for attempt_number in range(1, max_attempts + 1):
        next_top_k = current_top_k + increment
        if max_top_k > 0:
            next_top_k = min(next_top_k, max_top_k)
        if next_top_k <= current_top_k:
            break

        contexts = retriever(query, next_top_k)
        attempt_gate = evaluate_retrieval_gate(query, contexts, rag_config)
        attempt = {
            "attempt": attempt_number,
            "strategy": "increase_top_k",
            "query": query,
            "top_k": next_top_k,
            "gate_result": attempt_gate,
        }
        trace["retry_attempts"].append(attempt)
        trace["selected_strategy"] = "increase_top_k"
        trace["retrieved_contexts"] = contexts
        trace["gate_result"] = attempt_gate
        trace["pass_fail_reason"] = attempt_gate["reason"]
        trace["final_top_k"] = next_top_k

        current_top_k = next_top_k
        if attempt_gate["passed"]:
            break

    trace["retry_exhausted"] = bool(
        trace["retry_attempts"] and not trace["gate_result"].get("passed", False)
    )
    return trace


def _apply_optional_reranker(
    query: str,
    trace: dict[str, Any],
    rag_config: dict[str, Any],
) -> None:
    reranker_config = rag_config.get("reranker") or {}
    metadata = {
        "enabled": bool(reranker_config.get("enabled", False)),
        "provider": reranker_config.get("provider", "local"),
        "model": reranker_config.get("model", "BAAI/bge-reranker-v2-m3"),
        "input_count": 0,
        "output_count": len(trace.get("retrieved_contexts") or []),
        "latency_ms": 0,
        "failed": False,
        "fail_open_used": False,
    }

    if not metadata["enabled"]:
        trace["reranker"] = metadata
        return

    candidate_contexts = list(trace.get("retrieved_contexts") or [])
    final_contexts, metadata = rerank_contexts(
        query=query,
        contexts=candidate_contexts,
        reranker_config=reranker_config,
    )
    trace["candidate_contexts"] = candidate_contexts
    trace["retrieved_contexts"] = final_contexts
    trace["reranker"] = metadata
    trace["final_top_k"] = len(final_contexts)
