import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  logout,
  refreshSession,
  type AuthSessionResponse,
  type CurrentUser,
} from "../api/auth";
import {
  SESSION_EXPIRED_EVENT,
} from "../api/auth-events";
import {
  clearCsrfToken,
  CSRF_STORAGE_KEY,
  getCsrfToken,
} from "../api/client";

interface AuthContextValue {
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  user: CurrentUser | null;
  signIn: (session: AuthSessionResponse) => void;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<CurrentUser | null>;
  setUser: (user: CurrentUser | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(
  null,
);

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      if (!getCsrfToken()) {
        const session = await refreshSession();
        setUser(session.user);
        return session.user;
      }

      const currentUser = await getCurrentUser();
      setUser(currentUser);
      return currentUser;
    } catch {
      clearCsrfToken();
      setUser(null);
      return null;
    } finally {
      setIsAuthLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  useEffect(() => {
    function handleSessionExpired() {
      clearCsrfToken();
      setUser(null);
      setIsAuthLoading(false);
    }

    function handleAuthStorageChange(event: StorageEvent) {
      if (event.key === CSRF_STORAGE_KEY && event.newValue === null) {
        setUser(null);
        setIsAuthLoading(false);
      }
    }

    window.addEventListener(
      SESSION_EXPIRED_EVENT,
      handleSessionExpired,
    );
    window.addEventListener("storage", handleAuthStorageChange);

    return () => {
      window.removeEventListener(
        SESSION_EXPIRED_EVENT,
        handleSessionExpired,
      );
      window.removeEventListener("storage", handleAuthStorageChange);
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: user !== null,
      isAuthLoading,
      user,
      signIn(session: AuthSessionResponse) {
        setUser(session.user);
        setIsAuthLoading(false);
      },
      async signOut() {
        try {
          await logout();
        } finally {
          setUser(null);
          setIsAuthLoading(false);
        }
      },
      refreshUser,
      setUser,
    }),
    [isAuthLoading, refreshUser, user],
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
