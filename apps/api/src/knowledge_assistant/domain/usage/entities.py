from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class LLMUsageEvent:
    id: UUID
    owner_id: UUID
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    cache_hit: bool
    created_at: datetime


@dataclass(frozen=True)
class LLMUsageSummary:
    requests: int
    cache_hits: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
