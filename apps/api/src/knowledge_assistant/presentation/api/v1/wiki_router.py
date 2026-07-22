from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_assistant.application.wiki.queries.get_revision_diff import (
    GetWikiRevisionDiffQuery,
)
from knowledge_assistant.application.wiki.services.quality import (
    calculate_wiki_quality,
)
from knowledge_assistant.bootstrap.dependencies.user import get_current_user
from knowledge_assistant.bootstrap.dependencies.wiki import (
    CompileDocumentWikiCommandDependency,
    ScanWikiMaintenanceCommandDependency,
    WikiRepositoryDependency,
)
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.domain.wiki.entities import (
    WikiConflictStatus,
    WikiMaintenanceStatus,
    WikiMaintenanceSuggestion,
    WikiPage,
    WikiPageConflict,
    WikiPageDetails,
    WikiPageRevision,
    WikiQualityScore,
)
from knowledge_assistant.presentation.api.v1.schemas.wiki import (
    CompileWikiResponse,
    UpdateWikiConflictRequest,
    UpdateWikiMaintenanceSuggestionRequest,
    WikiClaimCitationResponse,
    WikiMaintenanceSuggestionResponse,
    WikiPageConflictResponse,
    WikiPageDetailsResponse,
    WikiPageReferenceResponse,
    WikiPageResponse,
    WikiPageRevisionResponse,
    WikiPageSourceResponse,
    WikiQualityScoreResponse,
    WikiRevisionDiffLineResponse,
    WikiRevisionDiffResponse,
)


router = APIRouter(prefix="/wiki", tags=["Wiki"])


def _to_quality_response(
    quality: WikiQualityScore,
) -> WikiQualityScoreResponse:
    return WikiQualityScoreResponse(
        source_coverage=quality.source_coverage,
        freshness=quality.freshness,
        consistency=quality.consistency,
        connectivity=quality.connectivity,
        overall=quality.overall,
        supported_claims=quality.supported_claims,
        unsupported_claims=quality.unsupported_claims,
        open_conflicts=quality.open_conflicts,
        connections_count=quality.connections_count,
        issues=list(quality.issues),
    )


def _to_response(
    page: WikiPage,
    quality: WikiQualityScore | None = None,
) -> WikiPageResponse:
    return WikiPageResponse(
        id=page.id,
        document_id=page.document_id,
        slug=page.slug,
        title=page.title,
        summary=page.summary,
        content_markdown=page.content_markdown,
        created_at=page.created_at,
        updated_at=page.updated_at,
        quality=(
            _to_quality_response(quality)
            if quality is not None
            else None
        ),
    )


def _to_conflict_response(
    conflict: WikiPageConflict,
) -> WikiPageConflictResponse:
    return WikiPageConflictResponse(
        id=conflict.id,
        source_document_id=conflict.source_document_id,
        existing_statement=conflict.existing_statement,
        incoming_statement=conflict.incoming_statement,
        explanation=conflict.explanation,
        status=conflict.status.value,
        resolution_note=conflict.resolution_note,
        created_at=conflict.created_at,
        resolved_at=conflict.resolved_at,
    )


def _to_details_response(
    details: WikiPageDetails,
) -> WikiPageDetailsResponse:
    page = details.page

    return WikiPageDetailsResponse(
        id=page.id,
        document_id=page.document_id,
        slug=page.slug,
        title=page.title,
        summary=page.summary,
        content_markdown=page.content_markdown,
        created_at=page.created_at,
        updated_at=page.updated_at,
        quality=(
            _to_quality_response(details.quality)
            if details.quality is not None
            else None
        ),
        sources=[
            WikiPageSourceResponse(
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                document_filename=source.document_filename,
                chunk_index=source.chunk_index,
                page_number=source.page_number,
            )
            for source in details.sources
        ],
        related_pages=[
            WikiPageReferenceResponse(
                page_id=reference.page_id,
                slug=reference.slug,
                title=reference.title,
                label=reference.label,
            )
            for reference in details.related_pages
        ],
        backlinks=[
            WikiPageReferenceResponse(
                page_id=reference.page_id,
                slug=reference.slug,
                title=reference.title,
                label=reference.label,
            )
            for reference in details.backlinks
        ],
        conflicts=[
            _to_conflict_response(conflict)
            for conflict in details.conflicts
        ],
        claim_citations=[
            WikiClaimCitationResponse(
                claim_key=claim.claim_key,
                claim_text=claim.claim_text,
                position=claim.position,
                sources=[
                    WikiPageSourceResponse(
                        chunk_id=source.chunk_id,
                        document_id=source.document_id,
                        document_filename=source.document_filename,
                        chunk_index=source.chunk_index,
                        page_number=source.page_number,
                    )
                    for source in claim.sources
                ],
            )
            for claim in details.claim_citations
        ],
    )


def _to_maintenance_response(
    suggestion: WikiMaintenanceSuggestion,
) -> WikiMaintenanceSuggestionResponse:
    return WikiMaintenanceSuggestionResponse(
        id=suggestion.id,
        issue_type=suggestion.issue_type.value,
        status=suggestion.status.value,
        title=suggestion.title,
        description=suggestion.description,
        page_ids=list(suggestion.page_ids),
        metadata=suggestion.metadata,
        confidence=suggestion.confidence,
        created_at=suggestion.created_at,
        updated_at=suggestion.updated_at,
    )


def _to_revision_response(
    revision: WikiPageRevision,
) -> WikiPageRevisionResponse:
    return WikiPageRevisionResponse(
        id=revision.id,
        wiki_page_id=revision.wiki_page_id,
        page_slug=revision.page_slug,
        revision_number=revision.revision_number,
        title=revision.title,
        summary=revision.summary,
        content_markdown=revision.content_markdown,
        operation=revision.operation.value,
        triggering_document_id=revision.triggering_document_id,
        created_at=revision.created_at,
    )


