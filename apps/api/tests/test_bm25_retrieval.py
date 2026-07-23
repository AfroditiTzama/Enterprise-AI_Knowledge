from knowledge_assistant.infrastructure.retrieval.bm25 import BM25Ranker


def test_bm25_prefers_matching_document() -> None:
    ranker = BM25Ranker(
        [
            "transformer model for molecules",
            "hospital appointment scheduling",
        ]
    )
    results = ranker.search("molecular transformer", limit=2)
    assert results
    assert results[0].index == 0
