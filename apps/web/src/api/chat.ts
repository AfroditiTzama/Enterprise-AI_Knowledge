import apiClient from "./client";

export interface KnowledgeSource {
  source_id: string;
  source_type: string;
  document_id: string | null;
  title: string;
  score: number;
  slug: string | null;
  page_number: number | null;
  chunk_index: number | null;
}

export interface AskKnowledgeResponse {
  answer_markdown: string;
  retrieval_mode: string;
  sources: KnowledgeSource[];
}

export async function askKnowledge(
  question: string,
): Promise<AskKnowledgeResponse> {
  const response =
    await apiClient.post<AskKnowledgeResponse>(
      "/chat/ask",
      { question },
    );

  return response.data;
}
