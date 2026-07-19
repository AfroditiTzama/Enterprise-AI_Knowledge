from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_assistant.domain.wiki.entities import (
    WikiDocumentGraph,
    WikiPage,
)
from knowledge_assistant.domain.wiki.repository import WikiRepository
from knowledge_assistant.infrastructure.database.mappers.wiki_mapper import (
    WikiMapper,
)
from knowledge_assistant.infrastructure.database.models.wiki import (
    WikiPageLinkModel,
    WikiPageModel,
    WikiPageSourceModel,
)


class SQLAlchemyWikiRepository(WikiRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def replace_for_document(
        self,
        graph: WikiDocumentGraph,
    ) -> None:
        self._validate_graph(graph)

        existing_page_result = await self._session.execute(
            select(WikiPageModel.id).where(
                WikiPageModel.owner_id == graph.owner_id,
                WikiPageModel.document_id == graph.document_id,
            )
        )

        existing_page_ids = list(
            existing_page_result.scalars().all()
        )

        if existing_page_ids:
            await self._session.execute(
                delete(WikiPageLinkModel).where(
                    or_(
                        WikiPageLinkModel.source_page_id.in_(
                            existing_page_ids
                        ),
                        WikiPageLinkModel.target_page_id.in_(
                            existing_page_ids
                        ),
                    )
                )
            )

            await self._session.execute(
                delete(WikiPageSourceModel).where(
                    WikiPageSourceModel.wiki_page_id.in_(
                        existing_page_ids
                    )
                )
            )

            await self._session.execute(
                delete(WikiPageModel).where(
                    WikiPageModel.id.in_(existing_page_ids)
                )
            )

        page_models = [
            WikiMapper.page_to_model(page)
            for page in graph.pages
        ]

        source_models = [
            WikiMapper.source_to_model(source)
            for source in graph.sources
        ]

        link_models = [
            WikiMapper.link_to_model(link)
            for link in graph.links
        ]

        self._session.add_all(page_models)
        self._session.add_all(source_models)
        self._session.add_all(link_models)

        await self._session.flush()

    async def list_by_owner_id(
        self,
        owner_id: UUID,
    ) -> list[WikiPage]:
        result = await self._session.execute(
            select(WikiPageModel)
            .where(
                WikiPageModel.owner_id == owner_id,
            )
            .order_by(
                WikiPageModel.title.asc(),
            )
        )

        return [
            WikiMapper.page_to_domain(model)
            for model in result.scalars().all()
        ]

    async def list_by_document_id(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
    ) -> list[WikiPage]:
        result = await self._session.execute(
            select(WikiPageModel)
            .where(
                WikiPageModel.owner_id == owner_id,
                WikiPageModel.document_id == document_id,
            )
            .order_by(
                WikiPageModel.title.asc(),
            )
        )

        return [
            WikiMapper.page_to_domain(model)
            for model in result.scalars().all()
        ]

    async def get_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> WikiPage | None:
        result = await self._session.execute(
            select(WikiPageModel).where(
                WikiPageModel.owner_id == owner_id,
                WikiPageModel.slug == slug.strip().lower(),
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return WikiMapper.page_to_domain(model)

    @staticmethod
    def _validate_graph(
        graph: WikiDocumentGraph,
    ) -> None:
        page_ids = {page.id for page in graph.pages}

        for page in graph.pages:
            if page.owner_id != graph.owner_id:
                raise ValueError(
                    "Wiki page owner does not match graph owner."
                )

            if page.document_id != graph.document_id:
                raise ValueError(
                    "Wiki page document does not match graph document."
                )

        for source in graph.sources:
            if source.wiki_page_id not in page_ids:
                raise ValueError(
                    "Wiki source references an unknown wiki page."
                )

        for link in graph.links:
            if link.source_page_id not in page_ids:
                raise ValueError(
                    "Wiki link has an unknown source page."
                )

            if link.target_page_id not in page_ids:
                raise ValueError(
                    "Wiki link has an unknown target page."
                )