from library.hybrid_retriever import HybridRetriever
from library.keyword_search import KeywordSearch


class VectorStore:
    def __init__(self):
        self.calls = []

    def search(self, query, top_k):
        self.calls.append((query, top_k))
        return [
            {
                "chunk_id": "shared",
                "doc_id": "doc",
                "chunk_index": 1,
                "text": "Vector result mentioning retrieval.",
                "score": 0.9,
            },
            {
                "chunk_id": "vector-only",
                "doc_id": "doc",
                "chunk_index": 2,
                "text": "Semantic-only result.",
                "score": 0.8,
            },
        ][:top_k]


def test_hybrid_rrf_dedupes_and_preserves_scores():
    vector_store = VectorStore()
    keyword = KeywordSearch(
        chunks=[
            {
                "chunk_id": "shared",
                "doc_id": "doc",
                "chunk_index": 1,
                "text": "Vector result mentioning retrieval and BM25.",
            },
            {
                "chunk_id": "keyword-only",
                "doc_id": "doc",
                "chunk_index": 3,
                "text": "BM25 exact keyword result.",
            },
        ]
    )
    retriever = HybridRetriever(
        vector_store,
        keyword_search=keyword,
        rag_config={"hybrid_search": {"enabled": True, "vector_top_k": 2, "keyword_top_k": 2}},
    )

    results = retriever.search("BM25", top_k=3)
    ids = [result["chunk_id"] for result in results]

    assert len(ids) == len(set(ids))
    assert "shared" in ids
    assert "keyword-only" in ids
    shared = next(result for result in results if result["chunk_id"] == "shared")
    assert shared["score_type"] == "hybrid_rrf"
    assert shared["vector_score"] == 0.9
    assert shared["keyword_score"] is not None
    assert set(shared["rank_sources"]) == {"keyword", "vector"}


def test_hybrid_respects_retry_top_k_for_candidate_pool_sizes():
    vector_store = VectorStore()
    keyword = KeywordSearch(chunks=[{"chunk_id": "k", "text": "BM25"}])
    retriever = HybridRetriever(
        vector_store,
        keyword_search=keyword,
        rag_config={"hybrid_search": {"enabled": True, "vector_top_k": 20, "keyword_top_k": 20}},
    )

    retriever.search("BM25", top_k=14)

    assert vector_store.calls == [("BM25", 28)]
    assert retriever.last_trace["keyword_top_k"] == 28
    assert retriever.last_trace["vector_top_k"] == 28


def test_hybrid_falls_back_to_vector_when_keyword_index_is_too_large():
    class LargeVectorStore(VectorStore):
        def get_stats(self):
            return {"total_chunks": 100}

        def export_chunks(self, limit=None):
            raise AssertionError("keyword search should fail before exporting all chunks")

    retriever = HybridRetriever(
        LargeVectorStore(),
        rag_config={
            "keyword_search": {"max_chunks_for_in_memory": 10},
            "hybrid_search": {"enabled": True, "vector_top_k": 2, "keyword_top_k": 2},
        },
    )

    results = retriever.search("BM25", top_k=2)

    assert [result["chunk_id"] for result in results] == ["shared", "vector-only"]
    assert retriever.last_trace["keyword_failed"] is True
    assert "max_chunks_for_in_memory=10" in retriever.last_trace["keyword_error"]
