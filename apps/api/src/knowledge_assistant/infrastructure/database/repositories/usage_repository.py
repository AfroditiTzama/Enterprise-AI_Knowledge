from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_assistant.domain.usage.entities import (
    LLMUsageEvent,
    LLMUsageSummary,
)
from knowledge_assistant.domain.usage.repository import LLMUsageRepository
from knowledge_assistant.infrastructure.database.models.usage import (
    LLMUsageEventModel,
)


class SQLAlchemyLLMUsageRepository(LLMUsageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: LLMUsageEvent) -> None:
        self._session.add(
            LLMUsageEventModel(
                id=event.id,
                owner_id=event.owner_id,
                operation=event.operation,
                model=event.model,
                input_tokens=event.input_tokens,
                output_tokens=event.output_tokens,
                estimated_cost_usd=event.estimated_cost_usd,
                latency_ms=event.latency_ms,
                cache_hit=event.cache_hit,
                created_at=event.created_at,
                updated_at=event.created_at,
            )
        )
        await self._session.flush()

    async def summarize(
        self,
        *,
        owner_id: UUID,
        since: datetime,
    ) -> LLMUsageSummary:
        statement = select(
            func.count(LLMUsageEventModel.id),
            func.coalesce(
                func.sum(
                    case(
                        (LLMUsageEventModel.cache_hit.is_(True), 1),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(func.sum(LLMUsageEventModel.input_tokens), 0),
            func.coalesce(func.sum(LLMUsageEventModel.output_tokens), 0),
            func.coalesce(
                func.sum(LLMUsageEventModel.estimated_cost_usd),
                0.0,
            ),
        ).where(
            LLMUsageEventModel.owner_id == owner_id,
            LLMUsageEventModel.created_at >= since,
        )
        result = await self._session.execute(statement)
        row = result.one()
        return LLMUsageSummary(
            requests=int(row[0] or 0),
            cache_hits=int(row[1] or 0),
            input_tokens=int(row[2] or 0),
            output_tokens=int(row[3] or 0),
            estimated_cost_usd=float(row[4] or 0.0),
        )
