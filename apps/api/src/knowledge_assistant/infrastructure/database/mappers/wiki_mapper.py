from knowledge_assistant.domain.wiki.entities import (
    WikiPage,
    WikiPageLink,
    WikiPageSource,
)
from knowledge_assistant.infrastructure.database.models.wiki import (
    WikiPageLinkModel,
    WikiPageModel,
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