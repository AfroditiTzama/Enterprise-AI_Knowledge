import apiClient from "./client";

export interface WikiQualityScore {
  source_coverage: number;
  freshness: number;
  consistency: number;
  connectivity: number;
  overall: number;
  supported_claims: number;
  unsupported_claims: number;
  open_conflicts: number;
  connections_count: number;
  issues: string[];
}

export interface WikiPageItem {
  id: string;
  document_id: string | null;
  slug: string;
  title: string;
  summary: string;
  content_markdown: string;
  created_at: string;
  updated_at: string;
  quality: WikiQualityScore | null;
}

export interface WikiPageSourceItem {
  chunk_id: string;
  document_id: string;
  document_filename: string;
  chunk_index: number;
  page_number: number | null;
}

export interface WikiClaimCitationItem {
  claim_key: string;
  claim_text: string;
  position: number;
  sources: WikiPageSourceItem[];
}

export interface WikiPageReferenceItem {
  page_id: string;
  slug: string;
  title: string;
  label: string;
}

export interface WikiPageConflictItem {
  id: string;
  source_document_id: string | null;
  existing_statement: string;
  incoming_statement: string;
  explanation: string;
  status: "OPEN" | "RESOLVED" | "DISMISSED";
  resolution_note: string;
  created_at: string;
  resolved_at: string | null;
}

export interface WikiPageDetails extends WikiPageItem {
  sources: WikiPageSourceItem[];
  related_pages: WikiPageReferenceItem[];
  backlinks: WikiPageReferenceItem[];
  conflicts: WikiPageConflictItem[];
  claim_citations: WikiClaimCitationItem[];
}

export interface WikiPageRevisionItem {
  id: string;
  wiki_page_id: string | null;
  page_slug: string;
  revision_number: number;
  title: string;
  summary: string;
  content_markdown: string;
  operation: "CREATE" | "UPDATE" | "MERGE" | "RESTORE";
  triggering_document_id: string | null;
  created_at: string;
}

export interface WikiRevisionDiffLine {
  kind: "added" | "removed" | "context";
  text: string;
}

export interface WikiRevisionDiff {
  from_revision_number: number | null;
  to_revision_number: number;
  lines: WikiRevisionDiffLine[];
}

export type WikiMaintenanceStatus =
  | "PENDING"
  | "APPROVED"
  | "REJECTED";

export type WikiMaintenanceIssueType =
  | "DUPLICATE"
  | "ORPHAN"
  | "BROKEN_LINK"
  | "OVERSIZED"
  | "UNDERSIZED"
  | "UNSUPPORTED_CLAIMS";

export interface WikiMaintenanceSuggestion {
  id: string;
  issue_type: WikiMaintenanceIssueType;
  status: WikiMaintenanceStatus;
  title: string;
  description: string;
  page_ids: string[];
  metadata: Record<string, unknown>;
  confidence: number;
  created_at: string;
  updated_at: string;
}

export interface CompileWikiResponse {
  document_id: string;
  pages_count: number;
  sources_count: number;
  links_count: number;
  conflicts_count: number;
  pages: WikiPageItem[];
}

export async function compileDocumentWiki(
  documentId: string,
): Promise<CompileWikiResponse> {
  const response = await apiClient.post<CompileWikiResponse>(
    `/wiki/documents/${documentId}/compile`,
  );

  return response.data;
}

export async function listWikiPages(): Promise<WikiPageItem[]> {
  const response = await apiClient.get<WikiPageItem[]>("/wiki/pages");
  return response.data;
}

export async function getWikiPage(
  slug: string,
): Promise<WikiPageDetails> {
  const response = await apiClient.get<WikiPageDetails>(
    `/wiki/pages/${encodeURIComponent(slug)}`,
  );

  return response.data;
}

export async function listWikiPageRevisions(
  slug: string,
): Promise<WikiPageRevisionItem[]> {
  const response = await apiClient.get<WikiPageRevisionItem[]>(
    `/wiki/pages/${encodeURIComponent(slug)}/revisions`,
  );

  return response.data;
}

export async function getWikiRevisionDiff(
  slug: string,
  revisionNumber: number,
): Promise<WikiRevisionDiff> {
  const response = await apiClient.get<WikiRevisionDiff>(
    `/wiki/pages/${encodeURIComponent(
      slug,
    )}/revisions/${revisionNumber}/diff`,
  );

  return response.data;
}

export async function restoreWikiRevision(
  slug: string,
  revisionNumber: number,
): Promise<WikiPageItem> {
  const response = await apiClient.post<WikiPageItem>(
    `/wiki/pages/${encodeURIComponent(
      slug,
    )}/revisions/${revisionNumber}/restore`,
  );

  return response.data;
}

export async function updateWikiConflict(
  conflictId: string,
  status: "OPEN" | "RESOLVED" | "DISMISSED",
  resolutionNote = "",
): Promise<WikiPageConflictItem> {
  const response = await apiClient.patch<WikiPageConflictItem>(
    `/wiki/conflicts/${conflictId}`,
    {
      status,
      resolution_note: resolutionNote,
    },
  );

  return response.data;
}

export async function scanWikiMaintenance(): Promise<
  WikiMaintenanceSuggestion[]
> {
  const response = await apiClient.post<WikiMaintenanceSuggestion[]>(
    "/wiki/maintenance/scan",
  );
  return response.data;
}

export async function listWikiMaintenanceSuggestions(): Promise<
  WikiMaintenanceSuggestion[]
> {
  const response = await apiClient.get<WikiMaintenanceSuggestion[]>(
    "/wiki/maintenance/suggestions",
  );
  return response.data;
}

export async function updateWikiMaintenanceSuggestion(
  suggestionId: string,
  status: "APPROVED" | "REJECTED",
): Promise<WikiMaintenanceSuggestion> {
  const response = await apiClient.patch<WikiMaintenanceSuggestion>(
    `/wiki/maintenance/suggestions/${suggestionId}`,
    { status },
  );
  return response.data;
}
