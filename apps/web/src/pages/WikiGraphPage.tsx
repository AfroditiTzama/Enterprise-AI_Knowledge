import {
  BookOpen,
  LoaderCircle,
  Maximize2,
  Minimize2,
  Network,
  RotateCcw,
  Search,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  getApiErrorMessage,
} from "../api/errors";
import {
  withApiRetry,
} from "../api/retry";
import {
  getWikiPage,
  listWikiPages,
} from "../api/wiki";
import FeedbackBanner from "../components/FeedbackBanner";

interface GraphNode {
  id: string;
  slug: string;
  title: string;
  summary: string;
  isGlobal: boolean;
  x: number;
  y: number;
}

interface GraphEdge {
  id: string;
  sourceSlug: string;
  targetSlug: string;
  label: string;
}

interface DragState {
  slug: string;
  pointerId: number;
  lastX: number;
  lastY: number;
  moved: boolean;
}

interface PanState {
  pointerId: number;
  lastX: number;
  lastY: number;
}

const sceneWidth = 1400;
const sceneHeight = 850;

function createNodePositions(
  count: number,
): Array<{ x: number; y: number }> {
  if (count === 0) {
    return [];
  }

  if (count === 1) {
    return [
      {
        x: sceneWidth / 2,
        y: sceneHeight / 2,
      },
    ];
  }

  const centerX = sceneWidth / 2;
  const centerY = sceneHeight / 2;
  const positions: Array<{
    x: number;
    y: number;
  }> = [];

  const nodesPerRing = 10;

  for (let index = 0; index < count; index += 1) {
    const ringIndex = Math.floor(
      index / nodesPerRing,
    );

    const ringStart =
      ringIndex * nodesPerRing;

    const remaining =
      count - ringStart;

    const nodesInRing = Math.min(
      nodesPerRing,
      remaining,
    );

    const positionInRing =
      index - ringStart;

    const radius =
      230 + ringIndex * 150;

    const angle =
      (
        positionInRing /
        nodesInRing
      ) *
        Math.PI *
        2 -
      Math.PI / 2;

    positions.push({
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    });
  }

  return positions;
}

