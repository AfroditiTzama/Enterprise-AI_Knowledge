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
import ProfilePage from "./pages/ProfilePage";
import WikiGraphPage from "./pages/WikiGraphPage";
import WikiPage from "./pages/WikiPage";

function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <AuthPage />
          )
        }
      />

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
