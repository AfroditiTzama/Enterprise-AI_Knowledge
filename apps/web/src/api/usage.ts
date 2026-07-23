import apiClient from "./client";

export interface UsageSummary {
  days: number;
  requests: number;
  cache_hits: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
}

export async function getUsageSummary(
  days = 30,
): Promise<UsageSummary> {
  const response = await apiClient.get<UsageSummary>(
    "/usage/summary",
    { params: { days } },
  );
  return response.data;
}
