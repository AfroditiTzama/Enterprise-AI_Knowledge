import {
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
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
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
  listWikiPageRevisions,
  listWikiPages,
  type WikiPageDetails,
  type WikiPageItem,
  type WikiPageRevisionItem,
  type WikiPageSourceItem,
} from "../api/wiki";
import FeedbackBanner from "../components/FeedbackBanner";
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

  const loadPages = useCallback(async () => {
    setListError("");
    setIsListLoading(true);
    setIsRetrying(false);

    try {
      const items = await withApiRetry(listWikiPages, {
        retries: 2,
        onRetry: () => setIsRetrying(true),
      });

      setPages(items);

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

    if (!normalized) {
      return pages;
    }

    return pages.filter((page) =>
      [page.title, page.summary, page.slug].some((value) =>
        value.toLowerCase().includes(normalized),
      ),
    );
  }, [pages, query]);

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
                    <strong>{page.title}</strong>
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

                <div className="markdown-body">
                  <ReactMarkdown>{details.content_markdown}</ReactMarkdown>
                </div>

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
      )}

      <SourcePreviewDrawer
        isOpen={isSourcePreviewOpen}
        isLoading={isSourcePreviewLoading}
        error={sourcePreviewError}
        content={sourcePreviewContent}
        onClose={() => setIsSourcePreviewOpen(false)}
      />
    </section>
  );
}
