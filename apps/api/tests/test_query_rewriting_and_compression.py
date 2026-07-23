from knowledge_assistant.infrastructure.retrieval.context_compressor import (
    ExtractiveContextCompressor,
)
from knowledge_assistant.infrastructure.retrieval.query_rewriter import (
    LocalQueryRewriter,
)


def test_query_rewriter_keeps_original_and_adds_keywords() -> None:
    variants = LocalQueryRewriter().rewrite(
        "What are the main findings about transformer models?"
    )

    assert variants[0] == "What are the main findings about transformer models?"
    assert any("findings" in value and "transformer" in value for value in variants)


def test_context_compressor_prefers_query_relevant_sentences() -> None:
    text = (
        "The first paragraph discusses administration. "
        "Transformer models are used for document retrieval. "
        "The final paragraph covers unrelated scheduling."
    )

    compressed = ExtractiveContextCompressor().compress(
        text=text,
        query="transformer document retrieval",
        max_characters=70,
    )

    assert "Transformer models" in compressed
    assert len(compressed) <= 70
