import {
  BadgeCheck,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Link,
  useSearchParams,
} from "react-router-dom";

import {
  confirmEmailVerification,
} from "../api/auth";
import {
  getApiErrorMessage,
} from "../api/errors";
import FeedbackBanner from "../components/FeedbackBanner";
import {
  useAuth,
} from "../context/AuthContext";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = useMemo(
    () => searchParams.get("token") ?? "",
    [searchParams],
  );
  const { isAuthenticated, setUser } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    async function verify() {
      if (!token) {
        setError("The verification link is incomplete.");
        setIsLoading(false);
        return;
      }

      try {
        const user = await confirmEmailVerification(token);
        if (isAuthenticated) {
          setUser(user);
        }
        setVerified(true);
      } catch (requestError) {
        setError(getApiErrorMessage(requestError));
      } finally {
        setIsLoading(false);
      }
    }

    void verify();
  }, [isAuthenticated, setUser, token]);

  return (
    <main className="auth-layout auth-layout-single">
      <section className="auth-form-panel">
        <div className="auth-card verification-card">
          <span className="auth-icon-badge">
            <BadgeCheck size={24} />
          </span>
          <div className="auth-card-header">
            <p className="eyebrow">Email verification</p>
            <h1>
              {isLoading
                ? "Verifying your email..."
                : verified
                  ? "Email verified"
                  : "Verification failed"}
            </h1>
          </div>

          {verified && (
            <FeedbackBanner
              kind="success"
              message="Your email address is now verified."
            />
          )}
          {error && (
            <FeedbackBanner kind="error" message={error} />
          )}

          {!isLoading && (
            <Link
              className="primary-button full-width"
              to={isAuthenticated ? "/profile" : "/"}
            >
              {isAuthenticated ? "Return to profile" : "Sign in"}
            </Link>
          )}
        </div>
      </section>
    </main>
  );
}