@router.post(
    "/documents/{document_id}/compile",
    response_model=CompileWikiResponse,
    status_code=status.HTTP_201_CREATED,
)
async def compile_document_wiki(
    document_id: UUID,
    command: CompileDocumentWikiCommandDependency,
    current_user: User = Depends(get_current_user),
) -> CompileWikiResponse:
    try:
        graph = await command.execute(
            document_id=document_id,
            owner_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return CompileWikiResponse(
        document_id=graph.document_id,
        pages_count=len(graph.pages),
        sources_count=len(graph.sources),
        links_count=len(graph.links),
        conflicts_count=len(graph.conflicts),
        pages=[_to_response(page) for page in graph.pages],
    )


@router.get("/pages", response_model=list[WikiPageResponse])
async def list_wiki_pages(
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> list[WikiPageResponse]:
    pages = await wiki_repository.list_by_owner_id(current_user.id)
    responses: list[WikiPageResponse] = []

    for page in pages:
        details = await wiki_repository.get_details_by_slug(
            owner_id=current_user.id,
            slug=page.slug,
        )
        quality = (
            calculate_wiki_quality(details)
            if details is not None
            else None
        )
        responses.append(_to_response(page, quality))

    return responses


@router.get(
    "/pages/{slug}/revisions",
    response_model=list[WikiPageRevisionResponse],
)
async def list_wiki_page_revisions(
    slug: str,
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> list[WikiPageRevisionResponse]:
    revisions = await wiki_repository.list_revisions_by_slug(
        owner_id=current_user.id,
        slug=slug,
    )
    return [_to_revision_response(revision) for revision in revisions]


@router.get(
    "/pages/{slug}/revisions/{revision_number}/diff",
    response_model=WikiRevisionDiffResponse,
)
async def get_wiki_revision_diff(
    slug: str,
    revision_number: int,
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> WikiRevisionDiffResponse:
    query = GetWikiRevisionDiffQuery(wiki_repository)

    try:
        result = await query.execute(
            owner_id=current_user.id,
            slug=slug,
            revision_number=revision_number,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return WikiRevisionDiffResponse(
        from_revision_number=result.from_revision_number,
        to_revision_number=result.to_revision_number,
        lines=[
            WikiRevisionDiffLineResponse(
                kind=line.kind,
                text=line.text,
            )
            for line in result.lines
        ],
    )


@router.post(
    "/pages/{slug}/revisions/{revision_number}/restore",
    response_model=WikiPageResponse,
)
async def restore_wiki_revision(
    slug: str,
    revision_number: int,
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> WikiPageResponse:
    try:
        page = await wiki_repository.restore_revision(
            owner_id=current_user.id,
            slug=slug,
            revision_number=revision_number,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return _to_response(page)


@router.patch(
    "/conflicts/{conflict_id}",
    response_model=WikiPageConflictResponse,
)
async def update_wiki_conflict(
    conflict_id: UUID,
    payload: UpdateWikiConflictRequest,
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> WikiPageConflictResponse:
    try:
        conflict = await wiki_repository.update_conflict_status(
            owner_id=current_user.id,
            conflict_id=conflict_id,
            status=WikiConflictStatus(payload.status),
            resolution_note=payload.resolution_note,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return _to_conflict_response(conflict)


@router.post(
    "/maintenance/scan",
    response_model=list[WikiMaintenanceSuggestionResponse],
)
async def scan_wiki_maintenance(
    command: ScanWikiMaintenanceCommandDependency,
    current_user: User = Depends(get_current_user),
) -> list[WikiMaintenanceSuggestionResponse]:
    suggestions = await command.execute(owner_id=current_user.id)
    return [
        _to_maintenance_response(suggestion)
        for suggestion in suggestions
    ]


@router.get(
    "/maintenance/suggestions",
    response_model=list[WikiMaintenanceSuggestionResponse],
)
async def list_wiki_maintenance_suggestions(
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> list[WikiMaintenanceSuggestionResponse]:
    suggestions = await wiki_repository.list_maintenance_suggestions(
        owner_id=current_user.id,
    )
    return [
        _to_maintenance_response(suggestion)
        for suggestion in suggestions
    ]


@router.patch(
    "/maintenance/suggestions/{suggestion_id}",
    response_model=WikiMaintenanceSuggestionResponse,
)
async def update_wiki_maintenance_suggestion(
    suggestion_id: UUID,
    payload: UpdateWikiMaintenanceSuggestionRequest,
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> WikiMaintenanceSuggestionResponse:
    try:
        suggestion = (
            await wiki_repository.update_maintenance_suggestion_status(
                owner_id=current_user.id,
                suggestion_id=suggestion_id,
                status=WikiMaintenanceStatus(payload.status),
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return _to_maintenance_response(suggestion)


@router.get(
    "/pages/{slug}",
    response_model=WikiPageDetailsResponse,
)
async def get_wiki_page(
    slug: str,
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> WikiPageDetailsResponse:
    details = await wiki_repository.get_details_by_slug(
        owner_id=current_user.id,
        slug=slug,
    )

    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wiki page was not found.",
        )

    details = WikiPageDetails(
        page=details.page,
        sources=details.sources,
        related_pages=details.related_pages,
        backlinks=details.backlinks,
        conflicts=details.conflicts,
        claim_citations=details.claim_citations,
        quality=calculate_wiki_quality(details),
    )

    return _to_details_response(details)
