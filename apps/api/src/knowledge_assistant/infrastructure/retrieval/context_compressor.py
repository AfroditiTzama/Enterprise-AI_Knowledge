import re

from knowledge_assistant.infrastructure.retrieval.bm25 import tokenize


class ExtractiveContextCompressor:
    def compress(
        self,
        *,
        text: str,
        query: str,
        max_characters: int,
    ) -> str:
        cleaned = text.strip()
        if len(cleaned) <= max_characters:
            return cleaned

        query_terms = set(tokenize(query))
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+|\n{2,}", cleaned)
            if sentence.strip()
        ]
        scored: list[tuple[float, int, str]] = []
        for index, sentence in enumerate(sentences):
            sentence_terms = set(tokenize(sentence))
            overlap = len(query_terms & sentence_terms)
            density = overlap / max(len(sentence_terms), 1)
            scored.append((overlap + density, index, sentence))

        scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
        selected: list[tuple[int, str]] = []
        total = 0
        for _, index, sentence in scored:
            if total + len(sentence) + 1 > max_characters:
                continue
            selected.append((index, sentence))
            total += len(sentence) + 1
            if total >= max_characters * 0.85:
                break

        if not selected:
            return cleaned[:max_characters].rstrip()

        selected.sort(key=lambda item: item[0])
        return " ".join(sentence for _, sentence in selected)
