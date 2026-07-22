from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.wiki.entities import (
    WikiConflictStatus,
    WikiDocumentGraph,
    WikiPage,
    WikiPageConflict,
    WikiMaintenanceStatus,
    WikiMaintenanceSuggestion,
    WikiMaintenanceSuggestionDraft,
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
    async def apply_global_compilation(
        self,
        graph: WikiDocumentGraph,
    ) -> None:
        """Create or update owner-scoped global Wiki pages."""
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

    @abstractmethod
    async def restore_revision(
        self,
        *,
        owner_id: UUID,
        slug: str,
        revision_number: int,
    ) -> WikiPage:
        """Restore a historical revision as a new current revision."""
        raise NotImplementedError

    @abstractmethod
    async def update_conflict_status(
        self,
        *,
        owner_id: UUID,
        conflict_id: UUID,
        status: WikiConflictStatus,
        resolution_note: str,
    ) -> WikiPageConflict:
        """Resolve or dismiss one owner-scoped Wiki conflict."""
        raise NotImplementedError

    @abstractmethod
    async def sync_maintenance_suggestions(
        self,
        *,
        owner_id: UUID,
        suggestions: list[WikiMaintenanceSuggestionDraft],
    ) -> list[WikiMaintenanceSuggestion]:
        """Synchronize the active maintenance suggestions for one owner."""
        raise NotImplementedError

    @abstractmethod
    async def list_maintenance_suggestions(
        self,
        *,
        owner_id: UUID,
        status: WikiMaintenanceStatus | None = None,
    ) -> list[WikiMaintenanceSuggestion]:
        """Return owner-scoped Wiki maintenance suggestions."""
        raise NotImplementedError

    @abstractmethod
    async def update_maintenance_suggestion_status(
        self,
        *,
        owner_id: UUID,
        suggestion_id: UUID,
        status: WikiMaintenanceStatus,
    ) -> WikiMaintenanceSuggestion:
        """Approve or reject one maintenance suggestion."""
        raise NotImplementedError
