from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_assistant.bootstrap.dependencies.user import (
    get_current_user,
)
from knowledge_assistant.bootstrap.dependencies.wiki import (
    CompileDocumentWikiCommandDependency,
    WikiRepositoryDependency,
)
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.domain.wiki.entities import (
    WikiPage,
    WikiPageDetails,
    WikiPageRevision,
)
from knowledge_assistant.presentation.api.v1.schemas.wiki import (
    CompileWikiResponse,
    WikiPageDetailsResponse,
    WikiPageReferenceResponse,
    WikiPageResponse,
    WikiPageRevisionResponse,
    WikiPageSourceResponse,
)


router = APIRouter(
    prefix="/wiki",
    tags=["Wiki"],
)


def _to_response(
    page: WikiPage,
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
        sources=[
            WikiPageSourceResponse(
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                document_filename=(
                    source.document_filename
                ),
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
        triggering_document_id=(
            revision.triggering_document_id
        ),
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
        pages=[
            _to_response(page)
            for page in graph.pages
        ],
    )


@router.get(
    "/pages",
    response_model=list[WikiPageResponse],
)
async def list_wiki_pages(
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> list[WikiPageResponse]:
    pages = await wiki_repository.list_by_owner_id(
        current_user.id
    )

    return [
        _to_response(page)
        for page in pages
    ]


@router.get(
    "/pages/{slug}/revisions",
    response_model=list[WikiPageRevisionResponse],
)
async def list_wiki_page_revisions(
    slug: str,
    wiki_repository: WikiRepositoryDependency,
    current_user: User = Depends(get_current_user),
) -> list[WikiPageRevisionResponse]:
    revisions = (
        await wiki_repository.list_revisions_by_slug(
            owner_id=current_user.id,
            slug=slug,
        )
    )

    return [
        _to_revision_response(revision)
        for revision in revisions
    ]


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

    return _to_details_response(details)
