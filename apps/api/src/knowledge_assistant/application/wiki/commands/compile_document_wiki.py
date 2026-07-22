import logging
import re
from uuid import UUID

from knowledge_assistant.domain.documents.chunk_repository import (
    DocumentChunkRepository,
)
from knowledge_assistant.domain.documents.entities import DocumentStatus
from knowledge_assistant.domain.documents.repository import DocumentRepository
from knowledge_assistant.domain.wiki.compiler import (
    WikiClaimDraft,
    WikiCompiler,
    WikiPageDraft,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiClaimCitation,
    WikiDocumentGraph,
    WikiPage,
    WikiPageConflict,
    WikiPageLink,
    WikiPageRevisionHint,
    WikiPageSource,
    WikiRevisionOperation,
)
from knowledge_assistant.domain.wiki.matcher import (
    WikiMatchDecision,
    WikiSemanticMatcher,
)
from knowledge_assistant.domain.wiki.merger import WikiPageMerger
from knowledge_assistant.domain.wiki.repository import WikiRepository


logger = logging.getLogger(__name__)


class CompileDocumentWikiCommand:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        document_chunk_repository: DocumentChunkRepository,
        wiki_repository: WikiRepository,
        wiki_compiler: WikiCompiler,
        wiki_semantic_matcher: WikiSemanticMatcher,
        wiki_page_merger: WikiPageMerger,
    ) -> None:
        self._document_repository = document_repository
        self._document_chunk_repository = document_chunk_repository
        self._wiki_repository = wiki_repository
        self._wiki_compiler = wiki_compiler
        self._wiki_semantic_matcher = wiki_semantic_matcher
        self._wiki_page_merger = wiki_page_merger

    async def execute(
        self,
        *,
        document_id: UUID,
        owner_id: UUID,
    ) -> WikiDocumentGraph:
        document = await self._document_repository.get_by_id(document_id)

        if document is None or document.owner_id != owner_id:
            raise ValueError("Document was not found.")

        if document.status != DocumentStatus.PROCESSED:
            raise ValueError(
                "Document must be processed before wiki compilation."
            )

        chunks = await self._document_chunk_repository.list_by_document_id(
            document_id
        )

        if not chunks:
            raise ValueError("The document has no stored chunks.")

        compilation = await self._wiki_compiler.compile(
            document_title=document.original_filename,
            chunks=tuple(chunks),
        )
        compiled_drafts = tuple(
            self._namespace_draft_citations(
                draft=draft,
                document_id=document.id,
            )
            for draft in compilation.pages
        )

        existing_pages = await self._wiki_repository.list_by_owner_id(
            owner_id
        )
        existing_by_id = {page.id: page for page in existing_pages}
        existing_by_slug = {page.slug: page for page in existing_pages}

        semantic_matches = await self._wiki_semantic_matcher.match(
            drafts=compiled_drafts,
            existing_pages=tuple(existing_pages),
        )
        matches_by_draft_slug = {
            match.draft_slug: match for match in semantic_matches
        }

        for semantic_match in semantic_matches:
            logger.info(
                (
                    "Wiki semantic decision: draft=%s decision=%s "
                    "candidate=%s score=%s"
                ),
                semantic_match.draft_slug,
                semantic_match.decision.value,
                semantic_match.matched_page_slug,
                (
                    f"{semantic_match.score:.4f}"
                    if semantic_match.score is not None
                    else "n/a"
                ),
            )

        legacy_prefix = f"{document.id.hex[:8]}-"
        legacy_pages_by_global_slug = {
            page.slug[len(legacy_prefix) :]: page
            for page in existing_pages
            if page.document_id == document.id
            and page.slug.startswith(legacy_prefix)
        }

        pages_by_draft_slug: dict[str, WikiPage] = {}
        working_pages_by_id = dict(existing_by_id)
        conflicts: list[WikiPageConflict] = []
        revision_hints_by_page_id: dict[UUID, WikiPageRevisionHint] = {}
        generated_draft_slugs: set[str] = set()

        for draft in compiled_drafts:
            draft_slug = draft.slug.strip().lower()

            if draft_slug in generated_draft_slugs:
                raise ValueError(
                    "Wiki compilation produced duplicate page slugs."
                )
            generated_draft_slugs.add(draft_slug)

            global_slug = self._create_global_slug(draft_slug=draft_slug)
            match = matches_by_draft_slug.get(draft_slug)

            existing_page: WikiPage | None = None
            final_slug = global_slug

            if match is not None and match.matched_page_id is not None:
                existing_page = working_pages_by_id.get(
                    match.matched_page_id
                )
                if existing_page is None:
                    existing_page = existing_by_id.get(
                        match.matched_page_id
                    )

                if (
                    match.decision
                    == WikiMatchDecision.SEMANTIC_CANDIDATE
                    and existing_page is not None
                ):
                    final_slug = existing_page.slug

            if existing_page is None:
                existing_page = (
                    existing_by_slug.get(global_slug)
                    or legacy_pages_by_global_slug.get(global_slug)
                )

            if existing_page is None:
                wiki_page = WikiPage.create(
                    owner_id=owner_id,
                    document_id=None,
                    slug=final_slug,
                    title=draft.title,
                    summary=draft.summary,
                    content_markdown=draft.content_markdown,
                )
                revision_hints_by_page_id[wiki_page.id] = (
                    WikiPageRevisionHint(
                        page_id=wiki_page.id,
                        operation=WikiRevisionOperation.CREATE,
                    )
                )
            else:
                current_page = working_pages_by_id.get(
                    existing_page.id,
                    existing_page,
                )
                merge_result = await self._wiki_page_merger.merge(
                    existing_page=current_page,
                    incoming_draft=draft,
                    document_title=document.original_filename,
                )
                wiki_page = current_page.update_from_compilation(
                    slug=final_slug,
                    title=merge_result.title,
                    summary=merge_result.summary,
                    content_markdown=merge_result.content_markdown,
                )
                revision_hints_by_page_id[wiki_page.id] = (
                    WikiPageRevisionHint(
                        page_id=wiki_page.id,
                        operation=WikiRevisionOperation.MERGE,
                    )
                )

                for conflict in merge_result.conflicts:
                    conflicts.append(
                        WikiPageConflict.create(
                            owner_id=owner_id,
                            wiki_page_id=wiki_page.id,
                            source_document_id=document.id,
                            existing_statement=(
                                conflict.existing_statement
                            ),
                            incoming_statement=(
                                conflict.incoming_statement
                            ),
                            explanation=conflict.explanation,
                        )
                    )

            working_pages_by_id[wiki_page.id] = wiki_page
            pages_by_draft_slug[draft_slug] = wiki_page

        chunks_by_id = {chunk.id: chunk for chunk in chunks}
        sources: list[WikiPageSource] = []
        source_keys: set[tuple[UUID, UUID]] = set()

        for draft in compiled_drafts:
            wiki_page = pages_by_draft_slug[draft.slug.strip().lower()]

            for chunk_id in dict.fromkeys(draft.source_chunk_ids):
                chunk = chunks_by_id.get(chunk_id)

                if chunk is None:
                    raise ValueError(
                        "Wiki page references an unknown chunk."
                    )

                source_key = (wiki_page.id, chunk.id)
                if source_key in source_keys:
                    continue
                source_keys.add(source_key)

                sources.append(
                    WikiPageSource.create(
                        wiki_page_id=wiki_page.id,
                        chunk_id=chunk.id,
                        page_number=chunk.page_number,
                    )
                )

        claim_citations: list[WikiClaimCitation] = []
        claim_citation_keys: set[tuple[UUID, str, UUID]] = set()

        for draft in compiled_drafts:
            wiki_page = pages_by_draft_slug[draft.slug.strip().lower()]

            for position, claim in enumerate(draft.claims):
                for chunk_id in claim.source_chunk_ids:
                    chunk = chunks_by_id.get(chunk_id)
                    if chunk is None:
                        raise ValueError(
                            "Wiki claim references an unknown chunk."
                        )

                    citation_key = (
                        wiki_page.id,
                        claim.claim_key,
                        chunk_id,
                    )
                    if citation_key in claim_citation_keys:
                        continue
                    claim_citation_keys.add(citation_key)

                    claim_citations.append(
                        WikiClaimCitation.create(
                            owner_id=owner_id,
                            wiki_page_id=wiki_page.id,
                            chunk_id=chunk_id,
                            claim_key=claim.claim_key,
                            claim_text=claim.claim_text,
                            position=position,
                        )
                    )

        links: list[WikiPageLink] = []
        relationship_keys: set[tuple[UUID, UUID]] = set()

        for draft in compiled_drafts:
            source_page = pages_by_draft_slug[draft.slug.strip().lower()]

            for related_slug in draft.related_page_slugs:
                normalized_related_slug = related_slug.strip().lower()
                target_page = pages_by_draft_slug.get(
                    normalized_related_slug
                )

                if target_page is None or target_page.id == source_page.id:
                    continue

                relationship_key = (source_page.id, target_page.id)
                if relationship_key in relationship_keys:
                    continue
                relationship_keys.add(relationship_key)

                links.append(
                    WikiPageLink.create(
                        source_page_id=source_page.id,
                        target_page_id=target_page.id,
                        label="related",
                    )
                )

        unique_pages = tuple(
            {page.id: page for page in pages_by_draft_slug.values()}.values()
        )

        graph = WikiDocumentGraph(
            owner_id=owner_id,
            document_id=document.id,
            pages=unique_pages,
            sources=tuple(sources),
            links=tuple(links),
            conflicts=tuple(conflicts),
            claim_citations=tuple(claim_citations),
            revision_hints=tuple(revision_hints_by_page_id.values()),
        )

        await self._wiki_repository.apply_global_compilation(graph)
        return graph

    @staticmethod
    def _create_global_slug(*, draft_slug: str) -> str:
        cleaned_slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            draft_slug.lower(),
        ).strip("-")

        if not cleaned_slug:
            return "wiki-page"

        return cleaned_slug

    @staticmethod
    def _namespace_draft_citations(
        *,
        draft: WikiPageDraft,
        document_id: UUID,
    ) -> WikiPageDraft:
        slug_namespace = re.sub(
            r"[^a-z0-9]+",
            "-",
            draft.slug.strip().lower(),
        ).strip("-")[:32]
        namespace = (
            f"{document_id.hex[:8]}-{slug_namespace}"
            if slug_namespace
            else document_id.hex[:8]
        )
        claim_key_map: dict[str, str] = {}
        claims: list[WikiClaimDraft] = []

        for claim in draft.claims:
            original_key = claim.claim_key.strip().lower()
            if not original_key:
                continue

            namespaced_key = f"{namespace}-{original_key}"
            claim_key_map[original_key] = namespaced_key
            claims.append(
                WikiClaimDraft(
                    claim_key=namespaced_key,
                    claim_text=claim.claim_text,
                    source_chunk_ids=claim.source_chunk_ids,
                )
            )

        content = draft.content_markdown
        for original_key, namespaced_key in claim_key_map.items():
            pattern = re.compile(
                rf"(\]\(citation:)({re.escape(original_key)})(\))",
                re.IGNORECASE,
            )
            content = pattern.sub(
                lambda match: (
                    f"{match.group(1)}{namespaced_key}{match.group(3)}"
                ),
                content,
            )

        return WikiPageDraft(
            title=draft.title,
            slug=draft.slug,
            summary=draft.summary,
            content_markdown=content,
            source_chunk_ids=draft.source_chunk_ids,
            related_page_slugs=draft.related_page_slugs,
            claims=tuple(claims),
        )
