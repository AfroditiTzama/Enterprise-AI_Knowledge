from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WikiPageResponse(BaseModel):
    id: UUID
    document_id: UUID | None
    slug: str
    title: str
    summary: str
    content_markdown: str
    created_at: datetime
    updated_at: datetime


class WikiPageSourceResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_filename: str
    chunk_index: int
    page_number: int | None


class WikiPageReferenceResponse(BaseModel):
    page_id: UUID
    slug: str
    title: str
    label: str


class WikiPageDetailsResponse(WikiPageResponse):
    sources: list[WikiPageSourceResponse]
    related_pages: list[WikiPageReferenceResponse]
    backlinks: list[WikiPageReferenceResponse]


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


class CompileWikiResponse(BaseModel):
    document_id: UUID
    pages_count: int
    sources_count: int
    links_count: int
    pages: list[WikiPageResponse]
