import { useProjects } from "@/hooks/useProjects";
import { useActiveProject } from "@/contexts/ProjectContext";
import { useNavigate } from "react-router-dom";

export function ProjectSelector() {
  const { data: projects, isLoading } = useProjects();
  const { activeProject, setActiveProject } = useActiveProject();
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="px-4 py-2 text-sm text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="px-3 pb-2">
      <select
        value={activeProject?.id || ""}
        onChange={(e) => {
          const project = projects?.find((p) => p.id === e.target.value);
          setActiveProject(project || null);
        }}
        className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
      >
        <option value="" disabled>
          Select a project...
        </option>
        {projects?.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <button
        onClick={() => navigate("/projects")}
        className="mt-1 w-full text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        Manage Projects
      </button>
    </div>
  );
}
