from uuid import UUID

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from knowledge_assistant.bootstrap.dependencies.document import (
    DeleteDocumentCommandDependency,
    GetDocumentChunkPreviewQueryDependency,
    ListDocumentsQueryDependency,
    ProcessDocumentCommandDependency,
    UploadDocumentCommandDependency,
)
from knowledge_assistant.bootstrap.dependencies.user import get_current_user
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.presentation.api.v1.schemas.document import (
    DocumentChunkPreviewResponse,
    DocumentResponse,
    ProcessDocumentResponse,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


CurrentUserDependency = Annotated[
    User,
    Depends(get_current_user),
]


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[
        UploadFile,
        File(description="Document file to upload"),
    ],
    current_user: CurrentUserDependency,
    command: UploadDocumentCommandDependency,
) -> DocumentResponse:
    try:
        file_content = await file.read()

        document = await command.execute(
            owner_id=current_user.id,
            original_filename=file.filename or "",
            content_type=file.content_type,
            file_content=file_content,
        )

        return DocumentResponse.model_validate(document)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()


@router.get(
    "",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_documents(
    current_user: CurrentUserDependency,
    query: ListDocumentsQueryDependency,
) -> list[DocumentResponse]:
    documents = await query.execute(
        owner_id=current_user.id,
    )

    return [
        DocumentResponse.model_validate(document)
        for document in documents
    ]


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    current_user: CurrentUserDependency,
    command: DeleteDocumentCommandDependency,
) -> None:
    try:
        await command.execute(
            document_id=document_id,
            owner_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/chunks/{chunk_id}",
    response_model=DocumentChunkPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document_chunk_preview(
    chunk_id: UUID,
    current_user: CurrentUserDependency,
    query: GetDocumentChunkPreviewQueryDependency,
) -> DocumentChunkPreviewResponse:
    try:
        preview = await query.execute(
            chunk_id=chunk_id,
            owner_id=current_user.id,
        )

        return DocumentChunkPreviewResponse(
            chunk_id=preview.chunk_id,
            document_id=preview.document_id,
            document_filename=(
                preview.document_filename
            ),
            chunk_index=preview.chunk_index,
            page_number=preview.page_number,
            text=preview.text,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{document_id}/chunks/{chunk_index}",
    response_model=DocumentChunkPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document_chunk_preview_by_location(
    document_id: UUID,
    chunk_index: int,
    current_user: CurrentUserDependency,
    query: GetDocumentChunkPreviewQueryDependency,
) -> DocumentChunkPreviewResponse:
    try:
        preview = await query.execute_by_location(
            document_id=document_id,
            chunk_index=chunk_index,
            owner_id=current_user.id,
        )

        return DocumentChunkPreviewResponse(
            chunk_id=preview.chunk_id,
            document_id=preview.document_id,
            document_filename=(
                preview.document_filename
            ),
            chunk_index=preview.chunk_index,
            page_number=preview.page_number,
            text=preview.text,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{document_id}/process",
    response_model=ProcessDocumentResponse,
    status_code=status.HTTP_200_OK,
)
async def process_document(
    document_id: UUID,
    current_user: CurrentUserDependency,
    command: ProcessDocumentCommandDependency,
) -> ProcessDocumentResponse:
    try:
        result = await command.execute(
            document_id=document_id,
            owner_id=current_user.id,
        )

        full_text = result.extracted_document.full_text

        return ProcessDocumentResponse(
            document=DocumentResponse.model_validate(
                result.document
            ),
            extracted_segments=len(
                result.extracted_document.segments
            ),
            extracted_characters=len(full_text),
            chunks_count=len(result.chunks),
            text_preview=full_text[:1000],
        )

    except ValueError as exc:
        if str(exc) == "Document was not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The stored document file could not be found.",
        ) from exc
