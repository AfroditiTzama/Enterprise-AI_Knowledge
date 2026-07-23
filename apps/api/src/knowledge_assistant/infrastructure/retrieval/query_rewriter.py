import re


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "that", "the", "this",
    "to", "was", "what", "when", "where", "which", "who", "why", "with",
    "και", "να", "το", "τα", "τη", "την", "της", "των", "σε", "στο",
    "στη", "στις", "που", "πως", "πώς", "τι", "είναι", "ειναι", "με",
    "για", "από", "απο", "ο", "η", "οι", "ένα", "ενα", "μια", "μία",
}


class LocalQueryRewriter:
    """Create deterministic, no-cost query variants for hybrid search."""

    def rewrite(self, question: str) -> tuple[str, ...]:
        cleaned = " ".join(question.strip().split())
        if not cleaned:
            return ()

        tokens = [
            token.lower()
            for token in re.findall(r"[\w\-]+", cleaned, flags=re.UNICODE)
        ]
        keywords = [
            token
            for token in tokens
            if len(token) > 2 and token not in _STOP_WORDS
        ]

        variants = [cleaned]
        if keywords:
            keyword_query = " ".join(dict.fromkeys(keywords))
            if keyword_query.lower() != cleaned.lower():
                variants.append(keyword_query)

        # A compact phrase works well for embedding search when the original
        # question contains conversational filler.
        if len(keywords) > 6:
            variants.append(" ".join(dict.fromkeys(keywords[:12])))

        return tuple(dict.fromkeys(variant for variant in variants if variant))
