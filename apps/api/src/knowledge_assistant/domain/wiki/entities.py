from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
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


class WikiConflictStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


@dataclass(frozen=True)
class WikiPageConflict:
    id: UUID
    owner_id: UUID
    wiki_page_id: UUID
    source_document_id: UUID | None
    existing_statement: str
    incoming_statement: str
    explanation: str
    status: WikiConflictStatus
    resolution_note: str
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def create(
        cls,
        *,
        owner_id: UUID,
        wiki_page_id: UUID,
        source_document_id: UUID | None,
        existing_statement: str,
        incoming_statement: str,
        explanation: str,
    ) -> "WikiPageConflict":
        existing = existing_statement.strip()
        incoming = incoming_statement.strip()
        cleaned_explanation = explanation.strip()

        if not existing or not incoming:
            raise ValueError(
                "Wiki conflict statements cannot be empty."
            )

        return cls(
            id=uuid4(),
            owner_id=owner_id,
            wiki_page_id=wiki_page_id,
            source_document_id=source_document_id,
            existing_statement=existing,
            incoming_statement=incoming,
            explanation=cleaned_explanation,
            status=WikiConflictStatus.OPEN,
            resolution_note="",
            created_at=datetime.now(timezone.utc),
            resolved_at=None,
        )


@dataclass(frozen=True)
class WikiPageRevisionHint:
    page_id: UUID
    operation: "WikiRevisionOperation"


@dataclass(frozen=True)
class WikiClaimCitation:
    id: UUID
    owner_id: UUID
    wiki_page_id: UUID
    chunk_id: UUID
    claim_key: str
    claim_text: str
    position: int
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        owner_id: UUID,
        wiki_page_id: UUID,
        chunk_id: UUID,
        claim_key: str,
        claim_text: str,
        position: int,
    ) -> "WikiClaimCitation":
        cleaned_key = claim_key.strip().lower()
        cleaned_text = claim_text.strip()

        if not cleaned_key:
            raise ValueError("Wiki claim key cannot be empty.")

        if not cleaned_text:
            raise ValueError("Wiki claim text cannot be empty.")

        if position < 0:
            raise ValueError("Wiki claim position cannot be negative.")

        return cls(
            id=uuid4(),
            owner_id=owner_id,
            wiki_page_id=wiki_page_id,
            chunk_id=chunk_id,
            claim_key=cleaned_key,
            claim_text=cleaned_text,
            position=position,
            created_at=datetime.now(timezone.utc),
        )


@dataclass(frozen=True)
class WikiDocumentGraph:
    owner_id: UUID
    document_id: UUID
    pages: tuple[WikiPage, ...]
    sources: tuple[WikiPageSource, ...]
    links: tuple[WikiPageLink, ...]
    conflicts: tuple[WikiPageConflict, ...] = ()
    claim_citations: tuple[WikiClaimCitation, ...] = ()
    revision_hints: tuple[WikiPageRevisionHint, ...] = ()


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
class WikiClaimReference:
    claim_key: str
    claim_text: str
    position: int
    sources: tuple[WikiPageSourceReference, ...]


@dataclass(frozen=True)
class WikiQualityScore:
    source_coverage: int
    freshness: int
    consistency: int
    connectivity: int
    overall: int
    supported_claims: int
    unsupported_claims: int
    open_conflicts: int
    connections_count: int
    issues: tuple[str, ...]


class WikiMaintenanceIssueType(str, Enum):
    DUPLICATE = "DUPLICATE"
    ORPHAN = "ORPHAN"
    BROKEN_LINK = "BROKEN_LINK"
    OVERSIZED = "OVERSIZED"
    UNDERSIZED = "UNDERSIZED"
    UNSUPPORTED_CLAIMS = "UNSUPPORTED_CLAIMS"


class WikiMaintenanceStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class WikiMaintenanceSuggestion:
    id: UUID
    owner_id: UUID
    issue_type: WikiMaintenanceIssueType
    status: WikiMaintenanceStatus
    fingerprint: str
    title: str
    description: str
    page_ids: tuple[UUID, ...]
    metadata: dict[str, Any]
    confidence: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WikiMaintenanceSuggestionDraft:
    issue_type: WikiMaintenanceIssueType
    fingerprint: str
    title: str
    description: str
    page_ids: tuple[UUID, ...]
    metadata: dict[str, Any]
    confidence: float


@dataclass(frozen=True)
class WikiPageDetails:
    page: WikiPage
    sources: tuple[WikiPageSourceReference, ...]
    related_pages: tuple[WikiPageReference, ...]
    backlinks: tuple[WikiPageReference, ...]
    conflicts: tuple[WikiPageConflict, ...] = ()
    claim_citations: tuple[WikiClaimReference, ...] = ()
    quality: WikiQualityScore | None = None


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
