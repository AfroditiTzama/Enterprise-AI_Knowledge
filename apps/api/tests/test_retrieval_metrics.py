from knowledge_assistant.domain.evaluation.metrics import (
    answer_metrics,
    retrieval_metrics,
)


def test_retrieval_metrics() -> None:
    metrics = retrieval_metrics(
        retrieved_ids=["a", "b", "c"],
        expected_ids={"b", "c"},
        k=3,
    )
    assert metrics.precision_at_k == 2 / 3
    assert metrics.recall_at_k == 1.0
    assert metrics.reciprocal_rank == 0.5


def test_answer_metrics_detect_valid_citations() -> None:
    metrics = answer_metrics(
        answer="A supported factual paragraph with enough words. [S1]",
        available_source_ids={"S1"},
        source_texts=["A supported factual paragraph with enough words."],
        question="What is supported?",
    )
    assert metrics.citation_correctness == 1.0
    assert metrics.citation_coverage == 1.0
