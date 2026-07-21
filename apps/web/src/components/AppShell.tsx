import {
  BookOpen,
  BrainCircuit,
  FileText,
  LogOut,
  Menu,
  MessageSquareText,
  Network,
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
  useNavigate,
} from "react-router-dom";

import {
  removeAccessToken,
} from "../api/auth";

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
];

export default function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();

  const [
    isSidebarOpen,
    setIsSidebarOpen,
  ] = useState(false);

  const activeLabel = useMemo(() => {
    const sortedItems = [...navItems].sort(
      (first, second) =>
        second.to.length - first.to.length,
    );

    return (
      sortedItems.find(
        (item) =>
          location.pathname === item.to ||
          location.pathname.startsWith(
            `${item.to}/`,
          ),
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

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow = "hidden";

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        setIsSidebarOpen(false);
      }
    }

    window.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.body.style.overflow =
        previousOverflow;

      window.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [isSidebarOpen]);

  function handleLogout() {
    removeAccessToken();
    setIsSidebarOpen(false);

    navigate("/", {
      replace: true,
    });
  }

  return (
    <div className="app-shell">
      <header className="mobile-topbar">
        <button
          type="button"
          className="mobile-nav-button"
          onClick={() =>
            setIsSidebarOpen(true)
          }
          aria-label="Open navigation menu"
          aria-expanded={isSidebarOpen}
          aria-controls="application-sidebar"
        >
          <Menu size={22} />
        </button>

        <div className="mobile-topbar-brand">
          <BrainCircuit size={22} />
          <span>{activeLabel}</span>
        </div>
      </header>

      <button
        type="button"
        className={
          isSidebarOpen
            ? "sidebar-overlay open"
            : "sidebar-overlay"
        }
        onClick={() =>
          setIsSidebarOpen(false)
        }
        tabIndex={isSidebarOpen ? 0 : -1}
        aria-label="Close navigation menu"
        aria-hidden={!isSidebarOpen}
      />

      <aside
        id="application-sidebar"
        className={
          isSidebarOpen
            ? "sidebar open"
            : "sidebar"
        }
      >
        <div className="sidebar-header-row">
          <div className="sidebar-brand">
            <BrainCircuit size={28} />
            <span>Knowledge AI</span>
          </div>

          <button
            type="button"
            className="mobile-sidebar-close"
            onClick={() =>
              setIsSidebarOpen(false)
            }
            aria-label="Close navigation menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/wiki"}
                onClick={() =>
                  setIsSidebarOpen(false)
                }
                className={({ isActive }) =>
                  isActive
                    ? "nav-item active"
                    : "nav-item"
                }
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <button
          type="button"
          className="logout-button"
          onClick={handleLogout}
        >
          <LogOut size={18} />
          <span>Sign out</span>
        </button>
      </aside>

      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
