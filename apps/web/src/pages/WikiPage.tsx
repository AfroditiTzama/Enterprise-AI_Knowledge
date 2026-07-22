import {
  XCircle,
  GitCompareArrows,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Clock3,
  ExternalLink,
  FileText,
  History,
  Link2,
  LoaderCircle,
  Network,
  Search,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import ReactMarkdown, {
  defaultUrlTransform,
} from "react-markdown";
import {
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import {
  getDocumentChunkPreview,
} from "../api/documents";
import {
  getApiErrorMessage,
} from "../api/errors";
import {
  withApiRetry,
} from "../api/retry";
import {
  getWikiPage,
  getWikiRevisionDiff,
  listWikiMaintenanceSuggestions,
  listWikiPageRevisions,
  listWikiPages,
  restoreWikiRevision,
  scanWikiMaintenance,
  updateWikiConflict,
  updateWikiMaintenanceSuggestion,
  type WikiMaintenanceSuggestion,
  type WikiPageDetails,
  type WikiPageItem,
  type WikiPageRevisionItem,
  type WikiPageSourceItem,
  type WikiRevisionDiff,
} from "../api/wiki";
import ConfirmDialog from "../components/ConfirmDialog";
import FeedbackBanner from "../components/FeedbackBanner";
import RevisionDiffDrawer from "../components/RevisionDiffDrawer";
import SourcePreviewDrawer, {
  type SourcePreviewContent,
} from "../components/SourcePreviewDrawer";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function WikiPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedSlug = searchParams.get("slug");
  const [pages, setPages] = useState<WikiPageItem[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(
    requestedSlug,
  );
  const [details, setDetails] = useState<WikiPageDetails | null>(null);
  const [revisions, setRevisions] =
    useState<WikiPageRevisionItem[]>([]);
  const [query, setQuery] = useState("");
  const [isListLoading, setIsListLoading] = useState(true);
  const [isPageLoading, setIsPageLoading] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [listError, setListError] = useState("");
  const [pageError, setPageError] = useState("");
  const [isSourcePreviewOpen, setIsSourcePreviewOpen] =
    useState(false);
  const [isSourcePreviewLoading, setIsSourcePreviewLoading] =
    useState(false);
  const [sourcePreviewError, setSourcePreviewError] = useState("");
  const [sourcePreviewContent, setSourcePreviewContent] =
    useState<SourcePreviewContent | null>(null);
  const [selectedRevision, setSelectedRevision] =
    useState<WikiPageRevisionItem | null>(null);
  const [revisionDiff, setRevisionDiff] =
    useState<WikiRevisionDiff | null>(null);
  const [isRevisionDiffOpen, setIsRevisionDiffOpen] =
    useState(false);
  const [isRevisionDiffLoading, setIsRevisionDiffLoading] =
    useState(false);
  const [isRestoreConfirmOpen, setIsRestoreConfirmOpen] =
    useState(false);
  const [isRestoringRevision, setIsRestoringRevision] =
    useState(false);
  const [revisionActionError, setRevisionActionError] =
    useState("");
  const [conflictActionId, setConflictActionId] =
    useState<string | null>(null);
  const [maintenanceSuggestions, setMaintenanceSuggestions] =
    useState<WikiMaintenanceSuggestion[]>([]);
  const [isMaintenanceLoading, setIsMaintenanceLoading] =
    useState(false);
  const [maintenanceError, setMaintenanceError] = useState("");
  const [maintenanceActionId, setMaintenanceActionId] =
    useState<string | null>(null);
  const [qualityFilter, setQualityFilter] = useState<
    "all" | "attention" | "conflicts"
  >("all");

  const loadPages = useCallback(async () => {
    setListError("");
    setIsListLoading(true);
    setIsRetrying(false);

    try {
      const [items, suggestions] = await withApiRetry(
        () =>
          Promise.all([
            listWikiPages(),
            listWikiMaintenanceSuggestions(),
          ]),
        {
          retries: 2,
          onRetry: () => setIsRetrying(true),
        },
      );

      setPages(items);
      setMaintenanceSuggestions(suggestions);

      const requestedExists =
        requestedSlug &&
        items.some((page) => page.slug === requestedSlug);
      const nextSlug = requestedExists
        ? requestedSlug
        : items[0]?.slug ?? null;

      setSelectedSlug(nextSlug);

      if (nextSlug) {
        setSearchParams({ slug: nextSlug }, { replace: true });
      }
    } catch (requestError) {
      setListError(getApiErrorMessage(requestError));
    } finally {
      setIsListLoading(false);
      setIsRetrying(false);
    }
  }, [requestedSlug, setSearchParams]);

  const loadSelectedPage = useCallback(async () => {
    if (!selectedSlug) {
      setDetails(null);
      setRevisions([]);
      return;
    }

    setPageError("");
    setIsPageLoading(true);

    try {
      const [pageDetails, pageRevisions] = await withApiRetry(
        () =>
          Promise.all([
            getWikiPage(selectedSlug),
            listWikiPageRevisions(selectedSlug),
          ]),
        { retries: 2 },
      );

      setDetails(pageDetails);
      setRevisions(pageRevisions);
    } catch (requestError) {
      setDetails(null);
      setRevisions([]);
      setPageError(getApiErrorMessage(requestError));
    } finally {
      setIsPageLoading(false);
    }
  }, [selectedSlug]);

  useEffect(() => {
    void loadPages();
  }, [loadPages]);

  useEffect(() => {
    void loadSelectedPage();
  }, [loadSelectedPage]);

  const filteredPages = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    return pages.filter((page) => {
      const matchesQuery =
        !normalized ||
        [page.title, page.summary, page.slug].some((value) =>
          value.toLowerCase().includes(normalized),
        );

      if (!matchesQuery) {
        return false;
      }

      if (qualityFilter === "attention") {
        return (page.quality?.overall ?? 100) < 75;
      }

      if (qualityFilter === "conflicts") {
        return (page.quality?.open_conflicts ?? 0) > 0;
      }

      return true;
    });
  }, [pages, qualityFilter, query]);

  function selectPage(slug: string) {
    setSelectedSlug(slug);
    setSearchParams({ slug }, { replace: true });
  }

  async function openSourcePreview(source: WikiPageSourceItem) {
    setIsSourcePreviewOpen(true);
    setIsSourcePreviewLoading(true);
    setSourcePreviewError("");
    setSourcePreviewContent(null);

    try {
      const preview = await getDocumentChunkPreview(source.chunk_id);

      setSourcePreviewContent({
        title: preview.document_filename,
        sourceLabel: "Original document",
        locationLabel:
          preview.page_number !== null
            ? `Page ${preview.page_number}`
            : `Chunk ${preview.chunk_index + 1}`,
        text: preview.text,
      });
    } catch (requestError) {
      setSourcePreviewError(getApiErrorMessage(requestError));
    } finally {
      setIsSourcePreviewLoading(false);
    }
  }

  async function openRevisionDiff(
    revision: WikiPageRevisionItem,
  ) {
    if (!selectedSlug) {
      return;
    }

    setSelectedRevision(revision);
    setRevisionDiff(null);
    setRevisionActionError("");
    setIsRevisionDiffOpen(true);
    setIsRevisionDiffLoading(true);

    try {
      const diff = await getWikiRevisionDiff(
        selectedSlug,
        revision.revision_number,
      );
      setRevisionDiff(diff);
    } catch (requestError) {
      setRevisionActionError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsRevisionDiffLoading(false);
    }
  }

  async function restoreSelectedRevision() {
    if (!selectedSlug || !selectedRevision) {
      return;
    }

    setIsRestoringRevision(true);
    setRevisionActionError("");

    try {
      await restoreWikiRevision(
        selectedSlug,
        selectedRevision.revision_number,
      );
      setIsRestoreConfirmOpen(false);
      setIsRevisionDiffOpen(false);
      await loadSelectedPage();
      await loadPages();
    } catch (requestError) {
      setRevisionActionError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsRestoringRevision(false);
    }
  }

  async function changeConflictStatus(
    conflictId: string,
    nextStatus: "RESOLVED" | "DISMISSED",
  ) {
    setConflictActionId(conflictId);
    setRevisionActionError("");

    try {
      await updateWikiConflict(
        conflictId,
        nextStatus,
      );
      await loadSelectedPage();
    } catch (requestError) {
      setRevisionActionError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setConflictActionId(null);
    }
  }

  async function runMaintenanceScan() {
    setIsMaintenanceLoading(true);
    setMaintenanceError("");

    try {
      const suggestions = await scanWikiMaintenance();
      setMaintenanceSuggestions(suggestions);
      await loadPages();
    } catch (requestError) {
      setMaintenanceError(getApiErrorMessage(requestError));
    } finally {
      setIsMaintenanceLoading(false);
    }
  }

  async function changeMaintenanceStatus(
    suggestionId: string,
    nextStatus: "APPROVED" | "REJECTED",
  ) {
    setMaintenanceActionId(suggestionId);
    setMaintenanceError("");

    try {
      const updated = await updateWikiMaintenanceSuggestion(
        suggestionId,
        nextStatus,
      );
      setMaintenanceSuggestions((current) =>
        current.map((suggestion) =>
          suggestion.id === updated.id ? updated : suggestion,
        ),
      );
    } catch (requestError) {
      setMaintenanceError(getApiErrorMessage(requestError));
    } finally {
      setMaintenanceActionId(null);
    }
  }

  function openClaimCitation(claimKey: string) {
    const claim = details?.claim_citations.find(
      (item) => item.claim_key.toLowerCase() === claimKey.toLowerCase(),
    );
    const source = claim?.sources[0];

    if (source) {
      void openSourcePreview(source);
    }
  }

  return (
    <section className="page-container wiki-page-container">
      <header className="page-header">
        <div>
          <p className="eyebrow">Compiled knowledge</p>
          <h1>Knowledge Wiki</h1>
          <p>
            Browse connected pages, trace sources and review how your
            knowledge changes over time.
          </p>
        </div>

        <div className="page-actions">
          <button
            type="button"
            className="primary-button"
            disabled={isMaintenanceLoading}
            onClick={() => void runMaintenanceScan()}
          >
            {isMaintenanceLoading ? (
              <LoaderCircle className="spin" size={17} />
            ) : (
              <Sparkles size={17} />
            )}
            Scan Wiki
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate("/wiki/graph")}
          >
            <Network size={17} />
            Open graph
          </button>
        </div>
      </header>

      {isRetrying && (
        <FeedbackBanner
          kind="retrying"
          message="The server is waking up. Retrying…"
        />
      )}

      {listError && !isRetrying && (
        <FeedbackBanner
          kind="error"
          message={listError}
          onRetry={() => void loadPages()}
        />
      )}

      {isListLoading && !isRetrying ? (
        <div className="loading-panel">
          <LoaderCircle className="spin" size={25} />
          Loading Wiki pages...
        </div>
      ) : listError ? null : pages.length === 0 ? (
        <section className="empty-state">
          <div className="empty-icon">
            <BookOpen size={30} />
          </div>
          <h2>No Wiki pages yet</h2>
          <p>
            Process a document and select Build Wiki to create your
            first connected knowledge pages.
          </p>
          <button
            type="button"
            className="primary-button compact"
            onClick={() => navigate("/dashboard")}
          >
            Go to documents
            <ArrowRight size={17} />
          </button>
        </section>
      ) : (
        <div className="wiki-workspace">
          {maintenanceError && (
            <FeedbackBanner
              kind="error"
              message={maintenanceError}
            />
          )}

          {maintenanceSuggestions.length > 0 && (
            <section className="maintenance-panel">
              <div className="section-heading-row">
                <div>
                  <p className="eyebrow">Autonomous maintenance</p>
                  <h2>Wiki review suggestions</h2>
                  <p className="muted-copy">
                    Suggestions are review-only. Approving one records
                    your decision without silently changing the Wiki.
                  </p>
                </div>
                <ShieldCheck size={21} />
              </div>

              <div className="maintenance-suggestion-list">
                {maintenanceSuggestions.map((suggestion) => (
                  <article key={suggestion.id}>
                    <header>
                      <div>
                        <span className="maintenance-type">
                          {suggestion.issue_type.replaceAll("_", " ")}
                        </span>
                        <h3>{suggestion.title}</h3>
                      </div>
                      <span
                        className={`maintenance-status ${suggestion.status.toLowerCase()}`}
                      >
                        {suggestion.status}
                      </span>
                    </header>
                    <p>{suggestion.description}</p>
                    <small>
                      Confidence {Math.round(suggestion.confidence * 100)}%
                    </small>

                    <details className="maintenance-preview">
                      <summary>Preview details</summary>
                      <pre>
                        {JSON.stringify(suggestion.metadata, null, 2)}
                      </pre>
                    </details>

                    {suggestion.status === "PENDING" && (
                      <footer>
                        <button
                          type="button"
                          className="secondary-button compact"
                          disabled={maintenanceActionId === suggestion.id}
                          onClick={() =>
                            void changeMaintenanceStatus(
                              suggestion.id,
                              "REJECTED",
                            )
                          }
                        >
                          <ThumbsDown size={15} />
                          Reject
                        </button>
                        <button
                          type="button"
                          className="primary-button compact"
                          disabled={maintenanceActionId === suggestion.id}
                          onClick={() =>
                            void changeMaintenanceStatus(
                              suggestion.id,
                              "APPROVED",
                            )
                          }
                        >
                          <ThumbsUp size={15} />
                          Approve
                        </button>
                      </footer>
                    )}
                  </article>
                ))}
              </div>
            </section>
          )}

          <div className="wiki-layout">
          <aside className="wiki-sidebar">
            <div className="search-box">
              <Search size={17} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search Wiki pages"
              />
            </div>

            <div className="wiki-quality-filters" role="group" aria-label="Wiki quality filters">
              <button
                type="button"
                className={qualityFilter === "all" ? "active" : ""}
                onClick={() => setQualityFilter("all")}
              >
                All
              </button>
              <button
                type="button"
                className={qualityFilter === "attention" ? "active" : ""}
                onClick={() => setQualityFilter("attention")}
              >
                Needs attention
              </button>
              <button
                type="button"
                className={qualityFilter === "conflicts" ? "active" : ""}
                onClick={() => setQualityFilter("conflicts")}
              >
                Open conflicts
              </button>
            </div>

            <div className="wiki-page-count">
              {filteredPages.length} of {pages.length} pages
            </div>

            <div className="wiki-page-list">
              {filteredPages.map((page) => (
                <button
                  type="button"
                  key={page.id}
                  className={
                    selectedSlug === page.slug
                      ? "wiki-page-item active"
                      : "wiki-page-item"
                  }
                  onClick={() => selectPage(page.slug)}
                >
                  <BookOpen size={17} />
                  <span>
                    <span className="wiki-page-item-heading">
                      <strong>{page.title}</strong>
                      {page.quality && (
                        <em
                          className={
                            page.quality.overall >= 75
                              ? "quality-pill good"
                              : "quality-pill attention"
                          }
                        >
                          {page.quality.overall}
                        </em>
                      )}
                    </span>
                    <small>{page.summary}</small>
                  </span>
                </button>
              ))}
            </div>
          </aside>

          <main className="wiki-content-panel">
            {pageError && (
              <FeedbackBanner
                kind="error"
                message={pageError}
                onRetry={() => void loadSelectedPage()}
              />
            )}

            {isPageLoading ? (
              <div className="loading-panel">
                <LoaderCircle className="spin" size={25} />
                Opening Wiki page...
              </div>
            ) : pageError ? null : details ? (
              <article className="wiki-article">
                {revisionActionError && (
                  <FeedbackBanner
                    kind="error"
                    message={revisionActionError}
                  />
                )}

                <header className="wiki-article-header">
                  <div>
                    <p className="wiki-slug">{details.slug}</p>
                    <h2>{details.title}</h2>
                    <p>{details.summary}</p>
                  </div>

                  <span className="wiki-updated">
                    <Clock3 size={15} />
                    Updated {formatDate(details.updated_at)}
                  </span>
                </header>

                {details.quality && (
                  <section className="wiki-quality-panel">
                    <div className="quality-overall">
                      <ShieldCheck size={21} />
                      <div>
                        <strong>{details.quality.overall}/100</strong>
                        <span>Overall Wiki quality</span>
                      </div>
                    </div>

                    <div className="quality-metric-grid">
                      <div>
                        <span>Source coverage</span>
                        <strong>{details.quality.source_coverage}%</strong>
                      </div>
                      <div>
                        <span>Freshness</span>
                        <strong>{details.quality.freshness}%</strong>
                      </div>
                      <div>
                        <span>Consistency</span>
                        <strong>{details.quality.consistency}%</strong>
                      </div>
                      <div>
                        <span>Connectivity</span>
                        <strong>{details.quality.connectivity}%</strong>
                      </div>
                    </div>

                    {details.quality.issues.length > 0 && (
                      <div className="quality-issue-list">
                        {details.quality.issues.map((issue) => (
                          <span key={issue}>
                            <AlertTriangle size={14} />
                            {issue}
                          </span>
                        ))}
                      </div>
                    )}
                  </section>
                )}

                <div className="markdown-body">
                  <ReactMarkdown
                    urlTransform={(url) =>
                      url.startsWith("citation:")
                        ? url
                        : defaultUrlTransform(url)
                    }
                    components={{
                      a: ({ href, children }) => {
                        if (href?.startsWith("citation:")) {
                          const claimKey = href.slice("citation:".length);
                          return (
                            <button
                              type="button"
                              className="inline-citation"
                              title="Open the supporting source"
                              onClick={() => openClaimCitation(claimKey)}
                            >
                              {children}
                            </button>
                          );
                        }

                        return (
                          <a
                            href={href}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {children}
                          </a>
                        );
                      },
                    }}
                  >
                    {details.content_markdown}
                  </ReactMarkdown>
                </div>

                {details.conflicts.length > 0 && (
                  <section className="wiki-conflict-section">
                    <div className="section-heading-row">
                      <div>
                        <p className="eyebrow">Knowledge review</p>
                        <h3>Detected source conflicts</h3>
                      </div>
                      <AlertTriangle size={20} />
                    </div>

                    <p className="muted-copy">
                      The Wiki kept both claims instead of silently
                      choosing one. Review them and mark the issue.
                    </p>

                    <div className="wiki-conflict-list">
                      {details.conflicts.map((conflict) => (
                        <article key={conflict.id}>
                          <header>
                            <strong>Potential contradiction</strong>
                            <span
                              className={`conflict-status ${conflict.status.toLowerCase()}`}
                            >
                              {conflict.status}
                            </span>
                          </header>

                          <div className="conflict-statements">
                            <div>
                              <small>Existing knowledge</small>
                              <p>{conflict.existing_statement}</p>
                            </div>
                            <div>
                              <small>Incoming source</small>
                              <p>{conflict.incoming_statement}</p>
                            </div>
                          </div>

                          <p className="conflict-explanation">
                            {conflict.explanation}
                          </p>

                          {conflict.status === "OPEN" && (
                            <footer>
                              <button
                                type="button"
                                className="secondary-button compact"
                                disabled={conflictActionId === conflict.id}
                                onClick={() =>
                                  void changeConflictStatus(
                                    conflict.id,
                                    "DISMISSED",
                                  )
                                }
                              >
                                <XCircle size={16} />
                                Dismiss
                              </button>
                              <button
                                type="button"
                                className="primary-button compact"
                                disabled={conflictActionId === conflict.id}
                                onClick={() =>
                                  void changeConflictStatus(
                                    conflict.id,
                                    "RESOLVED",
                                  )
                                }
                              >
                                <CheckCircle2 size={16} />
                                Mark resolved
                              </button>
                            </footer>
                          )}
                        </article>
                      ))}
                    </div>
                  </section>
                )}

                <section className="claim-support-section">
                  <div className="section-heading-row">
                    <div>
                      <p className="eyebrow">Claim-level evidence</p>
                      <h3>Supported statements</h3>
                    </div>
                    <ShieldCheck size={20} />
                  </div>

                  {details.claim_citations.length === 0 ? (
                    <p className="muted-copy">
                      This page predates claim-level citations or contains
                      unsupported content. Rebuild it from a source document
                      to generate traceable paragraph citations.
                    </p>
                  ) : (
                    <div className="claim-support-list">
                      {details.claim_citations.map((claim) => (
                        <article key={claim.claim_key}>
                          <span>[{claim.claim_key}]</span>
                          <div>
                            <p>{claim.claim_text}</p>
                            <div>
                              {claim.sources.map((source) => (
                                <button
                                  type="button"
                                  key={`${claim.claim_key}-${source.chunk_id}`}
                                  onClick={() =>
                                    void openSourcePreview(source)
                                  }
                                >
                                  <FileText size={14} />
                                  {source.document_filename}
                                  {source.page_number !== null
                                    ? ` · page ${source.page_number}`
                                    : ` · chunk ${source.chunk_index + 1}`}
                                </button>
                              ))}
                            </div>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <div className="wiki-support-grid">
                  <section className="wiki-support-card">
                    <div className="support-card-heading">
                      <FileText size={18} />
                      <h3>Sources</h3>
                      <span>{details.sources.length}</span>
                    </div>

                    {details.sources.length === 0 ? (
                      <p className="muted-copy">
                        No source references are currently attached.
                      </p>
                    ) : (
                      <div className="wiki-source-list">
                        {details.sources.map((source) => (
                          <button
                            type="button"
                            key={source.chunk_id}
                            onClick={() =>
                              void openSourcePreview(source)
                            }
                          >
                            <FileText size={16} />
                            <span>
                              <strong>{source.document_filename}</strong>
                              <small>
                                {source.page_number !== null
                                  ? `Page ${source.page_number}`
                                  : `Chunk ${source.chunk_index + 1}`}
                              </small>
                            </span>
                            <ExternalLink size={15} />
                          </button>
                        ))}
                      </div>
                    )}
                  </section>

                  <section className="wiki-support-card">
                    <div className="support-card-heading">
                      <Link2 size={18} />
                      <h3>Connections</h3>
                      <span>
                        {details.related_pages.length +
                          details.backlinks.length}
                      </span>
                    </div>

                    <div className="relationship-group">
                      <h4>Related pages</h4>
                      {details.related_pages.length === 0 ? (
                        <p className="muted-copy">No outgoing links.</p>
                      ) : (
                        details.related_pages.map((reference) => (
                          <button
                            type="button"
                            key={`${reference.slug}-${reference.label}`}
                            onClick={() => selectPage(reference.slug)}
                          >
                            <span>{reference.title}</span>
                            <small>{reference.label}</small>
                          </button>
                        ))
                      )}
                    </div>

                    <div className="relationship-group">
                      <h4>Backlinks</h4>
                      {details.backlinks.length === 0 ? (
                        <p className="muted-copy">No backlinks yet.</p>
                      ) : (
                        details.backlinks.map((reference) => (
                          <button
                            type="button"
                            key={`${reference.slug}-${reference.label}`}
                            onClick={() => selectPage(reference.slug)}
                          >
                            <span>{reference.title}</span>
                            <small>{reference.label}</small>
                          </button>
                        ))
                      )}
                    </div>
                  </section>
                </div>

                <section className="revision-section">
                  <div className="section-heading-row">
                    <div>
                      <p className="eyebrow">Revision history</p>
                      <h3>How this page evolved</h3>
                    </div>
                    <History size={20} />
                  </div>

                  {revisions.length === 0 ? (
                    <p className="muted-copy">
                      No revisions are available for this page.
                    </p>
                  ) : (
                    <div className="revision-list">
                      {revisions.map((revision) => (
                        <article key={revision.id}>
                          <span className="revision-number">
                            v{revision.revision_number}
                          </span>
                          <div>
                            <strong>{revision.operation}</strong>
                            <p>{revision.summary}</p>
                            <small>{formatDate(revision.created_at)}</small>
                            <button
                              type="button"
                              className="revision-action-button"
                              onClick={() =>
                                void openRevisionDiff(revision)
                              }
                            >
                              <GitCompareArrows size={15} />
                              View changes
                            </button>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </section>
              </article>
            ) : (
              <div className="empty-detail-state">
                <BookOpen size={28} />
                <h2>Select a Wiki page</h2>
                <p>Choose a page from the list to open its content.</p>
              </div>
            )}
          </main>
          </div>
        </div>
      )}

      <SourcePreviewDrawer
        isOpen={isSourcePreviewOpen}
        isLoading={isSourcePreviewLoading}
        error={sourcePreviewError}
        content={sourcePreviewContent}
        onClose={() => setIsSourcePreviewOpen(false)}
      />

      <RevisionDiffDrawer
        isOpen={isRevisionDiffOpen}
        isLoading={isRevisionDiffLoading}
        isRestoring={isRestoringRevision}
        error={revisionActionError}
        diff={revisionDiff}
        onRestore={() => setIsRestoreConfirmOpen(true)}
        onClose={() => setIsRevisionDiffOpen(false)}
      />

      <ConfirmDialog
        isOpen={isRestoreConfirmOpen}
        title="Restore this Wiki revision?"
        description={
          selectedRevision
            ? `Version ${selectedRevision.revision_number} will become the current page. The current version will remain in history.`
            : "The selected revision will become current."
        }
        confirmLabel="Restore revision"
        isBusy={isRestoringRevision}
        onConfirm={() => void restoreSelectedRevision()}
        onClose={() => setIsRestoreConfirmOpen(false)}
      />
    </section>
  );
}
