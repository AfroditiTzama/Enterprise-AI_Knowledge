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

export interface WikiPageSourceItem {
  chunk_id: string;
  document_id: string;
  document_filename: string;
  chunk_index: number;
  page_number: number | null;
}

export interface WikiPageReferenceItem {
  page_id: string;
  slug: string;
  title: string;
  label: string;
}

export interface WikiPageDetails
  extends WikiPageItem {
  sources: WikiPageSourceItem[];
  related_pages: WikiPageReferenceItem[];
  backlinks: WikiPageReferenceItem[];
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
): Promise<WikiPageDetails> {
  const response =
    await apiClient.get<WikiPageDetails>(
      `/wiki/pages/${encodeURIComponent(slug)}`,
    );

  return response.data;
}
