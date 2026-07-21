import {
  ArrowLeftRight,
  BookOpen,
  FileText,
  History,
  Link2,
  LoaderCircle,
  Search,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import {
  useSearchParams,
} from "react-router-dom";

import {
  getDocumentChunkPreview,
} from "../api/documents";
import {
  getApiErrorMessage,
} from "../api/errors";
import SourcePreviewDrawer, {
  type SourcePreviewContent,
} from "../components/SourcePreviewDrawer";
import {
  getWikiPage,
  listWikiPageRevisions,
  listWikiPages,
  type WikiPageDetails,
  type WikiPageItem,
  type WikiPageReferenceItem,
  type WikiPageRevisionItem,
  type WikiPageSourceItem,
} from "../api/wiki";

function formatRevisionDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(value));
}

export default function WikiPage() {
  const [searchParams] = useSearchParams();

  const requestedSlug =
    searchParams.get("slug");
  const [pages, setPages] =
    useState<WikiPageItem[]>([]);
  const [selectedSlug, setSelectedSlug] =
    useState("");
  const [pageDetails, setPageDetails] =
    useState<WikiPageDetails | null>(null);
  const [revisions, setRevisions] =
    useState<WikiPageRevisionItem[]>([]);
  const [query, setQuery] =
    useState("");
  const [isLoading, setIsLoading] =
    useState(true);
  const [
    isLoadingDetails,
    setIsLoadingDetails,
  ] = useState(false);
  const [error, setError] =
    useState("");
  const [detailsError, setDetailsError] =
    useState("");
  const [
    isSourcePreviewOpen,
    setIsSourcePreviewOpen,
  ] = useState(false);
  const [
    isSourcePreviewLoading,
    setIsSourcePreviewLoading,
  ] = useState(false);
  const [
    sourcePreviewError,
    setSourcePreviewError,
  ] = useState("");
  const [
    sourcePreviewContent,
    setSourcePreviewContent,
  ] = useState<SourcePreviewContent | null>(
    null,
  );

  useEffect(() => {
    async function loadPages() {
      try {
        setError("");

        const items = await listWikiPages();

        setPages(items);

        if (items.length > 0) {
          const requestedPage = items.find(
            (item) =>
              item.slug === requestedSlug,
          );

          setSelectedSlug(
            requestedPage?.slug ??
              items[0].slug,
          );
        }
      } catch (requestError) {
        setError(
          getApiErrorMessage(requestError),
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadPages();
  }, [requestedSlug]);

  useEffect(() => {
    if (!selectedSlug) {
      setPageDetails(null);
      setRevisions([]);
      return;
    }

    let isCurrentRequest = true;

    async function loadDetails() {
      setIsLoadingDetails(true);
      setDetailsError("");

      try {
        const [
          details,
          revisionItems,
        ] = await Promise.all([
          getWikiPage(selectedSlug),
          listWikiPageRevisions(
            selectedSlug,
          ),
        ]);

        if (isCurrentRequest) {
          setPageDetails(details);
          setRevisions(revisionItems);
        }
      } catch (requestError) {
        if (isCurrentRequest) {
          setPageDetails(null);
          setRevisions([]);
          setDetailsError(
            getApiErrorMessage(requestError),
          );
        }
      } finally {
        if (isCurrentRequest) {
          setIsLoadingDetails(false);
        }
      }
    }

    void loadDetails();

    return () => {
      isCurrentRequest = false;
    };
  }, [selectedSlug]);

  const filteredPages = useMemo(() => {
    const normalizedQuery =
      query.trim().toLowerCase();

    if (!normalizedQuery) {
      return pages;
    }

    return pages.filter((page) => {
      return [
        page.title,
        page.summary,
        page.content_markdown,
      ].some((value) =>
        value
          .toLowerCase()
          .includes(normalizedQuery),
      );
    });
  }, [pages, query]);

  function openRelatedPage(
    reference: WikiPageReferenceItem,
  ) {
    setSelectedSlug(reference.slug);
  }

  async function openSourcePreview(
    source: WikiPageSourceItem,
  ) {
    setIsSourcePreviewOpen(true);
    setIsSourcePreviewLoading(true);
    setSourcePreviewError("");
    setSourcePreviewContent(null);

    try {
      const preview =
        await getDocumentChunkPreview(
          source.chunk_id,
        );

      setSourcePreviewContent({
        title: preview.document_filename,
        sourceLabel: "Original document",
        locationLabel:
          preview.page_number !== null
            ? `Page ${preview.page_number}`
            : `Chunk ${
                preview.chunk_index + 1
              }`,
        text: preview.text,
      });
    } catch (requestError) {
      setSourcePreviewError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsSourcePreviewLoading(false);
    }
  }

  function closeSourcePreview() {
    setIsSourcePreviewOpen(false);
  }

  return (
    <section className="page-container wiki-page-layout">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Compiled knowledge
          </p>

          <h1>Internal Wiki</h1>

          <p>
            Browse structured, connected and
            versioned knowledge generated from
            your documents.
          </p>
        </div>
      </header>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="loading-panel">
          <LoaderCircle
            className="spin"
            size={28}
          />
          Loading Wiki pages...
        </div>
      ) : pages.length === 0 ? (
        <section className="empty-state">
          <div className="empty-icon">
            <BookOpen size={30} />
          </div>

          <h2>No Wiki pages yet</h2>

          <p>
            Process a document and select
            Build Wiki from the Documents page.
          </p>
        </section>
      ) : (
        <div className="wiki-workspace">
          <aside className="wiki-index">
            <div className="search-box">
              <Search size={17} />

              <input
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                placeholder="Search Wiki pages"
              />
            </div>

            <div className="wiki-page-list">
              {filteredPages.map((page) => (
                <button
                  type="button"
                  key={page.id}
                  className={
                    page.slug === selectedSlug
                      ? "wiki-page-button active"
                      : "wiki-page-button"
                  }
                  onClick={() =>
                    setSelectedSlug(page.slug)
                  }
                >
                  <strong>{page.title}</strong>
                  <span>{page.summary}</span>
                </button>
              ))}
            </div>
          </aside>

          <article className="wiki-article">
            {detailsError && (
              <div className="error-message">
                {detailsError}
              </div>
            )}

            {isLoadingDetails ? (
              <div className="loading-panel">
                <LoaderCircle
                  className="spin"
                  size={26}
                />
                Loading Wiki page...
              </div>
            ) : pageDetails ? (
              <>
                <p className="wiki-document-label">
                  {pageDetails.document_id
                    ? `Document ${pageDetails.document_id.slice(
                        0,
                        8,
                      )}`
                    : "Global knowledge"}
                </p>

                <h2>{pageDetails.title}</h2>

                <p className="wiki-summary">
                  {pageDetails.summary}
                </p>

                <div className="markdown-body">
                  <ReactMarkdown>
                    {
                      pageDetails.content_markdown
                    }
                  </ReactMarkdown>
                </div>

                <div className="wiki-details-grid">
                  {pageDetails.related_pages
                    .length > 0 && (
                    <section className="wiki-detail-section">
                      <h3>
                        <Link2 size={18} />
                        Related pages
                      </h3>

                      <div className="wiki-reference-list">
                        {pageDetails.related_pages.map(
                          (reference) => (
                            <button
                              type="button"
                              key={reference.page_id}
                              className="wiki-reference-button"
                              onClick={() =>
                                openRelatedPage(
                                  reference,
                                )
                              }
                            >
                              <strong>
                                {reference.title}
                              </strong>

                              <span>
                                {reference.label}
                              </span>
                            </button>
                          ),
                        )}
                      </div>
                    </section>
                  )}

                  {pageDetails.backlinks.length >
                    0 && (
                    <section className="wiki-detail-section">
                      <h3>
                        <ArrowLeftRight size={18} />
                        Referenced by
                      </h3>

                      <div className="wiki-reference-list">
                        {pageDetails.backlinks.map(
                          (reference) => (
                            <button
                              type="button"
                              key={reference.page_id}
                              className="wiki-reference-button"
                              onClick={() =>
                                openRelatedPage(
                                  reference,
                                )
                              }
                            >
                              <strong>
                                {reference.title}
                              </strong>

                              <span>
                                {reference.label}
                              </span>
                            </button>
                          ),
                        )}
                      </div>
                    </section>
                  )}

                  {pageDetails.sources.length >
                    0 && (
                    <section className="wiki-detail-section wiki-source-section">
                      <h3>
                        <FileText size={18} />
                        Sources
                      </h3>

                      <div className="wiki-source-list">
                        {pageDetails.sources.map(
                          (source) => (
                            <button
                              type="button"
                              key={source.chunk_id}
                              className="wiki-source-card"
                              onClick={() =>
                                void openSourcePreview(
                                  source,
                                )
                              }
                            >
                              <FileText size={18} />

                              <div>
                                <strong>
                                  {
                                    source.document_filename
                                  }
                                </strong>

                                <span>
                                  {source.page_number !==
                                  null
                                    ? `Page ${source.page_number}`
                                    : `Chunk ${
                                        source.chunk_index +
                                        1
                                      }`}
                                </span>
                              </div>
                            </button>
                          ),
                        )}
                      </div>
                    </section>
                  )}

                  <section className="wiki-detail-section wiki-history-section">
                    <h3>
                      <History size={18} />
                      Version history
                    </h3>

                    {revisions.length === 0 ? (
                      <p className="wiki-history-empty">
                        No revisions have been
                        recorded yet. Build this
                        document Wiki again to
                        initialize its history.
                      </p>
                    ) : (
                      <div className="wiki-revision-list">
                        {revisions.map(
                          (revision) => (
                            <details
                              key={revision.id}
                              className="wiki-revision-card"
                            >
                              <summary>
                                <span>
                                  Revision{" "}
                                  {
                                    revision.revision_number
                                  }
                                </span>

                                <span
                                  className={
                                    `wiki-revision-operation ` +
                                    `revision-${revision.operation.toLowerCase()}`
                                  }
                                >
                                  {
                                    revision.operation
                                  }
                                </span>

                                <time>
                                  {formatRevisionDate(
                                    revision.created_at,
                                  )}
                                </time>
                              </summary>

                              <div className="wiki-revision-content">
                                <h4>
                                  {revision.title}
                                </h4>

                                <p>
                                  {revision.summary}
                                </p>

                                <div className="markdown-body">
                                  <ReactMarkdown>
                                    {
                                      revision.content_markdown
                                    }
                                  </ReactMarkdown>
                                </div>

                                {revision.triggering_document_id && (
                                  <small>
                                    Triggered by document{" "}
                                    {revision.triggering_document_id.slice(
                                      0,
                                      8,
                                    )}
                                  </small>
                                )}
                              </div>
                            </details>
                          ),
                        )}
                      </div>
                    )}
                  </section>
                </div>
              </>
            ) : (
              <div className="empty-article">
                Select a Wiki page.
              </div>
            )}
          </article>
        </div>
      )}
      <SourcePreviewDrawer
        isOpen={isSourcePreviewOpen}
        isLoading={isSourcePreviewLoading}
        error={sourcePreviewError}
        content={sourcePreviewContent}
        onClose={closeSourcePreview}
      />
    </section>
  );
}
