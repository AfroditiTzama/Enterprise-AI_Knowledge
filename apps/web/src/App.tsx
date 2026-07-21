import type {
  ReactNode,
} from "react";
import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import {
  isAuthenticated,
} from "./api/auth";
import AppShell from "./components/AppShell";
import AssistantPage from "./pages/AssistantPage";
import AuthPage from "./pages/AuthPage";
import DocumentsPage from "./pages/DocumentsPage";
import WikiGraphPage from "./pages/WikiGraphPage";
import WikiPage from "./pages/WikiPage";

function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {
  if (!isAuthenticated()) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  return children;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          isAuthenticated()
            ? (
              <Navigate
                to="/dashboard"
                replace
              />
            )
            : <AuthPage />
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route
          path="/dashboard"
          element={<DocumentsPage />}
        />

        <Route
          path="/wiki"
          element={<WikiPage />}
        />

        <Route
          path="/wiki/graph"
          element={<WikiGraphPage />}
        />

        <Route
          path="/assistant"
          element={<AssistantPage />}
        />
      </Route>

      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />
    </Routes>
  );
}
