import math
import re
from collections import Counter
from dataclasses import dataclass


_TOKEN_PATTERN = re.compile(r"[\w\-]+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) > 1
    ]


@dataclass(frozen=True)
class BM25Result:
    index: int
    score: float


class BM25Ranker:
    def __init__(
        self,
        documents: list[str],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self._documents = [tokenize(text) for text in documents]
        self._k1 = k1
        self._b = b
        self._average_length = (
            sum(len(tokens) for tokens in self._documents)
            / max(len(self._documents), 1)
        )
        document_frequency: Counter[str] = Counter()
        for tokens in self._documents:
            document_frequency.update(set(tokens))
        count = len(self._documents)
        self._idf = {
            term: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def search(self, query: str, *, limit: int) -> list[BM25Result]:
        query_terms = tokenize(query)
        if not query_terms or not self._documents:
            return []

        results: list[BM25Result] = []
        for index, tokens in enumerate(self._documents):
            frequencies = Counter(tokens)
            length = len(tokens)
            score = 0.0
            for term in query_terms:
                frequency = frequencies.get(term, 0)
                if frequency == 0:
                    continue
                denominator = frequency + self._k1 * (
                    1 - self._b
                    + self._b * length / max(self._average_length, 1.0)
                )
                score += self._idf.get(term, 0.0) * (
                    frequency * (self._k1 + 1) / denominator
                )
            if score > 0:
                results.append(BM25Result(index=index, score=score))

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]
