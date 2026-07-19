import re
from uuid import UUID

from knowledge_assistant.domain.documents.chunk_repository import (
    DocumentChunkRepository,
)
from knowledge_assistant.domain.documents.entities import (
    DocumentStatus,
)
from knowledge_assistant.domain.documents.repository import (
    DocumentRepository,
)
from knowledge_assistant.domain.wiki.compiler import WikiCompiler
from knowledge_assistant.domain.wiki.entities import (
    WikiDocumentGraph,
    WikiPage,
    WikiPageLink,
    WikiPageSource,
)
from knowledge_assistant.domain.wiki.repository import WikiRepository


class CompileDocumentWikiCommand:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        document_chunk_repository: DocumentChunkRepository,
        wiki_repository: WikiRepository,
        wiki_compiler: WikiCompiler,
    ) -> None:
        self._document_repository = document_repository
        self._document_chunk_repository = (
            document_chunk_repository
        )
        self._wiki_repository = wiki_repository
        self._wiki_compiler = wiki_compiler

    async def execute(
        self,
        *,
        document_id: UUID,
        owner_id: UUID,
    ) -> WikiDocumentGraph:
        document = await self._document_repository.get_by_id(
            document_id
        )

        if document is None or document.owner_id != owner_id:
            raise ValueError(
                "Document was not found."
            )

        if document.status != DocumentStatus.PROCESSED:
            raise ValueError(
                "Document must be processed before wiki compilation."
            )

        chunks = (
            await self._document_chunk_repository.list_by_document_id(
                document_id
            )
        )

        if not chunks:
            raise ValueError(
                "The document has no stored chunks."
            )

        compilation = await self._wiki_compiler.compile(
            document_title=document.original_filename,
            chunks=tuple(chunks),
        )

        pages_by_draft_slug: dict[str, WikiPage] = {}

        for draft in compilation.pages:
            draft_slug = draft.slug.strip().lower()

            canonical_slug = self._create_canonical_slug(
                document_id=document.id,
                draft_slug=draft_slug,
            )

            pages_by_draft_slug[draft_slug] = WikiPage.create(
                owner_id=owner_id,
                document_id=document.id,
                slug=canonical_slug,
                title=draft.title,
                summary=draft.summary,
                content_markdown=draft.content_markdown,
            )

        chunks_by_id = {
            chunk.id: chunk
            for chunk in chunks
        }

        sources: list[WikiPageSource] = []

        for draft in compilation.pages:
            wiki_page = pages_by_draft_slug[
                draft.slug.strip().lower()
            ]

            for chunk_id in dict.fromkeys(
                draft.source_chunk_ids
            ):
                chunk = chunks_by_id.get(chunk_id)

                if chunk is None:
                    raise ValueError(
                        "Wiki page references an unknown chunk."
                    )

                sources.append(
                    WikiPageSource.create(
                        wiki_page_id=wiki_page.id,
                        chunk_id=chunk.id,
                        page_number=chunk.page_number,
                    )
                )

        links: list[WikiPageLink] = []
        existing_relationships: set[
            tuple[UUID, UUID]
        ] = set()

        for draft in compilation.pages:
            source_page = pages_by_draft_slug[
                draft.slug.strip().lower()
            ]

            for related_slug in draft.related_page_slugs:
                target_page = pages_by_draft_slug.get(
                    related_slug.strip().lower()
                )

                if target_page is None:
                    continue

                if target_page.id == source_page.id:
                    continue

                relationship_key = (
                    source_page.id,
                    target_page.id,
                )

                if relationship_key in existing_relationships:
                    continue

                existing_relationships.add(
                    relationship_key
                )

                links.append(
                    WikiPageLink.create(
                        source_page_id=source_page.id,
                        target_page_id=target_page.id,
                        label="related",
                    )
                )

        graph = WikiDocumentGraph(
            owner_id=owner_id,
            document_id=document.id,
            pages=tuple(
                pages_by_draft_slug.values()
            ),
            sources=tuple(sources),
            links=tuple(links),
        )

        await self._wiki_repository.replace_for_document(
            graph
        )

        return graph

    @staticmethod
    def _create_canonical_slug(
        *,
        document_id: UUID,
        draft_slug: str,
    ) -> str:
        cleaned_slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            draft_slug.lower(),
        ).strip("-")

        if not cleaned_slug:
            cleaned_slug = "wiki-page"

        return (
            f"{document_id.hex[:8]}-{cleaned_slug}"
        )