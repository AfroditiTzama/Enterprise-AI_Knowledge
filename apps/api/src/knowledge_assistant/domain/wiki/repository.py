from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.wiki.entities import (
    WikiDocumentGraph,
    WikiPage,
    WikiPageDetails,
    WikiPageRevision,
)


class WikiRepository(ABC):
    @abstractmethod
    async def replace_for_document(
        self,
        graph: WikiDocumentGraph,
    ) -> None:
        """Replace the complete Wiki graph for a document."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_owner_id(
        self,
        owner_id: UUID,
    ) -> list[WikiPage]:
        """Return all Wiki pages owned by a user."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_document_id(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
    ) -> list[WikiPage]:
        """Return Wiki pages generated from one document."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> WikiPage | None:
        """Return one Wiki page by its owner-scoped slug."""
        raise NotImplementedError

    @abstractmethod
    async def get_details_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> WikiPageDetails | None:
        """Return a Wiki page with sources and relationships."""
        raise NotImplementedError

    @abstractmethod
    async def list_revisions_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> list[WikiPageRevision]:
        """Return the revision history of one Wiki page."""
        raise NotImplementedError
