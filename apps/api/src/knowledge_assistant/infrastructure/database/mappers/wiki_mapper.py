import json
from uuid import UUID

from knowledge_assistant.domain.wiki.entities import (
    WikiClaimCitation,
    WikiConflictStatus,
    WikiMaintenanceIssueType,
    WikiMaintenanceStatus,
    WikiMaintenanceSuggestion,
    WikiPage,
    WikiPageConflict,
    WikiPageLink,
    WikiPageRevision,
    WikiPageSource,
    WikiRevisionOperation,
)
from knowledge_assistant.infrastructure.database.models.wiki import (
    WikiClaimCitationModel,
    WikiMaintenanceSuggestionModel,
    WikiPageConflictModel,
    WikiPageLinkModel,
    WikiPageModel,
    WikiPageRevisionModel,
    WikiPageSourceModel,
)


class WikiMapper:
    @staticmethod
    def page_to_model(page: WikiPage) -> WikiPageModel:
        return WikiPageModel(
            id=page.id,
            owner_id=page.owner_id,
            document_id=page.document_id,
            slug=page.slug,
            title=page.title,
            summary=page.summary,
            content_markdown=page.content_markdown,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

    @staticmethod
    def page_to_domain(model: WikiPageModel) -> WikiPage:
        return WikiPage(
            id=model.id,
            owner_id=model.owner_id,
            document_id=model.document_id,
            slug=model.slug,
            title=model.title,
            summary=model.summary,
            content_markdown=model.content_markdown,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def source_to_model(
        source: WikiPageSource,
    ) -> WikiPageSourceModel:
        return WikiPageSourceModel(
            id=source.id,
            wiki_page_id=source.wiki_page_id,
            chunk_id=source.chunk_id,
            page_number=source.page_number,
        )

    @staticmethod
    def link_to_model(
        link: WikiPageLink,
    ) -> WikiPageLinkModel:
        return WikiPageLinkModel(
            id=link.id,
            source_page_id=link.source_page_id,
            target_page_id=link.target_page_id,
            label=link.label,
        )

    @staticmethod
    def revision_to_model(
        revision: WikiPageRevision,
    ) -> WikiPageRevisionModel:
        return WikiPageRevisionModel(
            id=revision.id,
            wiki_page_id=revision.wiki_page_id,
            owner_id=revision.owner_id,
            page_slug=revision.page_slug,
            revision_number=revision.revision_number,
            title=revision.title,
            summary=revision.summary,
            content_markdown=revision.content_markdown,
            operation=revision.operation.value,
            triggering_document_id=(
                revision.triggering_document_id
            ),
            created_at=revision.created_at,
        )

    @staticmethod
    def revision_to_domain(
        model: WikiPageRevisionModel,
    ) -> WikiPageRevision:
        return WikiPageRevision(
            id=model.id,
            wiki_page_id=model.wiki_page_id,
            owner_id=model.owner_id,
            page_slug=model.page_slug,
            revision_number=model.revision_number,
            title=model.title,
            summary=model.summary,
            content_markdown=model.content_markdown,
            operation=WikiRevisionOperation(
                model.operation
            ),
            triggering_document_id=(
                model.triggering_document_id
            ),
            created_at=model.created_at,
        )

    @staticmethod
    def conflict_to_model(
        conflict: WikiPageConflict,
    ) -> WikiPageConflictModel:
        return WikiPageConflictModel(
            id=conflict.id,
            owner_id=conflict.owner_id,
            wiki_page_id=conflict.wiki_page_id,
            source_document_id=conflict.source_document_id,
            existing_statement=conflict.existing_statement,
            incoming_statement=conflict.incoming_statement,
            explanation=conflict.explanation,
            status=conflict.status.value,
            resolution_note=conflict.resolution_note,
            created_at=conflict.created_at,
            resolved_at=conflict.resolved_at,
        )

    @staticmethod
    def conflict_to_domain(
        model: WikiPageConflictModel,
    ) -> WikiPageConflict:
        return WikiPageConflict(
            id=model.id,
            owner_id=model.owner_id,
            wiki_page_id=model.wiki_page_id,
            source_document_id=model.source_document_id,
            existing_statement=model.existing_statement,
            incoming_statement=model.incoming_statement,
            explanation=model.explanation,
            status=WikiConflictStatus(model.status),
            resolution_note=model.resolution_note,
            created_at=model.created_at,
            resolved_at=model.resolved_at,
        )

    @staticmethod
    def claim_citation_to_model(
        citation: WikiClaimCitation,
    ) -> WikiClaimCitationModel:
        return WikiClaimCitationModel(
            id=citation.id,
            owner_id=citation.owner_id,
            wiki_page_id=citation.wiki_page_id,
            chunk_id=citation.chunk_id,
            claim_key=citation.claim_key,
            claim_text=citation.claim_text,
            position=citation.position,
            created_at=citation.created_at,
        )

    @staticmethod
    def maintenance_to_domain(
        model: WikiMaintenanceSuggestionModel,
    ) -> WikiMaintenanceSuggestion:
        return WikiMaintenanceSuggestion(
            id=model.id,
            owner_id=model.owner_id,
            issue_type=WikiMaintenanceIssueType(model.issue_type),
            status=WikiMaintenanceStatus(model.status),
            fingerprint=model.fingerprint,
            title=model.title,
            description=model.description,
            page_ids=tuple(
                UUID(value)
                for value in json.loads(model.page_ids_json)
            ),
            metadata=dict(json.loads(model.metadata_json)),
            confidence=float(model.confidence),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

