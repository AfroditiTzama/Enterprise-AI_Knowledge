from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_assistant.bootstrap.dependencies.chat import (
    AskKnowledgeQueryDependency,
)
from knowledge_assistant.bootstrap.dependencies.user import (
    get_current_user,
)
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.presentation.api.v1.schemas.chat import (
    AskKnowledgeRequest,
    AskKnowledgeResponse,
    KnowledgeSourceResponse,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/ask",
    response_model=AskKnowledgeResponse,
)
async def ask_knowledge_assistant(
    request: AskKnowledgeRequest,
    query: AskKnowledgeQueryDependency,
    current_user: User = Depends(get_current_user),
) -> AskKnowledgeResponse:
    try:
        result = await query.execute(
            owner_id=current_user.id,
            question=request.question,
            assistant_behavior=current_user.assistant_behavior,
            preferred_language=current_user.preferred_language,
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

    return AskKnowledgeResponse(
        answer_markdown=result.answer_markdown,
        retrieval_mode=result.retrieval_mode,
        sources=[
            KnowledgeSourceResponse(
                source_id=source.source_id,
                source_type=source.source_type,
                document_id=source.document_id,
                title=source.title,
                slug=source.slug,
                page_number=source.page_number,
                chunk_index=source.chunk_index,
                score=source.score,
            )
            for source in result.sources
        ],
    )