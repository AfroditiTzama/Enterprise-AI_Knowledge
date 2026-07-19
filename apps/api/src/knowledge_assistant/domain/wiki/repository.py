from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.wiki.entities import (
    WikiDocumentGraph,
    WikiPage,
)


class WikiRepository(ABC):
    @abstractmethod
    async def replace_for_document(
        self,
        graph: WikiDocumentGraph,
    ) -> None:
        """Replace the complete wiki graph for a document."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_owner_id(
        self,
        owner_id: UUID,
    ) -> list[WikiPage]:
        """Return all wiki pages owned by a user."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_document_id(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
    ) -> list[WikiPage]:
        """Return the wiki pages generated from one document."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> WikiPage | None:
        """Return one wiki page by its owner-scoped slug."""
        raise NotImplementedError