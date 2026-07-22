import {
  ArrowLeft,
  LockKeyhole,
} from "lucide-react";
import {
  useMemo,
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  useSearchParams,
} from "react-router-dom";

import {
  confirmPasswordReset,
} from "../api/auth";
import {
  getApiErrorMessage,
} from "../api/errors";
import FeedbackBanner from "../components/FeedbackBanner";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = useMemo(
    () => searchParams.get("token") ?? "",
    [searchParams],
  );
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError("");

    if (!token) {
      setError("The password reset link is incomplete.");
      return;
    }
    if (password !== confirmation) {
      setError("The two passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await confirmPasswordReset({
        token,
        new_password: password,
      });
      setCompleted(true);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="auth-layout auth-layout-single">
      <section className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-card-header">
            <p className="eyebrow">Secure recovery</p>
            <h1>Choose a new password</h1>
            <p>
              Use at least 10 characters with a letter and a number.
            </p>
          </div>

          {completed ? (
            <>
              <FeedbackBanner
                kind="success"
                message="Your password has been reset successfully."
              />
              <Link className="primary-button full-width" to="/">
                Sign in
              </Link>
            </>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              <label>
                New password
                <div className="input-wrapper">
                  <LockKeyhole size={18} />
                  <input
                    type="password"
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    minLength={10}
                    autoComplete="new-password"
                    required
                  />
                </div>
              </label>

              <label>
                Confirm new password
                <div className="input-wrapper">
                  <LockKeyhole size={18} />
                  <input
                    type="password"
                    value={confirmation}
                    onChange={(event) =>
                      setConfirmation(event.target.value)
                    }
                    minLength={10}
                    autoComplete="new-password"
                    required
                  />
                </div>
              </label>

              {error && (
                <FeedbackBanner kind="error" message={error} />
              )}

              <button
                type="submit"
                className="primary-button full-width"
                disabled={isLoading}
              >
                {isLoading ? "Updating..." : "Update password"}
              </button>
            </form>
          )}

          <Link className="auth-back-link" to="/">
            <ArrowLeft size={17} />
            Back to sign in
          </Link>
        </div>
      </section>
    </main>
  );
}
