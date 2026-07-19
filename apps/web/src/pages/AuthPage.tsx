import {
  BrainCircuit,
  LockKeyhole,
  Mail,
} from "lucide-react";
import {
  useState,
  type FormEvent,
} from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  login,
  register,
  saveAccessToken,
} from "../api/auth";
import {
  getApiErrorMessage,
} from "../api/errors";

type AuthMode = "login" | "register";

export default function AuthPage() {
  const navigate = useNavigate();

  const [mode, setMode] =
    useState<AuthMode>("login");
  const [email, setEmail] =
    useState("");
  const [password, setPassword] =
    useState("");
  const [error, setError] =
    useState("");
  const [isLoading, setIsLoading] =
    useState(false);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setIsLoading(true);

    try {
      if (mode === "register") {
        await register({
          email,
          password,
        });
      }

      const result = await login({
        email,
        password,
      });

      saveAccessToken(result.access_token);

      navigate("/dashboard", {
        replace: true,
      });
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsLoading(false);
    }
  }

  function changeMode(
    newMode: AuthMode,
  ) {
    setMode(newMode);
    setError("");
  }

  return (
    <main className="auth-layout">
      <section className="auth-brand-panel">
        <div className="brand-mark">
          <BrainCircuit size={30} />
        </div>

        <p className="eyebrow">
          Enterprise AI
        </p>

        <h1>
          Turn documents into connected
          organizational knowledge.
        </h1>

        <p className="brand-description">
          Upload documents, generate an
          intelligent internal Wiki and ask
          grounded questions with traceable
          sources.
        </p>

        <div className="feature-list">
          <span>LLM Wiki generation</span>
          <span>Hybrid knowledge retrieval</span>
          <span>Grounded answers with citations</span>
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-card-header">
            <h2>
              {mode === "login"
                ? "Welcome back"
                : "Create your account"}
            </h2>

            <p>
              {mode === "login"
                ? "Sign in to access your knowledge workspace."
                : "Create an account to start building your knowledge base."}
            </p>
          </div>

          <div className="auth-tabs">
            <button
              type="button"
              className={
                mode === "login"
                  ? "auth-tab active"
                  : "auth-tab"
              }
              onClick={() =>
                changeMode("login")
              }
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
              onClick={() =>
                changeMode("register")
              }
            >
              Register
            </button>
          </div>

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >
            <label>
              Email
              <div className="input-wrapper">
                <Mail size={18} />

                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(
                      event.target.value,
                    )
                  }
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
                    setPassword(
                      event.target.value,
                    )
                  }
                  placeholder="Enter your password"
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
              <div className="error-message">
                {error}
              </div>
            )}

            <button
              className="primary-button"
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
