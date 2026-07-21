import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ThemePreference =
  | "system"
  | "light"
  | "dark";

type ResolvedTheme = "light" | "dark";

interface ThemeContextValue {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference: (value: ThemePreference) => void;
  toggleTheme: () => void;
}

const STORAGE_KEY = "knowledge-ai-theme";
const ThemeContext = createContext<ThemeContextValue | null>(
  null,
);

function getStoredPreference(): ThemePreference {
  const stored = localStorage.getItem(STORAGE_KEY);

  if (
    stored === "light" ||
    stored === "dark" ||
    stored === "system"
  ) {
    return stored;
  }

  return "system";
}

function getSystemTheme(): ResolvedTheme {
  return window.matchMedia("(prefers-color-scheme: dark)")
    .matches
    ? "dark"
    : "light";
}

export function ThemeProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [preference, setPreferenceState] =
    useState<ThemePreference>(getStoredPreference);
  const [systemTheme, setSystemTheme] =
    useState<ResolvedTheme>(getSystemTheme);

  const resolvedTheme =
    preference === "system" ? systemTheme : preference;

  useEffect(() => {
    const mediaQuery = window.matchMedia(
      "(prefers-color-scheme: dark)",
    );

    function handleChange(event: MediaQueryListEvent) {
      setSystemTheme(event.matches ? "dark" : "light");
    }

    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme =
      resolvedTheme;
  }, [resolvedTheme]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      preference,
      resolvedTheme,
      setPreference(value: ThemePreference) {
        localStorage.setItem(STORAGE_KEY, value);
        setPreferenceState(value);
      },
      toggleTheme() {
        const next =
          resolvedTheme === "dark" ? "light" : "dark";

        localStorage.setItem(STORAGE_KEY, next);
        setPreferenceState(next);
      },
    }),
    [preference, resolvedTheme],
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);

  if (context === null) {
    throw new Error(
      "useTheme must be used inside ThemeProvider.",
    );
  }

  return context;
}
