import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Project } from "@/lib/api";
import { useProjects } from "@/hooks/useProjects";

interface ProjectContextType {
  activeProject: Project | null;
  setActiveProject: (project: Project | null) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

const STORAGE_KEY = "canon-builder-active-project";

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [activeProject, setActiveProjectState] = useState<Project | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return null;
      }
    }
    return null;
  });

  const { data: projects } = useProjects();

  // Reconcile localStorage hydration against the server's project list.
  // If the stored project no longer exists (e.g. deleted in another session),
  // clear it so chat/documents/etc. don't fire API calls against a 404.
  useEffect(() => {
    if (!projects || !activeProject) return;
    if (!projects.some((p) => p.id === activeProject.id)) {
      setActiveProjectState(null);
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [projects, activeProject]);

  const setActiveProject = (project: Project | null) => {
    setActiveProjectState(project);
    if (project) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(project));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  return (
    <ProjectContext.Provider value={{ activeProject, setActiveProject }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useActiveProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useActiveProject must be used within a ProjectProvider");
  }
  return context;
}
