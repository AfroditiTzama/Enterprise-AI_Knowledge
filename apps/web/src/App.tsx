import type {
  ReactNode,
} from "react";
import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import AppShell from "./components/AppShell";
import {
  useAuth,
} from "./context/AuthContext";
import AssistantPage from "./pages/AssistantPage";
import AuthPage from "./pages/AuthPage";
import DocumentsPage from "./pages/DocumentsPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ProfilePage from "./pages/ProfilePage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import WikiGraphPage from "./pages/WikiGraphPage";
import WikiPage from "./pages/WikiPage";

function AuthLoadingScreen() {
  return (
    <main className="auth-loading-screen" aria-label="Checking session">
      <div className="app-loader" />
      <p>Securing your workspace...</p>
    </main>
  );
}

function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {
  const {
    isAuthenticated,
    isAuthLoading,
  } = useAuth();

  if (isAuthLoading) {
    return <AuthLoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default function App() {
  const {
    isAuthenticated,
    isAuthLoading,
  } = useAuth();

  return (
    <Routes>
      <Route
        path="/"
        element={
          isAuthLoading ? (
            <AuthLoadingScreen />
          ) : isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <AuthPage />
          )
        }
      />

      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DocumentsPage />} />
        <Route path="/wiki" element={<WikiPage />} />
        <Route path="/wiki/graph" element={<WikiGraphPage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
