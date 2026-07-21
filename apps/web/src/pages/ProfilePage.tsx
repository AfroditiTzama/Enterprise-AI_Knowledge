import {
  BookOpen,
  CalendarDays,
  CheckCircle2,
  FileText,
  LogOut,
  Mail,
  Monitor,
  Moon,
  Sun,
  UserRound,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getCurrentUser,
  type CurrentUser,
} from "../api/auth";
import {
  listDocuments,
} from "../api/documents";
import {
  getApiErrorMessage,
} from "../api/errors";
import {
  withApiRetry,
} from "../api/retry";
import {
  listWikiPages,
} from "../api/wiki";
import FeedbackBanner from "../components/FeedbackBanner";
import {
  useAuth,
} from "../context/AuthContext";
import {
  useTheme,
  type ThemePreference,
} from "../context/ThemeContext";

interface ProfileStats {
  documents: number;
  wikiPages: number;
}

const themeOptions: Array<{
  value: ThemePreference;
  label: string;
  description: string;
  icon: typeof Sun;
}> = [
  {
    value: "light",
    label: "Light",
    description: "Bright, calm workspace.",
    icon: Sun,
  },
  {
    value: "dark",
    label: "Dark",
    description: "Reduced glare in low light.",
    icon: Moon,
  },
  {
    value: "system",
    label: "System",
    description: "Follow your device setting.",
    icon: Monitor,
  },
];

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "long",
  }).format(new Date(value));
}

export default function ProfilePage() {
  const { signOut } = useAuth();
  const { preference, setPreference } = useTheme();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [stats, setStats] = useState<ProfileStats>({
    documents: 0,
    wikiPages: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [error, setError] = useState("");

  const loadProfile = useCallback(async () => {
    setError("");
    setIsLoading(true);
    setIsRetrying(false);

    try {
      const [currentUser, documents, pages] = await withApiRetry(
        () =>
          Promise.all([
            getCurrentUser(),
            listDocuments(),
            listWikiPages(),
          ]),
        {
          retries: 2,
          onRetry: () => setIsRetrying(true),
        },
      );

      setUser(currentUser);
      setStats({
        documents: documents.length,
        wikiPages: pages.length,
      });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsLoading(false);
      setIsRetrying(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  return (
    <section className="page-container profile-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Account & preferences</p>
          <h1>My Profile</h1>
          <p>
            Review your account and choose how your workspace looks.
          </p>
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
          onRetry={() => void loadProfile()}
        />
      )}

      {isLoading && !isRetrying ? (
        <div className="skeleton-stack" aria-label="Loading profile">
          <div className="skeleton-card" />
          <div className="skeleton-card" />
        </div>
      ) : user ? (
        <div className="profile-grid">
          <section className="surface-card profile-summary-card">
            <div className="profile-avatar">
              <UserRound size={30} />
            </div>

            <div>
              <p className="eyebrow">Signed in as</p>
              <h2>{user.full_name}</h2>
              <p className="profile-email">
                <Mail size={16} />
                {user.email}
              </p>
            </div>

            <div className="profile-details">
              <span>
                <CheckCircle2 size={17} />
                {user.is_active ? "Active account" : "Inactive account"}
              </span>
              <span>
                <CalendarDays size={17} />
                Joined {formatDate(user.created_at)}
              </span>
            </div>
          </section>

          <section className="surface-card profile-stats-card">
            <div>
              <FileText size={21} />
              <strong>{stats.documents}</strong>
              <span>Documents</span>
            </div>
            <div>
              <BookOpen size={21} />
              <strong>{stats.wikiPages}</strong>
              <span>Wiki pages</span>
            </div>
          </section>

          <section className="surface-card appearance-card">
            <div className="section-heading-row">
              <div>
                <p className="eyebrow">Appearance</p>
                <h2>Choose your theme</h2>
                <p>
                  Your preference stays saved on this device.
                </p>
              </div>
            </div>

            <div className="theme-option-grid">
              {themeOptions.map((option) => {
                const Icon = option.icon;
                const isSelected = preference === option.value;

                return (
                  <button
                    type="button"
                    key={option.value}
                    className={
                      isSelected
                        ? "theme-option selected"
                        : "theme-option"
                    }
                    onClick={() => setPreference(option.value)}
                    aria-pressed={isSelected}
                  >
                    <Icon size={22} />
                    <strong>{option.label}</strong>
                    <span>{option.description}</span>
                    {isSelected && <CheckCircle2 size={18} />}
                  </button>
                );
              })}
            </div>
          </section>

          <section className="surface-card account-actions-card">
            <div>
              <h2>Account session</h2>
              <p>
                Sign out safely from this device. You can sign in again
                immediately without refreshing the page.
              </p>
            </div>

            <button
              type="button"
              className="secondary-button"
              onClick={signOut}
            >
              <LogOut size={18} />
              Sign out
            </button>
          </section>
        </div>
      ) : null}
    </section>
  );
}
