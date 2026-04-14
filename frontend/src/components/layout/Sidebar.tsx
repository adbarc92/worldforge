import { NavLink } from "react-router-dom";
import { HealthIndicator } from "./HealthIndicator";
import { ProjectSelector } from "./ProjectSelector";
import { useSyntheses } from "../../hooks/useSynthesis";

const links = [
  { to: "/", label: "Chat", icon: "\uD83D\uDCAC" },
  { to: "/documents", label: "Documents", icon: "\uD83D\uDCC4" },
  { to: "/contradictions", label: "Contradictions", icon: "\u26A0\uFE0F" },
  { to: "/synthesis", label: "Synthesis", icon: "\uD83D\uDCD6" },
  { to: "/projects", label: "Projects", icon: "\uD83D\uDCC1" },
  { to: "/settings", label: "Settings", icon: "\u2699\uFE0F" },
];

function SynthesisStatusIcon() {
  const { data: syntheses } = useSyntheses();
  const latest = syntheses?.[0];
  if (!latest) return null;

  if (latest.status === "outline_pending" || latest.status === "generating") {
    return (
      <span className="ml-auto inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
    );
  }

  if (latest.status === "failed") {
    return <span className="ml-auto text-xs text-destructive">✕</span>;
  }

  if (latest.status === "completed") {
    return <span className="ml-auto text-xs text-green-500">✓</span>;
  }

  return null;
}

export function Sidebar() {
  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-muted/40">
      <div className="p-4 font-semibold text-lg">Canon Builder</div>
      <ProjectSelector />
      <nav className="flex-1 space-y-1 px-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50"
              }`
            }
          >
            <span>{link.icon}</span>
            {link.label}
            {link.to === "/synthesis" && <SynthesisStatusIcon />}
          </NavLink>
        ))}
      </nav>
      <HealthIndicator />
    </aside>
  );
}
