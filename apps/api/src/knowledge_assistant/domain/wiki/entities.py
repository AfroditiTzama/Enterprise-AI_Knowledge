from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


@dataclass
class WikiPage:
    id: UUID
    owner_id: UUID
    document_id: UUID | None
    slug: str
    title: str
    summary: str
    content_markdown: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        owner_id: UUID,
        document_id: UUID | None,
        slug: str,
        title: str,
        summary: str,
        content_markdown: str,
    ) -> "WikiPage":
        cleaned_slug = slug.strip().lower()
        cleaned_title = title.strip()
        cleaned_content = content_markdown.strip()

        if not cleaned_slug:
            raise ValueError("Wiki page slug cannot be empty.")

        if not cleaned_title:
            raise ValueError("Wiki page title cannot be empty.")

        if not cleaned_content:
            raise ValueError("Wiki page content cannot be empty.")

        now = datetime.now(timezone.utc)

        return cls(
            id=uuid4(),
            owner_id=owner_id,
            document_id=document_id,
            slug=cleaned_slug,
            title=cleaned_title,
            summary=summary.strip(),
            content_markdown=cleaned_content,
            created_at=now,
            updated_at=now,
        )

    def update_from_compilation(
        self,
        *,
        slug: str,
        title: str,
        summary: str,
        content_markdown: str,
    ) -> "WikiPage":
        cleaned_slug = slug.strip().lower()
        cleaned_title = title.strip()
        cleaned_content = content_markdown.strip()

        if not cleaned_slug:
            raise ValueError(
                "Wiki page slug cannot be empty."
            )

        if not cleaned_title:
            raise ValueError(
                "Wiki page title cannot be empty."
            )

        if not cleaned_content:
            raise ValueError(
                "Wiki page content cannot be empty."
            )

        return WikiPage(
            id=self.id,
            owner_id=self.owner_id,
            document_id=None,
            slug=cleaned_slug,
            title=cleaned_title,
            summary=summary.strip(),
            content_markdown=cleaned_content,
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
        )


@dataclass(frozen=True)
class WikiPageSource:
    id: UUID
    wiki_page_id: UUID
    chunk_id: UUID
    page_number: int | None

    @classmethod
    def create(
        cls,
        *,
        wiki_page_id: UUID,
        chunk_id: UUID,
        page_number: int | None,
    ) -> "WikiPageSource":
        return cls(
            id=uuid4(),
            wiki_page_id=wiki_page_id,
            chunk_id=chunk_id,
            page_number=page_number,
        )


@dataclass(frozen=True)
class WikiPageLink:
    id: UUID
    source_page_id: UUID
    target_page_id: UUID
    label: str

    @classmethod
    def create(
        cls,
        *,
        source_page_id: UUID,
        target_page_id: UUID,
        label: str,
    ) -> "WikiPageLink":
        return cls(
            id=uuid4(),
            source_page_id=source_page_id,
            target_page_id=target_page_id,
            label=label.strip(),
        )


@dataclass(frozen=True)
class WikiDocumentGraph:
    owner_id: UUID
    document_id: UUID
    pages: tuple[WikiPage, ...]
    sources: tuple[WikiPageSource, ...]
    links: tuple[WikiPageLink, ...]


@dataclass(frozen=True)
class WikiPageSourceReference:
    chunk_id: UUID
    document_id: UUID
    document_filename: str
    chunk_index: int
    page_number: int | None


@dataclass(frozen=True)
class WikiPageReference:
    page_id: UUID
    slug: str
    title: str
    label: str


@dataclass(frozen=True)
class WikiPageDetails:
    page: WikiPage
    sources: tuple[WikiPageSourceReference, ...]
    related_pages: tuple[WikiPageReference, ...]
    backlinks: tuple[WikiPageReference, ...]



class WikiRevisionOperation(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    MERGE = "MERGE"
    RESTORE = "RESTORE"


@dataclass(frozen=True)
class WikiPageRevision:
    id: UUID
    wiki_page_id: UUID | None
    owner_id: UUID
    page_slug: str
    revision_number: int
    title: str
    summary: str
    content_markdown: str
    operation: WikiRevisionOperation
    triggering_document_id: UUID | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        wiki_page_id: UUID | None,
        owner_id: UUID,
        page_slug: str,
        revision_number: int,
        title: str,
        summary: str,
        content_markdown: str,
        operation: WikiRevisionOperation,
        triggering_document_id: UUID | None,
    ) -> "WikiPageRevision":
        cleaned_slug = page_slug.strip().lower()
        cleaned_title = title.strip()
        cleaned_content = content_markdown.strip()

        if not cleaned_slug:
            raise ValueError(
                "Wiki revision page slug cannot be empty."
            )

        if revision_number < 1:
            raise ValueError(
                "Wiki revision number must be positive."
            )

        if not cleaned_title:
            raise ValueError(
                "Wiki revision title cannot be empty."
            )

        if not cleaned_content:
            raise ValueError(
                "Wiki revision content cannot be empty."
            )

        return cls(
            id=uuid4(),
            wiki_page_id=wiki_page_id,
            owner_id=owner_id,
            page_slug=cleaned_slug,
            revision_number=revision_number,
            title=cleaned_title,
            summary=summary.strip(),
            content_markdown=cleaned_content,
            operation=operation,
            triggering_document_id=triggering_document_id,
            created_at=datetime.now(timezone.utc),
        )
