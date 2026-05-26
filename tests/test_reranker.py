import pytest

import evals.auto_retrieve as auto_retrieve_module
from evals.auto_retrieve import retrieve_with_gate_retry
from library.reranker import rerank_contexts


class ScoreByChunkIdReranker:
    def __init__(self, scores):
        self.scores = scores

    def rerank(self, query, contexts, top_k):
        scored = []
        for context in contexts:
            updated = dict(context)
            updated["retrieval_score"] = context.get("score")
            updated["rerank_score"] = self.scores[context["chunk_id"]]
            updated["rank_source"] = "reranker"
            scored.append(updated)

        scored.sort(key=lambda item: item["rerank_score"], reverse=True)
        for index, context in enumerate(scored[:top_k]):
            context["reranked_rank"] = index + 1
        return scored[:top_k]


def test_disabled_reranker_returns_contexts_unchanged():
    contexts = [
        {"chunk_id": "a", "text": "alpha", "score": 0.9},
        {"chunk_id": "b", "text": "beta", "score": 0.8},
    ]

    final_contexts, metadata = rerank_contexts(
        "query",
        contexts,
        {"enabled": False, "final_top_k": 1},
    )

    assert final_contexts is contexts
    assert metadata["enabled"] is False
    assert metadata["output_count"] == 2


def test_enabled_reranker_reorders_and_respects_final_top_k():
    contexts = [
        {"chunk_id": "a", "doc_id": "d1", "chunk_index": 0, "text": "alpha", "score": 0.9, "title": "A"},
        {"chunk_id": "b", "doc_id": "d2", "chunk_index": 0, "text": "beta", "score": 0.8, "title": "B"},
        {"chunk_id": "c", "doc_id": "d3", "chunk_index": 0, "text": "gamma", "score": 0.7, "title": "C"},
    ]

    final_contexts, metadata = rerank_contexts(
        "query",
        contexts,
        {"enabled": True, "final_top_k": 2, "input_top_n": 3},
        reranker=ScoreByChunkIdReranker({"a": 0.1, "b": 0.9, "c": 0.8}),
    )

    assert [context["chunk_id"] for context in final_contexts] == ["b", "c"]
    assert [context["reranked_rank"] for context in final_contexts] == [1, 2]
    assert final_contexts[0]["original_rank"] == 2
    assert final_contexts[0]["retrieval_score"] == 0.8
    assert final_contexts[0]["score"] == 0.8
    assert final_contexts[0]["title"] == "B"
    assert metadata["input_count"] == 3
    assert metadata["output_count"] == 2
    assert metadata["failed"] is False


def test_reranker_fail_open_falls_back_to_original_order():
    class FailingReranker:
        def rerank(self, query, contexts, top_k):
            raise RuntimeError("model failed")

    contexts = [
        {"chunk_id": "a", "text": "alpha", "score": 0.9},
        {"chunk_id": "b", "text": "beta", "score": 0.8},
        {"chunk_id": "c", "text": "gamma", "score": 0.7},
    ]

    final_contexts, metadata = rerank_contexts(
        "query",
        contexts,
        {"enabled": True, "final_top_k": 2, "fail_open": True},
        reranker=FailingReranker(),
    )

    assert [context["chunk_id"] for context in final_contexts] == ["a", "b"]
    assert metadata["failed"] is True
    assert metadata["fail_open_used"] is True
    assert metadata["error_type"] == "RuntimeError"


def test_reranker_dedupes_obvious_duplicate_candidates():
    contexts = [
        {"chunk_id": "a", "doc_id": "d1", "chunk_index": 0, "text": "same text", "score": 0.9},
        {"chunk_id": "a", "doc_id": "d1", "chunk_index": 0, "text": "same text", "score": 0.8},
        {"chunk_id": "b", "doc_id": "d1", "chunk_index": 1, "text": "different text", "score": 0.7},
    ]

    final_contexts, metadata = rerank_contexts(
        "query",
        contexts,
        {"enabled": True, "final_top_k": 3, "input_top_n": 3},
        reranker=ScoreByChunkIdReranker({"a": 0.5, "b": 0.4}),
    )

    assert [context["chunk_id"] for context in final_contexts] == ["a", "b"]
    assert metadata["input_count"] == 2


def test_reranker_can_fail_closed():
    class FailingReranker:
        def rerank(self, query, contexts, top_k):
            raise RuntimeError("model failed")

    with pytest.raises(RuntimeError):
        rerank_contexts(
            "query",
            [{"chunk_id": "a", "text": "alpha", "score": 0.9}],
            {"enabled": True, "fail_open": False},
            reranker=FailingReranker(),
        )


def test_retrieve_with_gate_retry_applies_optional_reranker(monkeypatch):
    class VectorStore:
        def search(self, query, top_k):
            return [
                {"chunk_id": "a", "text": "alpha", "score": 0.9},
                {"chunk_id": "b", "text": "beta", "score": 0.8},
            ]

    def fake_rerank_contexts(query, contexts, reranker_config):
        assert reranker_config["enabled"] is True
        return [dict(contexts[1], rerank_score=0.9, rank_source="reranker")], {
            "enabled": True,
            "provider": "local",
            "model": "fake",
            "input_count": 2,
            "output_count": 1,
            "latency_ms": 1,
            "failed": False,
            "fail_open_used": False,
        }

    monkeypatch.setattr(auto_retrieve_module, "rerank_contexts", fake_rerank_contexts)

    trace = retrieve_with_gate_retry(
        "query",
        VectorStore(),
        {
            "rag": {
                "top_k": 2,
                "min_context_count": 1,
                "min_top_similarity": 0.1,
                "reranker": {
                    "enabled": True,
                    "model": "fake",
                    "final_top_k": 1,
                },
            }
        },
    )

    assert [context["chunk_id"] for context in trace["candidate_contexts"]] == ["a", "b"]
    assert [context["chunk_id"] for context in trace["retrieved_contexts"]] == ["b"]
    assert trace["reranker"]["enabled"] is True
    assert trace["final_top_k"] == 1
