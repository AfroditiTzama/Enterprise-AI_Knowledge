from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RetrievalFilters:
    source_scope: str = "all"
    document_ids: tuple[UUID, ...] = ()
    content_types: tuple[str, ...] = ()
    max_sources: int = 7

    def __post_init__(self) -> None:
        if self.source_scope not in {"all", "documents", "wiki"}:
            raise ValueError(
                "Source scope must be all, documents or wiki."
            )
        if not 1 <= self.max_sources <= 12:
            raise ValueError("max_sources must be between 1 and 12.")


@dataclass(frozen=True)
class RetrievalDiagnostics:
    rewritten_queries: tuple[str, ...]
    lexical_candidates: int
    vector_candidates: int
    wiki_candidates: int
    fused_candidates: int
    selected_sources: int
    context_characters: int
