from uuid import UUID

from sqlalchemy import (
    delete,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from knowledge_assistant.domain.wiki.entities import (
    WikiDocumentGraph,
    WikiPage,
    WikiPageDetails,
    WikiPageReference,
    WikiPageRevision,
    WikiPageSourceReference,
    WikiRevisionOperation,
)
from knowledge_assistant.domain.wiki.repository import WikiRepository
from knowledge_assistant.infrastructure.database.mappers.wiki_mapper import (
    WikiMapper,
)
from knowledge_assistant.infrastructure.database.models.document import (
    DocumentModel,
)
from knowledge_assistant.infrastructure.database.models.document_chunk import (
    DocumentChunkModel,
)
from knowledge_assistant.infrastructure.database.models.wiki import (
    WikiPageLinkModel,
    WikiPageModel,
    WikiPageRevisionModel,
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
            select(WikiPageModel).where(
                WikiPageModel.owner_id == graph.owner_id,
                WikiPageModel.document_id == graph.document_id,
            )
        )

        existing_page_models = list(
            existing_page_result.scalars().all()
        )

        existing_page_ids = [
            model.id
            for model in existing_page_models
        ]

        tracked_slugs = {
            model.slug
            for model in existing_page_models
        }

        tracked_slugs.update(
            page.slug
            for page in graph.pages
        )

        latest_revision_numbers: dict[str, int] = {}

        if tracked_slugs:
            revision_result = await self._session.execute(
                select(
                    WikiPageRevisionModel.page_slug,
                    func.max(
                        WikiPageRevisionModel.revision_number
                    ).label("max_revision_number"),
                )
                .where(
                    WikiPageRevisionModel.owner_id
                    == graph.owner_id,
                    WikiPageRevisionModel.page_slug.in_(
                        tracked_slugs
                    ),
                )
                .group_by(
                    WikiPageRevisionModel.page_slug
                )
            )

            latest_revision_numbers = {
                row.page_slug: int(
                    row.max_revision_number
                )
                for row in revision_result.all()
            }

        revisions: list[WikiPageRevision] = []

        # Backfill a baseline revision for Wiki pages that
        # existed before revision tracking was introduced.
        for existing_page in existing_page_models:
            if (
                existing_page.slug
                in latest_revision_numbers
            ):
                continue

            baseline_revision = WikiPageRevision.create(
                wiki_page_id=None,
                owner_id=existing_page.owner_id,
                page_slug=existing_page.slug,
                revision_number=1,
                title=existing_page.title,
                summary=existing_page.summary,
                content_markdown=(
                    existing_page.content_markdown
                ),
                operation=WikiRevisionOperation.CREATE,
                triggering_document_id=(
                    existing_page.document_id
                ),
            )

            revisions.append(baseline_revision)

            latest_revision_numbers[
                existing_page.slug
            ] = 1

        if existing_page_ids:
            # Preserve historical rows even when the current
            # page records are replaced.
            await self._session.execute(
                update(WikiPageRevisionModel)
                .where(
                    WikiPageRevisionModel.wiki_page_id.in_(
                        existing_page_ids
                    )
                )
                .values(wiki_page_id=None)
            )

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
                    WikiPageModel.id.in_(
                        existing_page_ids
                    )
                )
            )

        for page in graph.pages:
            latest_revision_number = (
                latest_revision_numbers.get(
                    page.slug
                )
            )

            if latest_revision_number is None:
                revision_number = 1
                operation = WikiRevisionOperation.CREATE
            else:
                revision_number = (
                    latest_revision_number + 1
                )
                operation = WikiRevisionOperation.UPDATE

            revision = WikiPageRevision.create(
                wiki_page_id=page.id,
                owner_id=page.owner_id,
                page_slug=page.slug,
                revision_number=revision_number,
                title=page.title,
                summary=page.summary,
                content_markdown=page.content_markdown,
                operation=operation,
                triggering_document_id=graph.document_id,
            )

            revisions.append(revision)

            latest_revision_numbers[
                page.slug
            ] = revision_number

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

        revision_models = [
            WikiMapper.revision_to_model(revision)
            for revision in revisions
        ]

        self._session.add_all(page_models)
        self._session.add_all(source_models)
        self._session.add_all(link_models)
        self._session.add_all(revision_models)

        await self._session.flush()

    async def apply_global_compilation(
        self,
        graph: WikiDocumentGraph,
    ) -> None:
        self._validate_graph(graph)

        incoming_page_ids = {
            page.id
            for page in graph.pages
        }

        incoming_slugs = {
            page.slug
            for page in graph.pages
        }

        existing_result = await self._session.execute(
            select(WikiPageModel).where(
                WikiPageModel.owner_id
                == graph.owner_id,
                or_(
                    WikiPageModel.id.in_(
                        incoming_page_ids
                    ),
                    WikiPageModel.slug.in_(
                        incoming_slugs
                    ),
                ),
            )
        )

        existing_models = list(
            existing_result.scalars().all()
        )

        existing_by_id = {
            model.id: model
            for model in existing_models
        }

        existing_by_slug = {
            model.slug: model
            for model in existing_models
        }

        revision_slugs = set(incoming_slugs)
        revision_slugs.update(
            model.slug
            for model in existing_models
        )

        latest_revision_numbers: dict[str, int] = {}

        if revision_slugs:
            revision_result = await self._session.execute(
                select(
                    WikiPageRevisionModel.page_slug,
                    func.max(
                        WikiPageRevisionModel.revision_number
                    ).label("max_revision_number"),
                )
                .where(
                    WikiPageRevisionModel.owner_id
                    == graph.owner_id,
                    WikiPageRevisionModel.page_slug.in_(
                        revision_slugs
                    ),
                )
                .group_by(
                    WikiPageRevisionModel.page_slug
                )
            )

            latest_revision_numbers = {
                row.page_slug: int(
                    row.max_revision_number
                )
                for row in revision_result.all()
            }

        revision_models: list[
            WikiPageRevisionModel
        ] = []

        new_page_models: list[WikiPageModel] = []

        for page in graph.pages:
            existing_model = (
                existing_by_id.get(page.id)
                or existing_by_slug.get(page.slug)
            )

            if existing_model is None:
                new_page_models.append(
                    WikiMapper.page_to_model(page)
                )

                latest_number = (
                    latest_revision_numbers.get(
                        page.slug,
                        0,
                    )
                )

                operation = (
                    WikiRevisionOperation.CREATE
                    if latest_number == 0
                    else WikiRevisionOperation.UPDATE
                )

                revision = WikiPageRevision.create(
                    wiki_page_id=page.id,
                    owner_id=page.owner_id,
                    page_slug=page.slug,
                    revision_number=latest_number + 1,
                    title=page.title,
                    summary=page.summary,
                    content_markdown=(
                        page.content_markdown
                    ),
                    operation=operation,
                    triggering_document_id=(
                        graph.document_id
                    ),
                )

                revision_models.append(
                    WikiMapper.revision_to_model(
                        revision
                    )
                )

                latest_revision_numbers[
                    page.slug
                ] = latest_number + 1

                continue

            if existing_model.id != page.id:
                raise ValueError(
                    "Global Wiki page identity mismatch."
                )

            previous_slug = existing_model.slug

            if previous_slug != page.slug:
                target_revision_number = (
                    latest_revision_numbers.get(
                        page.slug,
                        0,
                    )
                )

                if target_revision_number > 0:
                    raise ValueError(
                        "The global Wiki slug already has "
                        "an independent revision history."
                    )

                await self._session.execute(
                    update(WikiPageRevisionModel)
                    .where(
                        WikiPageRevisionModel.owner_id
                        == graph.owner_id,
                        WikiPageRevisionModel.page_slug
                        == previous_slug,
                    )
                    .values(
                        page_slug=page.slug
                    )
                )

                latest_revision_numbers[
                    page.slug
                ] = latest_revision_numbers.pop(
                    previous_slug,
                    0,
                )

            latest_number = (
                latest_revision_numbers.get(
                    page.slug,
                    0,
                )
            )

            if latest_number == 0:
                baseline_revision = (
                    WikiPageRevision.create(
                        wiki_page_id=existing_model.id,
                        owner_id=existing_model.owner_id,
                        page_slug=page.slug,
                        revision_number=1,
                        title=existing_model.title,
                        summary=existing_model.summary,
                        content_markdown=(
                            existing_model.content_markdown
                        ),
                        operation=(
                            WikiRevisionOperation.CREATE
                        ),
                        triggering_document_id=(
                            existing_model.document_id
                        ),
                    )
                )

                revision_models.append(
                    WikiMapper.revision_to_model(
                        baseline_revision
                    )
                )

                latest_number = 1

            has_changed = any(
                (
                    existing_model.slug != page.slug,
                    existing_model.title != page.title,
                    existing_model.summary
                    != page.summary,
                    existing_model.content_markdown
                    != page.content_markdown,
                    existing_model.document_id
                    is not None,
                )
            )

            existing_model.document_id = None
            existing_model.slug = page.slug
            existing_model.title = page.title
            existing_model.summary = page.summary
            existing_model.content_markdown = (
                page.content_markdown
            )
            existing_model.updated_at = page.updated_at

            if has_changed:
                revision = WikiPageRevision.create(
                    wiki_page_id=existing_model.id,
                    owner_id=existing_model.owner_id,
                    page_slug=page.slug,
                    revision_number=latest_number + 1,
                    title=page.title,
                    summary=page.summary,
                    content_markdown=(
                        page.content_markdown
                    ),
                    operation=WikiRevisionOperation.UPDATE,
                    triggering_document_id=(
                        graph.document_id
                    ),
                )

                revision_models.append(
                    WikiMapper.revision_to_model(
                        revision
                    )
                )

                latest_revision_numbers[
                    page.slug
                ] = latest_number + 1

        self._session.add_all(new_page_models)

        await self._session.flush()

        obsolete_result = await self._session.execute(
            select(WikiPageModel.id).where(
                WikiPageModel.owner_id
                == graph.owner_id,
                WikiPageModel.document_id
                == graph.document_id,
                ~WikiPageModel.id.in_(
                    incoming_page_ids
                ),
            )
        )

        obsolete_page_ids = list(
            obsolete_result.scalars().all()
        )

        if obsolete_page_ids:
            await self._session.execute(
                update(WikiPageRevisionModel)
                .where(
                    WikiPageRevisionModel.wiki_page_id.in_(
                        obsolete_page_ids
                    )
                )
                .values(wiki_page_id=None)
            )

            await self._session.execute(
                delete(WikiPageLinkModel).where(
                    or_(
                        WikiPageLinkModel.source_page_id.in_(
                            obsolete_page_ids
                        ),
                        WikiPageLinkModel.target_page_id.in_(
                            obsolete_page_ids
                        ),
                    )
                )
            )

            await self._session.execute(
                delete(WikiPageSourceModel).where(
                    WikiPageSourceModel.wiki_page_id.in_(
                        obsolete_page_ids
                    )
                )
            )

            await self._session.execute(
                delete(WikiPageModel).where(
                    WikiPageModel.id.in_(
                        obsolete_page_ids
                    )
                )
            )

        document_chunk_result = await self._session.execute(
            select(DocumentChunkModel.id).where(
                DocumentChunkModel.document_id
                == graph.document_id
            )
        )

        document_chunk_ids = list(
            document_chunk_result.scalars().all()
        )

        if document_chunk_ids and incoming_page_ids:
            await self._session.execute(
                delete(WikiPageSourceModel).where(
                    WikiPageSourceModel.wiki_page_id.in_(
                        incoming_page_ids
                    ),
                    WikiPageSourceModel.chunk_id.in_(
                        document_chunk_ids
                    ),
                )
            )

        source_models = [
            WikiMapper.source_to_model(source)
            for source in graph.sources
        ]

        existing_link_result = await self._session.execute(
            select(
                WikiPageLinkModel.source_page_id,
                WikiPageLinkModel.target_page_id,
                WikiPageLinkModel.label,
            ).where(
                WikiPageLinkModel.source_page_id.in_(
                    incoming_page_ids
                )
            )
        )

        existing_link_keys = {
            (
                row.source_page_id,
                row.target_page_id,
                row.label,
            )
            for row in existing_link_result.all()
        }

        link_models = [
            WikiMapper.link_to_model(link)
            for link in graph.links
            if (
                link.source_page_id,
                link.target_page_id,
                link.label,
            )
            not in existing_link_keys
        ]

        self._session.add_all(revision_models)
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
                WikiPageModel.slug
                == slug.strip().lower(),
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return WikiMapper.page_to_domain(model)

    async def get_details_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> WikiPageDetails | None:
        page = await self.get_by_slug(
            owner_id=owner_id,
            slug=slug,
        )

        if page is None:
            return None

        sources = await self._list_page_sources(
            owner_id=owner_id,
            page_id=page.id,
        )

        related_pages = await self._list_related_pages(
            owner_id=owner_id,
            page_id=page.id,
        )

        backlinks = await self._list_backlinks(
            owner_id=owner_id,
            page_id=page.id,
        )

        return WikiPageDetails(
            page=page,
            sources=sources,
            related_pages=related_pages,
            backlinks=backlinks,
        )

    async def list_revisions_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> list[WikiPageRevision]:
        result = await self._session.execute(
            select(WikiPageRevisionModel)
            .where(
                WikiPageRevisionModel.owner_id
                == owner_id,
                WikiPageRevisionModel.page_slug
                == slug.strip().lower(),
            )
            .order_by(
                WikiPageRevisionModel.revision_number.desc()
            )
        )

        return [
            WikiMapper.revision_to_domain(model)
            for model in result.scalars().all()
        ]

    async def _list_page_sources(
        self,
        *,
        owner_id: UUID,
        page_id: UUID,
    ) -> tuple[WikiPageSourceReference, ...]:
        result = await self._session.execute(
            select(
                WikiPageSourceModel.chunk_id.label(
                    "chunk_id"
                ),
                DocumentChunkModel.document_id.label(
                    "document_id"
                ),
                DocumentModel.original_filename.label(
                    "document_filename"
                ),
                DocumentChunkModel.chunk_index.label(
                    "chunk_index"
                ),
                WikiPageSourceModel.page_number.label(
                    "source_page_number"
                ),
                DocumentChunkModel.page_number.label(
                    "chunk_page_number"
                ),
            )
            .join(
                DocumentChunkModel,
                DocumentChunkModel.id
                == WikiPageSourceModel.chunk_id,
            )
            .join(
                DocumentModel,
                DocumentModel.id
                == DocumentChunkModel.document_id,
            )
            .where(
                WikiPageSourceModel.wiki_page_id
                == page_id,
                DocumentModel.owner_id == owner_id,
            )
            .order_by(
                DocumentModel.original_filename.asc(),
                DocumentChunkModel.chunk_index.asc(),
            )
        )

        references: list[WikiPageSourceReference] = []

        for row in result.all():
            page_number = (
                row.source_page_number
                if row.source_page_number is not None
                else row.chunk_page_number
            )

            references.append(
                WikiPageSourceReference(
                    chunk_id=row.chunk_id,
                    document_id=row.document_id,
                    document_filename=(
                        row.document_filename
                    ),
                    chunk_index=row.chunk_index,
                    page_number=page_number,
                )
            )

        return tuple(references)

    async def _list_related_pages(
        self,
        *,
        owner_id: UUID,
        page_id: UUID,
    ) -> tuple[WikiPageReference, ...]:
        target_page = aliased(WikiPageModel)

        result = await self._session.execute(
            select(
                target_page.id.label("page_id"),
                target_page.slug.label("slug"),
                target_page.title.label("title"),
                WikiPageLinkModel.label.label(
                    "link_label"
                ),
            )
            .join(
                target_page,
                target_page.id
                == WikiPageLinkModel.target_page_id,
            )
            .where(
                WikiPageLinkModel.source_page_id
                == page_id,
                target_page.owner_id == owner_id,
                target_page.id != page_id,
            )
            .order_by(
                target_page.title.asc(),
            )
        )

        return tuple(
            WikiPageReference(
                page_id=row.page_id,
                slug=row.slug,
                title=row.title,
                label=(
                    row.link_label.strip()
                    or "related"
                ),
            )
            for row in result.all()
        )

    async def _list_backlinks(
        self,
        *,
        owner_id: UUID,
        page_id: UUID,
    ) -> tuple[WikiPageReference, ...]:
        source_page = aliased(WikiPageModel)

        result = await self._session.execute(
            select(
                source_page.id.label("page_id"),
                source_page.slug.label("slug"),
                source_page.title.label("title"),
                WikiPageLinkModel.label.label(
                    "link_label"
                ),
            )
            .join(
                source_page,
                source_page.id
                == WikiPageLinkModel.source_page_id,
            )
            .where(
                WikiPageLinkModel.target_page_id
                == page_id,
                source_page.owner_id == owner_id,
                source_page.id != page_id,
            )
            .order_by(
                source_page.title.asc(),
            )
        )

        return tuple(
            WikiPageReference(
                page_id=row.page_id,
                slug=row.slug,
                title=row.title,
                label=(
                    row.link_label.strip()
                    or "related"
                ),
            )
            for row in result.all()
        )

    @staticmethod
    def _validate_graph(
        graph: WikiDocumentGraph,
    ) -> None:
        page_ids = {
            page.id
            for page in graph.pages
        }

        for page in graph.pages:
            if page.owner_id != graph.owner_id:
                raise ValueError(
                    "Wiki page owner does not match graph owner."
                )

            if page.document_id not in {
                None,
                graph.document_id,
            }:
                raise ValueError(
                    "Wiki page document does not match graph document."
                )

        for source in graph.sources:
            if source.wiki_page_id not in page_ids:
                raise ValueError(
                    "Wiki source references an unknown Wiki page."
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
