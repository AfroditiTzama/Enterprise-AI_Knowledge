from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WikiPageResponse(BaseModel):
    id: UUID
    document_id: UUID
    slug: str
    title: str
    summary: str
    content_markdown: str
    created_at: datetime
    updated_at: datetime


class CompileWikiResponse(BaseModel):
    document_id: UUID
    pages_count: int
    sources_count: int
    links_count: int
    pages: list[WikiPageResponse]   