export default function WikiGraphPage() {
  const navigate = useNavigate();

  const [nodes, setNodes] =
    useState<GraphNode[]>([]);

  const [edges, setEdges] =
    useState<GraphEdge[]>([]);

  const [query, setQuery] =
    useState("");

  const [zoom, setZoom] =
    useState(1);

  const [isFullscreen, setIsFullscreen] =
    useState(false);

  const [pan, setPan] =
    useState({
      x: 0,
      y: 0,
    });

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [isRetrying, setIsRetrying] =
    useState(false);

  const [reloadKey, setReloadKey] =
    useState(0);

  const graphPanelRef =
    useRef<HTMLDivElement | null>(null);

  const initialNodesRef =
    useRef<GraphNode[]>([]);

  const dragState =
    useRef<DragState | null>(null);

  const panState =
    useRef<PanState | null>(null);

  useEffect(() => {
    let isCurrentRequest = true;

    async function loadGraph() {
      setError("");
      setIsLoading(true);
      setIsRetrying(false);

      try {
        const [pages, details] = await withApiRetry(
          async () => {
            const wikiPages = await listWikiPages();
            const wikiDetails = await Promise.all(
              wikiPages.map((page) =>
                getWikiPage(page.slug),
              ),
            );

            return [wikiPages, wikiDetails] as const;
          },
          {
            retries: 2,
            onRetry: () => {
              if (isCurrentRequest) {
                setIsRetrying(true);
              }
            },
          },
        );

        if (!isCurrentRequest) {
          return;
        }

        const positions = createNodePositions(pages.length);
        const graphNodes = pages.map(
          (page, index): GraphNode => ({
            id: page.id,
            slug: page.slug,
            title: page.title,
            summary: page.summary,
            isGlobal: page.document_id === null,
            x: positions[index].x,
            y: positions[index].y,
          }),
        );
        const edgeMap = new Map<string, GraphEdge>();

        for (const detail of details) {
          for (const related of detail.related_pages) {
            const edgeId = `${detail.slug}:${related.slug}`;
            edgeMap.set(edgeId, {
              id: edgeId,
              sourceSlug: detail.slug,
              targetSlug: related.slug,
              label: related.label,
            });
          }

          for (const backlink of detail.backlinks) {
            const edgeId = `${backlink.slug}:${detail.slug}`;

            if (!edgeMap.has(edgeId)) {
              edgeMap.set(edgeId, {
                id: edgeId,
                sourceSlug: backlink.slug,
                targetSlug: detail.slug,
                label: backlink.label,
              });
            }
          }
        }

        initialNodesRef.current = graphNodes.map((node) => ({
          ...node,
        }));
        setNodes(graphNodes.map((node) => ({ ...node })));
        setEdges(Array.from(edgeMap.values()));
      } catch (requestError) {
        if (isCurrentRequest) {
          setError(getApiErrorMessage(requestError));
          setNodes([]);
          setEdges([]);
        }
      } finally {
        if (isCurrentRequest) {
          setIsLoading(false);
          setIsRetrying(false);
        }
      }
    }

    void loadGraph();

    return () => {
      isCurrentRequest = false;
    };
  }, [reloadKey]);

  useEffect(() => {
    function handleFullscreenChange() {
      setIsFullscreen(
        document.fullscreenElement ===
          graphPanelRef.current,
      );
    }

    document.addEventListener(
      "fullscreenchange",
      handleFullscreenChange,
    );

    return () => {
      document.removeEventListener(
        "fullscreenchange",
        handleFullscreenChange,
      );
    };
  }, []);

  const visibleNodes = useMemo(() => {
    const normalizedQuery =
      query.trim().toLowerCase();

    if (!normalizedQuery) {
      return nodes;
    }

    return nodes.filter((node) =>
      [
        node.title,
        node.summary,
        node.slug,
      ].some((value) =>
        value
          .toLowerCase()
          .includes(normalizedQuery),
      ),
    );
  }, [nodes, query]);

  const visibleNodeSlugs = useMemo(
    () =>
      new Set(
        visibleNodes.map(
          (node) => node.slug,
        ),
      ),
    [visibleNodes],
  );

  const visibleEdges = useMemo(
    () =>
      edges.filter(
        (edge) =>
          visibleNodeSlugs.has(
            edge.sourceSlug,
          ) &&
          visibleNodeSlugs.has(
            edge.targetSlug,
          ),
      ),
    [edges, visibleNodeSlugs],
  );

  const nodeBySlug = useMemo(
    () =>
      new Map(
        nodes.map((node) => [
          node.slug,
          node,
        ]),
      ),
    [nodes],
  );

  function openWikiPage(
    slug: string,
  ) {
    navigate(
      `/wiki?slug=${encodeURIComponent(
        slug,
      )}`,
    );
  }

  function handleNodePointerDown(
    event: ReactPointerEvent<HTMLButtonElement>,
    node: GraphNode,
  ) {
    event.stopPropagation();

    event.currentTarget.setPointerCapture(
      event.pointerId,
    );

    dragState.current = {
      slug: node.slug,
      pointerId: event.pointerId,
      lastX: event.clientX,
      lastY: event.clientY,
      moved: false,
    };
  }

  function handleNodePointerMove(
    event: ReactPointerEvent<HTMLButtonElement>,
  ) {
    const currentDrag = dragState.current;

    if (
      currentDrag === null ||
      currentDrag.pointerId !==
        event.pointerId
    ) {
      return;
    }

    const deltaX =
      (
        event.clientX -
        currentDrag.lastX
      ) / zoom;

    const deltaY =
      (
        event.clientY -
        currentDrag.lastY
      ) / zoom;

    if (
      Math.abs(deltaX) > 1 ||
      Math.abs(deltaY) > 1
    ) {
      currentDrag.moved = true;
    }

    currentDrag.lastX = event.clientX;
    currentDrag.lastY = event.clientY;

    setNodes((currentNodes) =>
      currentNodes.map((node) =>
        node.slug === currentDrag.slug
          ? {
              ...node,
              x: node.x + deltaX,
              y: node.y + deltaY,
            }
          : node,
      ),
    );
  }

  function handleNodePointerUp(
    event: ReactPointerEvent<HTMLButtonElement>,
  ) {
    const currentDrag = dragState.current;

    if (
      currentDrag === null ||
      currentDrag.pointerId !==
        event.pointerId
    ) {
      return;
    }

    if (
      event.currentTarget.hasPointerCapture(
        event.pointerId,
      )
    ) {
      event.currentTarget.releasePointerCapture(
        event.pointerId,
      );
    }

    dragState.current = null;

    if (!currentDrag.moved) {
      openWikiPage(currentDrag.slug);
    }
  }

  function handleViewportPointerDown(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    const target =
      event.target as HTMLElement;

    if (
      target.closest(
        ".wiki-graph-node",
      ) ||
      target.closest(
        ".wiki-graph-controls",
      )
    ) {
      return;
    }

    event.currentTarget.setPointerCapture(
      event.pointerId,
    );

    panState.current = {
      pointerId: event.pointerId,
      lastX: event.clientX,
      lastY: event.clientY,
    };
  }

  function handleViewportPointerMove(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    const currentPan = panState.current;

    if (
      currentPan === null ||
      currentPan.pointerId !==
        event.pointerId
    ) {
      return;
    }

    const deltaX =
      event.clientX - currentPan.lastX;

    const deltaY =
      event.clientY - currentPan.lastY;

    currentPan.lastX = event.clientX;
    currentPan.lastY = event.clientY;

    setPan((currentPanValue) => ({
      x: currentPanValue.x + deltaX,
      y: currentPanValue.y + deltaY,
    }));
  }

  function handleViewportPointerUp(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    if (
      panState.current?.pointerId !==
      event.pointerId
    ) {
      return;
    }

    if (
      event.currentTarget.hasPointerCapture(
        event.pointerId,
      )
    ) {
      event.currentTarget.releasePointerCapture(
        event.pointerId,
      );
    }

    panState.current = null;
  }

  function resetView() {
    setQuery("");
    setNodes(
      initialNodesRef.current.map(
        (node) => ({
          ...node,
        }),
      ),
    );

    setZoom(1);

    setPan({
      x: 0,
      y: 0,
    });
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
        return;
      }

      if (!graphPanelRef.current) {
        return;
      }

      await graphPanelRef.current.requestFullscreen();
    } catch {
      setError(
        "Fullscreen mode could not be activated.",
      );
    }
  }

  return (
    <section className="page-container">
      <header className="page-header wiki-graph-header">
        <div>
          <p className="eyebrow">
            Knowledge relationships
          </p>

          <h1>Interactive Wiki Graph</h1>

          <p>
            Explore connected Wiki pages,
            drag nodes and open knowledge
            directly from the graph.
          </p>
        </div>

        <div className="wiki-graph-stats">
          <span>
            {visibleNodes.length} pages
          </span>

          <span>
            {visibleEdges.length} links
          </span>
        </div>
      </header>

      {isRetrying && (
        <FeedbackBanner
          kind="retrying"
          message="The server is waking up. Retrying…"
        />
      )}

      {error && !isRetrying && (
        <FeedbackBanner
          kind="error"
          message={error}
          onRetry={() =>
            setReloadKey((current) => current + 1)
          }
        />
      )}

      {isLoading && !isRetrying ? (
        <div className="loading-panel">
          <LoaderCircle
            className="spin"
            size={28}
          />
          Building knowledge graph...
        </div>
      ) : error ? null : nodes.length === 0 ? (
        <section className="empty-state">
          <div className="empty-icon">
            <Network size={30} />
          </div>

          <h2>No graph available</h2>

          <p>
            Build at least one Wiki page from
            the Documents section.
          </p>
        </section>
      ) : (
        <div
          ref={graphPanelRef}
          className="wiki-graph-panel"
        >
          <div className="wiki-graph-toolbar">
            <div className="search-box">
              <Search size={17} />

              <input
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                placeholder="Filter graph nodes"
              />
            </div>

            <div className="wiki-graph-legend">
              <span>
                <i className="global-node-dot" />
                Global page
              </span>

              <span>
                <i className="document-node-dot" />
                Document page
              </span>
            </div>
          </div>

          <div
            className="wiki-graph-viewport"
            onPointerDown={
              handleViewportPointerDown
            }
            onPointerMove={
              handleViewportPointerMove
            }
            onPointerUp={
              handleViewportPointerUp
            }
            onPointerCancel={
              handleViewportPointerUp
            }
          >
            <div className="wiki-graph-controls">
              <button
                type="button"
                onClick={() =>
                  setZoom((current) =>
                    Math.min(
                      1.8,
                      current + 0.15,
                    ),
                  )
                }
                aria-label="Zoom in"
              >
                <ZoomIn size={18} />
              </button>

              <button
                type="button"
                onClick={() =>
                  setZoom((current) =>
                    Math.max(
                      0.45,
                      current - 0.15,
                    ),
                  )
                }
                aria-label="Zoom out"
              >
                <ZoomOut size={18} />
              </button>

              <button
                type="button"
                onClick={resetView}
                aria-label="Reset graph view"
                title="Reset view"
              >
                <RotateCcw size={18} />
              </button>

              <button
                type="button"
                onClick={() =>
                  void toggleFullscreen()
                }
                aria-label={
                  isFullscreen
                    ? "Exit fullscreen"
                    : "Enter fullscreen"
                }
                title={
                  isFullscreen
                    ? "Exit fullscreen"
                    : "Enter fullscreen"
                }
              >
                {isFullscreen ? (
                  <Minimize2 size={18} />
                ) : (
                  <Maximize2 size={18} />
                )}
              </button>

              <span>
                {Math.round(zoom * 100)}%
              </span>
            </div>

            <div
              className="wiki-graph-scene"
              style={{
                width: sceneWidth,
                height: sceneHeight,
                transform:
                  `translate(${pan.x}px, ` +
                  `${pan.y}px) ` +
                  `scale(${zoom})`,
              }}
            >
              <svg
                className="wiki-graph-edges"
                width={sceneWidth}
                height={sceneHeight}
                aria-hidden="true"
              >
                <defs>
                  <marker
                    id="wiki-edge-arrow"
                    markerWidth="8"
                    markerHeight="8"
                    refX="7"
                    refY="4"
                    orient="auto"
                  >
                    <path
                      d="M0,0 L8,4 L0,8 Z"
                      className="wiki-edge-arrow"
                    />
                  </marker>
                </defs>

                {visibleEdges.map((edge) => {
                  const source =
                    nodeBySlug.get(
                      edge.sourceSlug,
                    );

                  const target =
                    nodeBySlug.get(
                      edge.targetSlug,
                    );

                  if (!source || !target) {
                    return null;
                  }

                  return (
                    <g key={edge.id}>
                      <line
                        x1={source.x}
                        y1={source.y}
                        x2={target.x}
                        y2={target.y}
                        markerEnd={
                          "url(#wiki-edge-arrow)"
                        }
                      />

                      <text
                        x={
                          (
                            source.x +
                            target.x
                          ) / 2
                        }
                        y={
                          (
                            source.y +
                            target.y
                          ) / 2 -
                          7
                        }
                      >
                        {edge.label}
                      </text>
                    </g>
                  );
                })}
              </svg>

              {visibleNodes.map((node) => (
                <button
                  type="button"
                  key={node.id}
                  className={
                    node.isGlobal
                      ? (
                        "wiki-graph-node " +
                        "global"
                      )
                      : (
                        "wiki-graph-node " +
                        "document"
                      )
                  }
                  style={{
                    left: node.x,
                    top: node.y,
                  }}
                  onPointerDown={(event) =>
                    handleNodePointerDown(
                      event,
                      node,
                    )
                  }
                  onPointerMove={
                    handleNodePointerMove
                  }
                  onPointerUp={
                    handleNodePointerUp
                  }
                  onPointerCancel={
                    handleNodePointerUp
                  }
                  aria-label={
                    `Open ${node.title}`
                  }
                >
                  <BookOpen size={18} />

                  <strong>
                    {node.title}
                  </strong>

                  <span>
                    {node.summary}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
