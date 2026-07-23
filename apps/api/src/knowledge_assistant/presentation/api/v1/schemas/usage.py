from pydantic import BaseModel


class UsageSummaryResponse(BaseModel):
    days: int
    requests: int
    cache_hits: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
