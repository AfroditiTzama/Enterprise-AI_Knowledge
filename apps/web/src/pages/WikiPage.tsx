import {
  BookOpen,
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
  getApiErrorMessage,
} from "../api/errors";
import {
  listWikiPages,
  type WikiPageItem,
} from "../api/wiki";

export default function WikiPage() {
  const [pages, setPages] =
    useState<WikiPageItem[]>([]);
  const [selectedSlug, setSelectedSlug] =
    useState("");
  const [query, setQuery] =
    useState("");
  const [isLoading, setIsLoading] =
    useState(true);
  const [error, setError] =
    useState("");

  useEffect(() => {
    async function load() {
      try {
        const items = await listWikiPages();
        setPages(items);

        if (items.length > 0) {
          setSelectedSlug(items[0].slug);
        }
      } catch (requestError) {
        setError(
          getApiErrorMessage(requestError),
        );
      } finally {
        setIsLoading(false);
      }
    }

    void load();
  }, []);

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

  const selectedPage =
    pages.find(
      (page) => page.slug === selectedSlug,
    ) ?? null;

  return (
    <section className="page-container wiki-page-layout">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Compiled knowledge
          </p>

          <h1>Internal Wiki</h1>

          <p>
            Browse the structured knowledge
            generated from your documents.
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
                  setQuery(
                    event.target.value,
                  )
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
            {selectedPage ? (
              <>
                <p className="wiki-document-label">
                  Document{" "}
                  {selectedPage.document_id.slice(
                    0,
                    8,
                  )}
                </p>

                <h2>{selectedPage.title}</h2>

                <p className="wiki-summary">
                  {selectedPage.summary}
                </p>

                <div className="markdown-body">
                  <ReactMarkdown>
                    {
                      selectedPage.content_markdown
                    }
                  </ReactMarkdown>
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
    </section>
  );
}
