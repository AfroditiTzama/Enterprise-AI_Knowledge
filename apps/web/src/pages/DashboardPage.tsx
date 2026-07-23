import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Circle,
  FileText,
  MessageSquareText,
  Network,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Upload,
  WalletCards,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  listDocuments,
  type DocumentItem,
} from "../api/documents";
import {
  listProcessingJobs,
  type ProcessingJob,
} from "../api/jobs";
import { getApiErrorMessage } from "../api/errors";
import { getUsageSummary, type UsageSummary } from "../api/usage";
import { listWikiPages, type WikiPageItem } from "../api/wiki";
import FeedbackBanner from "../components/FeedbackBanner";
import { useAuth } from "../context/AuthContext";

interface DashboardData {
  documents: DocumentItem[];
  jobs: ProcessingJob[];
  wikiPages: WikiPageItem[];
  usage: UsageSummary;
}

const emptyUsage: UsageSummary = {
  days: 30,
  requests: 0,
  cache_hits: 0,
  input_tokens: 0,
  output_tokens: 0,
  estimated_cost_usd: 0,
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData>({
    documents: [],
    jobs: [],
    wikiPages: [],
    usage: emptyUsage,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const [documents, jobs, wikiPages, usage] = await Promise.all([
        listDocuments(),
        listProcessingJobs(),
        listWikiPages(),
        getUsageSummary(),
      ]);
      setData({ documents, jobs, wikiPages, usage });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const processedDocuments = data.documents.filter(
    (document) => document.status === "PROCESSED",
  ).length;
  const activeJobs = data.jobs.filter(
    (job) => job.status === "QUEUED" || job.status === "RUNNING",
  ).length;
  const failedJobs = data.jobs.filter(
    (job) => job.status === "FAILED",
  ).length;
  const hasAsked = localStorage.getItem("knowledge_ai_has_asked") === "true";

  const onboardingSteps = useMemo(
    () => [
      {
        label: "Upload a document",
        description: "Add a PDF, DOCX or TXT file.",
        complete: data.documents.length > 0,
        action: () => navigate("/documents"),
        actionLabel: "Open Documents",
      },
      {
        label: "Process the document",
        description: "Extract, structure and index its content.",
        complete: processedDocuments > 0,
        action: () => navigate("/documents"),
        actionLabel: "Process document",
      },
      {
        label: "Build your Wiki",
        description: "Create connected pages with traceable sources.",
        complete: data.wikiPages.length > 0,
        action: () => navigate("/documents"),
        actionLabel: "Build Wiki",
      },
      {
        label: "Ask the Assistant",
        description: "Use hybrid retrieval with citations.",
        complete: hasAsked,
        action: () => navigate("/assistant"),
        actionLabel: "Ask a question",
      },
    ],
    [data.documents.length, data.wikiPages.length, hasAsked, navigate, processedDocuments],
  );

  const completedSteps = onboardingSteps.filter(
    (step) => step.complete,
  ).length;

  return (
    <section className="page-container">
      <header className="page-header">
        <div>
          <p className="eyebrow">Workspace overview</p>
          <h1>Welcome back{user?.full_name ? `, ${user.full_name}` : ""}</h1>
          <p>
            See what is ready, what needs attention and the clearest next
            action for your knowledge workspace.
          </p>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={() => void load()}
          disabled={isLoading}
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </header>

      {error && (
        <FeedbackBanner
          kind="error"
          message={error}
          onRetry={() => void load()}
        />
      )}

      <section className="dashboard-metric-grid" aria-label="Workspace statistics">
        <article className="dashboard-metric-card">
          <FileText size={22} />
          <div><strong>{data.documents.length}</strong><span>Documents</span></div>
          <small>{processedDocuments} ready</small>
        </article>
        <article className="dashboard-metric-card">
          <BookOpen size={22} />
          <div><strong>{data.wikiPages.length}</strong><span>Wiki pages</span></div>
          <small>Connected knowledge</small>
        </article>
        <article className="dashboard-metric-card">
          <Sparkles size={22} />
          <div><strong>{activeJobs}</strong><span>Active jobs</span></div>
          <small>{failedJobs ? `${failedJobs} need retry` : "No failures"}</small>
        </article>
        <article className="dashboard-metric-card">
          <WalletCards size={22} />
          <div>
            <strong>${data.usage.estimated_cost_usd.toFixed(4)}</strong>
            <span>30-day LLM cost</span>
          </div>
          <small>{data.usage.cache_hits} cache hits</small>
        </article>
      </section>

      <div className="dashboard-layout-grid">
        <section className="surface-card onboarding-card">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Getting started</p>
              <h2>{completedSteps}/4 steps complete</h2>
              <p>Follow this path so you never have to guess what comes next.</p>
            </div>
            <ShieldCheck size={24} />
          </div>
          <div className="onboarding-progress" aria-hidden="true">
            <span style={{ width: `${completedSteps * 25}%` }} />
          </div>
          <div className="onboarding-list">
            {onboardingSteps.map((step) => (
              <article className="onboarding-row" key={step.label}>
                {step.complete ? (
                  <CheckCircle2 className="success-icon" size={21} />
                ) : (
                  <Circle size={21} />
                )}
                <div>
                  <strong>{step.label}</strong>
                  <p>{step.description}</p>
                </div>
                <button
                  type="button"
                  className={step.complete ? "tertiary-button" : "secondary-button compact"}
                  onClick={step.action}
                >
                  {step.complete ? "Review" : step.actionLabel}
                  <ArrowRight size={16} />
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="surface-card quick-actions-card">
          <p className="eyebrow">Quick actions</p>
          <h2>What would you like to do?</h2>
          <div className="quick-action-list">
            <button type="button" onClick={() => navigate("/documents") }>
              <Upload size={20} />
              <span><strong>Upload or process</strong><small>Manage source documents</small></span>
              <ArrowRight size={17} />
            </button>
            <button type="button" onClick={() => navigate("/assistant") }>
              <MessageSquareText size={20} />
              <span><strong>Ask the Assistant</strong><small>Search all or selected knowledge</small></span>
              <ArrowRight size={17} />
            </button>
            <button type="button" onClick={() => navigate("/wiki") }>
              <BookOpen size={20} />
              <span><strong>Review the Wiki</strong><small>Inspect claims, sources and quality</small></span>
              <ArrowRight size={17} />
            </button>
            <button type="button" onClick={() => navigate("/wiki/graph") }>
              <Network size={20} />
              <span><strong>Explore relationships</strong><small>Open the knowledge graph</small></span>
              <ArrowRight size={17} />
            </button>
          </div>
        </section>
      </div>
    </section>
  );
}
