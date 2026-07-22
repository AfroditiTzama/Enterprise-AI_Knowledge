from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WikiQualityScoreResponse(BaseModel):
    source_coverage: int
    freshness: int
    consistency: int
    connectivity: int
    overall: int
    supported_claims: int
    unsupported_claims: int
    open_conflicts: int
    connections_count: int
    issues: list[str]


class WikiPageResponse(BaseModel):
    id: UUID
    document_id: UUID | None
    slug: str
    title: str
    summary: str
    content_markdown: str
    created_at: datetime
    updated_at: datetime
    quality: WikiQualityScoreResponse | None = None


class WikiPageSourceResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_filename: str
    chunk_index: int
    page_number: int | None


class WikiClaimCitationResponse(BaseModel):
    claim_key: str
    claim_text: str
    position: int
    sources: list[WikiPageSourceResponse]


class WikiPageReferenceResponse(BaseModel):
    page_id: UUID
    slug: str
    title: str
    label: str


class WikiPageConflictResponse(BaseModel):
    id: UUID
    source_document_id: UUID | None
    existing_statement: str
    incoming_statement: str
    explanation: str
    status: str
    resolution_note: str
    created_at: datetime
    resolved_at: datetime | None


class WikiPageDetailsResponse(WikiPageResponse):
    sources: list[WikiPageSourceResponse]
    related_pages: list[WikiPageReferenceResponse]
    backlinks: list[WikiPageReferenceResponse]
    conflicts: list[WikiPageConflictResponse]
    claim_citations: list[WikiClaimCitationResponse]


class WikiPageRevisionResponse(BaseModel):
    id: UUID
    wiki_page_id: UUID | None
    page_slug: str
    revision_number: int
    title: str
    summary: str
    content_markdown: str
    operation: str
    triggering_document_id: UUID | None
    created_at: datetime


class WikiRevisionDiffLineResponse(BaseModel):
    kind: Literal["added", "removed", "context"]
    text: str


class WikiRevisionDiffResponse(BaseModel):
    from_revision_number: int | None
    to_revision_number: int
    lines: list[WikiRevisionDiffLineResponse]


class UpdateWikiConflictRequest(BaseModel):
    status: Literal["OPEN", "RESOLVED", "DISMISSED"]
    resolution_note: str = Field(default="", max_length=2000)


class CompileWikiResponse(BaseModel):
    document_id: UUID
    pages_count: int
    sources_count: int
    links_count: int
    conflicts_count: int
    pages: list[WikiPageResponse]


class WikiMaintenanceSuggestionResponse(BaseModel):
    id: UUID
    issue_type: str
    status: str
    title: str
    description: str
    page_ids: list[UUID]
    metadata: dict[str, Any]
    confidence: float
    created_at: datetime
    updated_at: datetime


class UpdateWikiMaintenanceSuggestionRequest(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
