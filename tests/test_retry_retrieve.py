from evals.auto_retrieve import retrieve_with_gate_retry, retry_retrieve
import evals.auto_retrieve as auto_retrieve_module
from evals.retrieval_gate import evaluate_retrieval_gate
from evals.trace import build_trace
from summary.library.rag_engine import RAGEngine


def test_retrieval_gate_passes_when_runtime_metrics_meet_thresholds():
    result = evaluate_retrieval_gate(
        "python testing",
        [
            {"text": "python testing with pytest", "score": 0.90},
            {"text": "unit tests and fixtures", "score": 0.80},
        ],
        {
            "min_context_count": 2,
            "min_top_similarity": 0.70,
            "min_avg_similarity": 0.70,
            "max_duplicate_ratio": 0.35,
        },
    )

    assert result["passed"] is True
    assert result["reason"] == "passed"


def test_retrieval_gate_fails_on_runtime_metrics_only():
    result = evaluate_retrieval_gate(
        "python testing",
        [{"text": "unrelated", "score": 0.20}],
        {
            "min_context_count": 2,
            "min_top_similarity": 0.70,
            "min_avg_similarity": 0.70,
            "max_duplicate_ratio": 0.35,
        },
    )

    assert result["passed"] is False
    assert "min_context_count" in result["failures"]
    assert "min_top_similarity" in result["failures"]


def test_retrieval_gate_uses_vector_score_for_hybrid_results():
    result = evaluate_retrieval_gate(
        "python testing",
        [
            {
                "text": "python testing with pytest",
                "score": 0.01,
                "score_type": "hybrid_rrf",
                "vector_score": 0.90,
            }
        ],
        {
            "min_context_count": 1,
            "min_top_similarity": 0.70,
        },
    )

    assert result["passed"] is True
    assert result["metrics"]["top_similarity"] == 0.90


def test_retry_retrieve_skips_retry_when_gate_passes():
    calls = []

    trace = retry_retrieve(
        "python testing",
        [
            {"text": "python testing with pytest", "score": 0.90},
            {"text": "unit tests and fixtures", "score": 0.80},
        ],
        retriever=lambda query, top_k: calls.append((query, top_k)) or [],
        rag_config={
            "top_k": 2,
            "min_context_count": 2,
            "min_top_similarity": 0.70,
            "enable_auto_retrieve": True,
            "max_attempts": 1,
            "retry_strategies": ["increase_top_k"],
        },
    )

    assert trace["gate_result"]["passed"] is True
    assert trace["retry_attempts"] == []
    assert calls == []


def test_retry_retrieve_increases_top_k_after_gate_failure():
    def retriever(query, top_k):
        assert query == "python testing"
        assert top_k == 4
        return [
            {"text": "python testing with pytest", "score": 0.90},
            {"text": "unit tests and fixtures", "score": 0.80},
        ]

    trace = retry_retrieve(
        "python testing",
        [{"text": "unrelated", "score": 0.20}],
        retriever=retriever,
        rag_config={
            "top_k": 2,
            "min_context_count": 2,
            "min_top_similarity": 0.70,
            "min_avg_similarity": 0.70,
            "enable_auto_retrieve": True,
            "max_attempts": 1,
            "retry_strategies": ["increase_top_k"],
            "increase_top_k": {
                "increment": 2,
                "max_top_k": 4,
            },
        },
    )

    assert trace["selected_strategy"] == "increase_top_k"
    assert trace["final_top_k"] == 4
    assert trace["gate_result"]["passed"] is True
    assert len(trace["retry_attempts"]) == 1
    assert trace["retry_exhausted"] is False


def test_retry_retrieve_marks_exhausted_when_gate_still_fails():
    trace = retry_retrieve(
        "python testing",
        [{"text": "unrelated", "score": 0.20}],
        retriever=lambda query, top_k: [{"text": "still unrelated", "score": 0.30}],
        rag_config={
            "top_k": 2,
            "min_context_count": 2,
            "min_top_similarity": 0.70,
            "enable_auto_retrieve": True,
            "max_attempts": 1,
            "retry_strategies": ["increase_top_k"],
            "increase_top_k": {
                "increment": 2,
                "max_top_k": 4,
            },
        },
    )

    assert trace["gate_result"]["passed"] is False
    assert trace["retry_exhausted"] is True
    assert trace["pass_fail_reason"]


def test_retry_retrieve_uses_rag_max_attempts_as_source_of_truth():
    calls = []

    retry_retrieve(
        "python testing",
        [{"text": "unrelated", "score": 0.20}],
        retriever=lambda query, top_k: calls.append(top_k) or [{"text": "bad", "score": 0.20}],
        rag_config={
            "top_k": 2,
            "min_context_count": 2,
            "min_top_similarity": 0.70,
            "enable_auto_retrieve": True,
            "max_attempts": 1,
            "max_retrieve_attempts": 3,
            "retry_strategies": ["increase_top_k"],
            "increase_top_k": {
                "increment": 2,
                "max_top_k": 8,
            },
        },
    )

    assert calls == [4]


