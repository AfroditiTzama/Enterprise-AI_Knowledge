from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from knowledge_assistant.infrastructure.database.base import Base
from knowledge_assistant.infrastructure.database.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class LLMUsageEventModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "llm_usage_events"

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_hit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
