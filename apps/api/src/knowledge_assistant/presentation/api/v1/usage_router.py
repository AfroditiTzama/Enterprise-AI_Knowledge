from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from knowledge_assistant.bootstrap.dependencies.chat import (
    get_usage_repository,
)
from knowledge_assistant.bootstrap.dependencies.user import CurrentUserDependency
from knowledge_assistant.domain.usage.repository import LLMUsageRepository
from knowledge_assistant.presentation.api.v1.schemas.usage import (
    UsageSummaryResponse,
)


router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    current_user: CurrentUserDependency,
    repository: Annotated[
        LLMUsageRepository,
        Depends(get_usage_repository),
    ],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> UsageSummaryResponse:
    summary = await repository.summarize(
        owner_id=current_user.id,
        since=datetime.now(timezone.utc) - timedelta(days=days),
    )
    return UsageSummaryResponse(
        days=days,
        requests=summary.requests,
        cache_hits=summary.cache_hits,
        input_tokens=summary.input_tokens,
        output_tokens=summary.output_tokens,
        estimated_cost_usd=summary.estimated_cost_usd,
    )