def test_shared_helper_retrieves_and_retries_with_increase_top_k():
    class VectorStore:
        def __init__(self):
            self.calls = []

        def search(self, query, top_k):
            self.calls.append((query, top_k))
            if top_k == 2:
                return [{"text": "unrelated", "score": 0.20}]
            return [
                {"text": "python testing with pytest", "score": 0.90},
                {"text": "unit tests and fixtures", "score": 0.80},
            ]

    vector_store = VectorStore()
    trace = retrieve_with_gate_retry(
        "python testing",
        vector_store,
        {
            "rag": {
                "top_k": 2,
                "min_context_count": 2,
                "min_top_similarity": 0.70,
                "enable_auto_retrieve": True,
                "max_attempts": 1,
                "retry_strategies": ["increase_top_k"],
                "increase_top_k": {"increment": 2, "max_top_k": 4},
            }
        },
    )

    assert vector_store.calls == [("python testing", 2), ("python testing", 4)]
    assert trace["selected_strategy"] == "increase_top_k"
    assert trace["final_top_k"] == 4
    assert trace["gate_result"]["passed"] is True
    assert trace["max_attempts_source"] == "rag.max_attempts"


def test_shared_helper_uses_hybrid_retriever_when_enabled():
    class VectorStore:
        def __init__(self):
            self.calls = []
            self.chunks = [
                {
                    "chunk_id": "keyword",
                    "doc_id": "doc",
                    "chunk_index": 1,
                    "text": "BM25 exact keyword context",
                }
            ]

        def search(self, query, top_k):
            self.calls.append(top_k)
            return [{"chunk_id": "vector", "text": "semantic context", "score": 0.9}]

        def export_chunks(self):
            return self.chunks

    vector_store = VectorStore()
    trace = retrieve_with_gate_retry(
        "BM25",
        vector_store,
        {
            "rag": {
                "top_k": 2,
                "min_context_count": 1,
                "min_top_similarity": 0.70,
                "hybrid_search": {
                    "enabled": True,
                    "vector_top_k": 2,
                    "keyword_top_k": 2,
                },
            }
        },
    )

    assert trace["retrieval"]["retriever"] == "hybrid"
    assert vector_store.calls == [4]
    assert any(
        context["chunk_id"] == "keyword"
        for context in trace["retrieved_contexts"]
    )


def test_qa_style_flow_can_use_returned_final_contexts():
    class VectorStore:
        def search(self, query, top_k):
            return [{"text": f"context for {query}", "score": 0.90, "title": "Book"}]

    trace = retrieve_with_gate_retry(
        "rag",
        VectorStore(),
        {"rag": {"top_k": 1, "min_context_count": 1, "min_top_similarity": 0.70}},
    )

    final_contexts = trace["retrieved_contexts"]
    assert final_contexts[0]["text"] == "context for rag"
    assert trace["retry_attempts"] == []


def test_learning_recommendations_use_provided_contexts_without_search():
    class VectorStore:
        def search(self, query, top_k):
            raise AssertionError("generation must not retrieve")

    class LLM:
        def __init__(self):
            self.prompts = []

        def complete(self, prompt):
            self.prompts.append(prompt)
            return "learning plan"

    engine = RAGEngine.__new__(RAGEngine)
    engine.vector_store = VectorStore()
    engine.llm = LLM()

    result = engine.recommend_learning_from_contexts(
        "RAG",
        [{
            "doc_id": "doc-1",
            "title": "RAG Book",
            "chapter": "Retrieval",
            "file_path": "rag.pdf",
            "score": 0.8,
        }],
    )

    assert result["success"] is True
    assert result["recommendations_text"] == "learning plan"
    assert result["source_documents"][0]["title"] == "RAG Book"
    assert engine.llm.prompts


def test_block_and_retry_fail_modes_prevent_generation_when_gate_still_fails():
    class VectorStore:
        def search(self, query, top_k):
            return [{"text": "unrelated", "score": 0.10}]

    class LLM:
        def __init__(self):
            self.called = False

        def complete(self, prompt):
            self.called = True
            return "should not happen"

    for fail_mode in ("block", "retry"):
        llm = LLM()
        trace = retrieve_with_gate_retry(
            "python testing",
            VectorStore(),
            {
                "eval": {"behavior": {"fail_mode": fail_mode}},
                "rag": {
                    "top_k": 1,
                    "min_context_count": 2,
                    "min_top_similarity": 0.70,
                    "enable_auto_retrieve": False,
                    "max_attempts": 1,
                    "increase_top_k": {"increment": 1, "max_top_k": 2},
                },
            },
        )

        if not trace["gate_result"]["passed"] and fail_mode in {"block", "retry"}:
            generated = False
        else:
            llm.complete("generate")
            generated = True

        assert generated is False
        assert llm.called is False


def test_block_fail_mode_does_not_retry_even_when_auto_retrieve_enabled():
    class VectorStore:
        def __init__(self):
            self.calls = []

        def search(self, query, top_k):
            self.calls.append(top_k)
            return [{"text": "unrelated", "score": 0.10}]

    vector_store = VectorStore()
    trace = retrieve_with_gate_retry(
        "python testing",
        vector_store,
        {
            "eval": {"behavior": {"fail_mode": "block"}},
            "rag": {
                "top_k": 2,
                "min_context_count": 2,
                "min_top_similarity": 0.70,
                "enable_auto_retrieve": True,
                "max_attempts": 3,
                "increase_top_k": {"increment": 2, "max_top_k": 8},
            },
        },
    )

    assert vector_store.calls == [2]
    assert trace["retry_attempts"] == []
    assert trace["gate_result"]["passed"] is False


def test_learning_recommendations_trace_stage_is_recorded():
    trace = build_trace(
        query="RAG",
        contexts=[],
        metadata={"stage": "learning_recommendations"},
    ).to_dict()

    assert trace["metadata"]["stage"] == "learning_recommendations"


def test_retry_retrieve_runtime_does_not_import_ragas_or_deepeval():
    source_names = set(auto_retrieve_module.__dict__)

    assert "ragas" not in source_names
    assert "deepeval" not in source_names
