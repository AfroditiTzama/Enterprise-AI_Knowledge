import {
  BookOpen,
  BrainCircuit,
  FileText,
  LogOut,
  MessageSquareText,
} from "lucide-react";
import {
  NavLink,
  Outlet,
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
    to: "/assistant",
    label: "Assistant",
    icon: MessageSquareText,
  },
];

export default function AppShell() {
  const navigate = useNavigate();

  function handleLogout() {
    removeAccessToken();

    navigate("/", {
      replace: true,
    });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <BrainCircuit size={28} />
          <span>Knowledge AI</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
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
