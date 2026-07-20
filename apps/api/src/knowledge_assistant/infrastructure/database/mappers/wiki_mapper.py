from knowledge_assistant.domain.wiki.entities import (
    WikiPage,
    WikiPageLink,
    WikiPageRevision,
    WikiPageSource,
    WikiRevisionOperation,
)
from knowledge_assistant.infrastructure.database.models.wiki import (
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
