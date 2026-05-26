"""Shared trace object contract for RAG, summary, DeepEval, and RAGAS hooks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class PipelineTrace:
    query: str
    original_query: str = ""
    final_query: str = ""
    contexts: list[dict[str, Any]] = field(default_factory=list)
    retrieved_contexts: list[dict[str, Any]] = field(default_factory=list)
    gate_result: dict[str, Any] = field(default_factory=dict)
    retry_attempts: list[dict[str, Any]] = field(default_factory=list)
    selected_strategy: str | None = None
    pass_fail_reason: str = ""
    prompt: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_context(context: dict[str, Any] | str, index: int = 0) -> dict[str, Any]:
    if isinstance(context, str):
        return {
            "id": str(index),
            "text": context,
            "score": None,
            "source": {},
        }

    return {
        "id": str(context.get("chunk_id") or context.get("id") or index),
        "text": context.get("text") or context.get("content") or "",
        "score": context.get("score"),
        "source": {
            "doc_id": context.get("doc_id", ""),
            "title": context.get("title", ""),
            "chapter": context.get("chapter", ""),
            "filename": context.get("filename", ""),
            "file_path": context.get("file_path", ""),
            "chunk_index": context.get("chunk_index"),
        },
        "metadata": {
            key: value
            for key, value in context.items()
            if key
            not in {
                "chunk_id",
                "id",
                "text",
                "content",
                "score",
                "doc_id",
                "title",
                "chapter",
                "filename",
                "file_path",
                "chunk_index",
            }
        },
    }


def contexts_from_retrieval_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_context(result, index=i) for i, result in enumerate(results or [])]


def build_trace(
    query: str,
    contexts: list[dict[str, Any]] | None = None,
    prompt: str = "",
    summary: str = "",
    metadata: dict[str, Any] | None = None,
    original_query: str | None = None,
    final_query: str | None = None,
    gate_result: dict[str, Any] | None = None,
    retry_attempts: list[dict[str, Any]] | None = None,
    selected_strategy: str | None = None,
    pass_fail_reason: str = "",
) -> PipelineTrace:
    final_contexts = contexts or []
    return PipelineTrace(
        query=query,
        original_query=original_query or query,
        final_query=final_query or query,
        contexts=final_contexts,
        retrieved_contexts=final_contexts,
        gate_result=gate_result or {},
        retry_attempts=retry_attempts or [],
        selected_strategy=selected_strategy,
        pass_fail_reason=pass_fail_reason,
        prompt=prompt,
        summary=summary,
        metadata=metadata or {},
    )
