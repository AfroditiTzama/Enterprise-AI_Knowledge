import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  removeAccessToken,
  saveAccessToken,
} from "../api/auth";
import {
  SESSION_EXPIRED_EVENT,
} from "../api/auth-events";

interface AuthContextValue {
  isAuthenticated: boolean;
  signIn: (token: string) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(
  null,
);

function hasStoredToken(): boolean {
  return Boolean(localStorage.getItem("access_token"));
}

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [isAuthenticated, setIsAuthenticated] =
    useState(hasStoredToken);

  useEffect(() => {
    function handleStorage(event: StorageEvent) {
      if (event.key === "access_token") {
        setIsAuthenticated(hasStoredToken());
      }
    }

    function handleSessionExpired() {
      setIsAuthenticated(false);
    }

    window.addEventListener("storage", handleStorage);
    window.addEventListener(
      SESSION_EXPIRED_EVENT,
      handleSessionExpired,
    );

    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener(
        SESSION_EXPIRED_EVENT,
        handleSessionExpired,
      );
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated,
      signIn(token: string) {
        saveAccessToken(token);
        setIsAuthenticated(true);
      },
      signOut() {
        removeAccessToken();
        setIsAuthenticated(false);
      },
    }),
    [isAuthenticated],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === null) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}
