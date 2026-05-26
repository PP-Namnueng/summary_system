from library.keyword_search import KeywordSearch, tokenize


def test_keyword_search_returns_exact_acronym_and_model_terms():
    search = KeywordSearch(
        chunks=[
            {
                "chunk_id": "a",
                "doc_id": "doc",
                "text": "Semantic retrieval can miss exact BM25 and RRF acronyms.",
                "title": "Retrieval",
            },
            {
                "chunk_id": "b",
                "doc_id": "doc",
                "text": "The bge-reranker-v2-m3 model reranks candidate contexts.",
                "title": "Reranking",
            },
        ]
    )

    acronym_results = search.search("BM25", top_k=1)
    model_results = search.search("bge-reranker-v2-m3", top_k=1)

    assert acronym_results[0]["chunk_id"] == "a"
    assert acronym_results[0]["score_type"] == "keyword_bm25"
    assert model_results[0]["chunk_id"] == "b"
    assert "bge-reranker-v2-m3" in tokenize(model_results[0]["text"])


def test_exact_phrase_boost_affects_ranking():
    search = KeywordSearch(
        chunks=[
            {"chunk_id": "loose", "text": "query planning and rewrite strategies"},
            {"chunk_id": "phrase", "text": "A query rewrite step can improve retrieval."},
        ]
    )

    results = search.search("query rewrite", top_k=2)

    assert results[0]["chunk_id"] == "phrase"
    assert results[0]["keyword_score"] > results[1]["keyword_score"]
