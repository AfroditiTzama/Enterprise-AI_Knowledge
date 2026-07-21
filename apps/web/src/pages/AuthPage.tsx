import {
  BrainCircuit,
  CheckCircle2,
  LockKeyhole,
  Mail,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useState,
  type FormEvent,
} from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  login,
  register,
} from "../api/auth";
import {
  getApiErrorMessage,
} from "../api/errors";
import FeedbackBanner from "../components/FeedbackBanner";
import {
  useAuth,
} from "../context/AuthContext";

type AuthMode = "login" | "register";

export default function AuthPage() {
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const [mode, setMode] = useState<AuthMode>("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const authNotice = sessionStorage.getItem("auth_notice");

    if (!authNotice) {
      return;
    }

    sessionStorage.removeItem("auth_notice");
    setNotice(authNotice);
  }, []);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError("");
    setNotice("");
    setIsLoading(true);

    try {
      if (mode === "register") {
        await register({
          full_name: fullName,
          email,
          password,
        });
      }

      const result = await login({ email, password });
      signIn(result.access_token);
      navigate("/dashboard", { replace: true });
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, {
          401: "Incorrect email or password.",
          409: "An account with this email already exists.",
          422: "Please check the information you entered.",
        }),
      );
    } finally {
      setIsLoading(false);
    }
  }

  function changeMode(newMode: AuthMode) {
    setMode(newMode);
    setError("");
    setNotice("");
  }

  return (
    <main className="auth-layout">
      <section className="auth-brand-panel">
        <div className="brand-mark">
          <BrainCircuit size={30} />
        </div>

        <p className="eyebrow">Enterprise AI</p>
        <h1>Turn documents into connected knowledge.</h1>
        <p className="brand-description">
          Upload files, build an intelligent Wiki and ask
          grounded questions with traceable sources.
        </p>

        <div className="feature-list auth-feature-list">
          {[
            "Document intelligence",
            "Connected Wiki pages",
            "Answers with citations",
          ].map((feature) => (
            <span key={feature}>
              <CheckCircle2 size={16} />
              {feature}
            </span>
          ))}
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-card-header">
            <p className="eyebrow">Knowledge workspace</p>
            <h2>
              {mode === "login"
                ? "Welcome back"
                : "Create your account"}
            </h2>
            <p>
              {mode === "login"
                ? "Sign in to continue where you left off."
                : "Start building a searchable knowledge base."}
            </p>
          </div>

          <div className="auth-tabs" role="tablist">
            <button
              type="button"
              className={
                mode === "login" ? "auth-tab active" : "auth-tab"
              }
              onClick={() => changeMode("login")}
            >
              Sign in
            </button>
            <button
              type="button"
              className={
                mode === "register"
                  ? "auth-tab active"
                  : "auth-tab"
              }
              onClick={() => changeMode("register")}
            >
              Register
            </button>
          </div>

          {notice && (
            <FeedbackBanner kind="success" message={notice} />
          )}

          <form className="auth-form" onSubmit={handleSubmit}>
            {mode === "register" && (
              <label>
                Full name
                <div className="input-wrapper">
                  <UserRound size={18} />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(event) =>
                      setFullName(event.target.value)
                    }
                    placeholder="Your full name"
                    autoComplete="name"
                    minLength={2}
                    required
                  />
                </div>
              </label>
            )}

            <label>
              Email
              <div className="input-wrapper">
                <Mail size={18} />
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="name@company.com"
                  autoComplete="email"
                  required
                />
              </div>
            </label>

            <label>
              Password
              <div className="input-wrapper">
                <LockKeyhole size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="At least 8 characters"
                  autoComplete={
                    mode === "login"
                      ? "current-password"
                      : "new-password"
                  }
                  minLength={8}
                  required
                />
              </div>
            </label>

            {error && (
              <FeedbackBanner kind="error" message={error} />
            )}

            <button
              className="primary-button full-width"
              type="submit"
              disabled={isLoading}
            >
              {isLoading
                ? "Please wait..."
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
