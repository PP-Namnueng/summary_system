from library.retrieval_quality import apply_content_quality_downrank, content_quality_penalty


def test_content_quality_downrank_lowers_noisy_chunks():
    contexts = [
        {"chunk_id": "index", "title": "Index", "text": "BM25 123", "hybrid_score": 1.0, "score": 1.0, "score_type": "hybrid_rrf"},
        {"chunk_id": "body", "title": "Retrieval", "text": "BM25 ranking details", "hybrid_score": 0.9, "score": 0.9, "score_type": "hybrid_rrf"},
    ]

    ranked = apply_content_quality_downrank(
        contexts,
        {"enabled": True, "mode": "downrank", "penalty": 0.2},
    )

    assert content_quality_penalty(contexts[0]) == 0.2
    assert ranked[0]["chunk_id"] == "body"
    assert ranked[1]["content_quality_penalty"] == 0.2
