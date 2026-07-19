import apiClient from "./client";

export interface WikiPageItem {
  id: string;
  document_id: string;
  slug: string;
  title: string;
  summary: string;
  content_markdown: string;
  created_at: string;
  updated_at: string;
}

export interface CompileWikiResponse {
  document_id: string;
  pages_count: number;
  sources_count: number;
  links_count: number;
  pages: WikiPageItem[];
}

export async function compileDocumentWiki(
  documentId: string,
): Promise<CompileWikiResponse> {
  const response =
    await apiClient.post<CompileWikiResponse>(
      `/wiki/documents/${documentId}/compile`,
    );

  return response.data;
}

export async function listWikiPages(): Promise<
  WikiPageItem[]
> {
  const response =
    await apiClient.get<WikiPageItem[]>(
      "/wiki/pages",
    );

  return response.data;
}

export async function getWikiPage(
  slug: string,
): Promise<WikiPageItem> {
  const response =
    await apiClient.get<WikiPageItem>(
      `/wiki/pages/${encodeURIComponent(slug)}`,
    );

  return response.data;
}
