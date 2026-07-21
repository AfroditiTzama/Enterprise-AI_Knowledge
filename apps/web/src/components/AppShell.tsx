import {
  BookOpen,
  BrainCircuit,
  FileText,
  LogOut,
  Menu,
  MessageSquareText,
  Moon,
  Network,
  Sun,
  UserRound,
  X,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  NavLink,
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  useAuth,
} from "../context/AuthContext";
import {
  useTheme,
} from "../context/ThemeContext";

const navItems = [
  {
    to: "/dashboard",
    label: "Documents",
    icon: FileText,
  },
  {
    to: "/wiki",
    label: "Wiki",
    icon: BookOpen,
  },
  {
    to: "/wiki/graph",
    label: "Knowledge Graph",
    icon: Network,
  },
  {
    to: "/assistant",
    label: "Assistant",
    icon: MessageSquareText,
  },
  {
    to: "/profile",
    label: "My Profile",
    icon: UserRound,
  },
];

export default function AppShell() {
  const location = useLocation();
  const { signOut } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();
  const [isSidebarOpen, setIsSidebarOpen] =
    useState(false);

  const activeLabel = useMemo(() => {
    const sortedItems = [...navItems].sort(
      (first, second) =>
        second.to.length - first.to.length,
    );

    return (
      sortedItems.find(
        (item) =>
          location.pathname === item.to ||
          location.pathname.startsWith(`${item.to}/`),
      )?.label ?? "Knowledge AI"
    );
  }, [location.pathname]);

  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!isSidebarOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsSidebarOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isSidebarOpen]);

  function handleLogout() {
    setIsSidebarOpen(false);
    signOut();
  }

  const ThemeIcon =
    resolvedTheme === "dark" ? Sun : Moon;

  return (
    <div className="app-shell">
      <header className="mobile-topbar">
        <button
          type="button"
          className="mobile-nav-button"
          onClick={() => setIsSidebarOpen(true)}
          aria-label="Open navigation menu"
          aria-expanded={isSidebarOpen}
          aria-controls="application-sidebar"
        >
          <Menu size={22} />
        </button>

        <div className="mobile-topbar-brand">
          <BrainCircuit size={21} />
          <span>{activeLabel}</span>
        </div>

        <button
          type="button"
          className="mobile-nav-button"
          onClick={toggleTheme}
          aria-label={`Switch to ${
            resolvedTheme === "dark" ? "light" : "dark"
          } mode`}
        >
          <ThemeIcon size={20} />
        </button>
      </header>

      <button
        type="button"
        className={
          isSidebarOpen
            ? "sidebar-overlay open"
            : "sidebar-overlay"
        }
        onClick={() => setIsSidebarOpen(false)}
        tabIndex={isSidebarOpen ? 0 : -1}
        aria-label="Close navigation menu"
        aria-hidden={!isSidebarOpen}
      />

      <aside
        id="application-sidebar"
        className={isSidebarOpen ? "sidebar open" : "sidebar"}
      >
        <div className="sidebar-header-row">
          <div className="sidebar-brand">
            <span className="sidebar-logo">
              <BrainCircuit size={24} />
            </span>
            <div>
              <strong>Knowledge AI</strong>
              <span>Enterprise workspace</span>
            </div>
          </div>

          <button
            type="button"
            className="mobile-sidebar-close"
            onClick={() => setIsSidebarOpen(false)}
            aria-label="Close navigation menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/wiki"}
                onClick={() => setIsSidebarOpen(false)}
                className={({ isActive }) =>
                  isActive ? "nav-item active" : "nav-item"
                }
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="sidebar-action"
            onClick={toggleTheme}
          >
            <ThemeIcon size={18} />
            <span>
              {resolvedTheme === "dark"
                ? "Light appearance"
                : "Dark appearance"}
            </span>
          </button>

          <button
            type="button"
            className="sidebar-action danger-text"
            onClick={handleLogout}
          >
            <LogOut size={18} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
