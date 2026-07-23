import re
from dataclasses import dataclass


_TOKEN_PATTERN = re.compile(r"[\w\-]+", flags=re.UNICODE)
_CITATION_PATTERN = re.compile(r"\[(S\d+)\]")


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) > 1
    }


@dataclass(frozen=True)
class RetrievalMetrics:
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float


@dataclass(frozen=True)
class AnswerMetrics:
    citation_correctness: float
    citation_coverage: float
    answer_relevance: float
    groundedness: float


def retrieval_metrics(
    *,
    retrieved_ids: list[str],
    expected_ids: set[str],
    k: int,
) -> RetrievalMetrics:
    top = retrieved_ids[: max(1, k)]
    hits = [source_id for source_id in top if source_id in expected_ids]
    precision = len(hits) / max(len(top), 1)
    recall = len(set(hits)) / max(len(expected_ids), 1)
    reciprocal_rank = 0.0
    for index, source_id in enumerate(top, start=1):
        if source_id in expected_ids:
            reciprocal_rank = 1.0 / index
            break
    return RetrievalMetrics(precision, recall, reciprocal_rank)


def answer_metrics(
    *,
    answer: str,
    available_source_ids: set[str],
    source_texts: list[str],
    question: str,
) -> AnswerMetrics:
    cited_ids = _CITATION_PATTERN.findall(answer)
    valid_citations = [
        source_id for source_id in cited_ids if source_id in available_source_ids
    ]
    citation_correctness = (
        len(valid_citations) / len(cited_ids) if cited_ids else 0.0
    )

    factual_blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n|\n(?=[-*])", answer)
        if len(_tokens(block)) >= 5
    ]
    cited_blocks = [
        block for block in factual_blocks if _CITATION_PATTERN.search(block)
    ]
    citation_coverage = (
        len(cited_blocks) / len(factual_blocks) if factual_blocks else 1.0
    )

    answer_tokens = _tokens(answer)
    question_tokens = _tokens(question)
    answer_relevance = len(answer_tokens & question_tokens) / max(
        len(question_tokens), 1
    )

    evidence_tokens = _tokens(" ".join(source_texts))
    groundedness = len(answer_tokens & evidence_tokens) / max(
        len(answer_tokens), 1
    )

    return AnswerMetrics(
        citation_correctness=min(citation_correctness, 1.0),
        citation_coverage=min(citation_coverage, 1.0),
        answer_relevance=min(answer_relevance, 1.0),
        groundedness=min(groundedness, 1.0),
    )


def classification_accuracy(
    expected: list[str],
    predicted: list[str],
) -> float:
    if not expected or len(expected) != len(predicted):
        return 0.0
    return sum(
        left == right
        for left, right in zip(expected, predicted, strict=True)
    ) / len(expected)


def token_similarity(reference: str, candidate: str) -> float:
    reference_tokens = _tokens(reference)
    candidate_tokens = _tokens(candidate)
    if not reference_tokens and not candidate_tokens:
        return 1.0
    return len(reference_tokens & candidate_tokens) / max(
        len(reference_tokens | candidate_tokens), 1
    )
