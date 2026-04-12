import type { ReactElement, ReactNode } from "react";
import { render } from "@testing-library/react";
import type { RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { ProjectProvider } from "@/contexts/ProjectContext";
import type { Project } from "@/lib/api";

interface WrapperProps {
  children: ReactNode;
  initialRoute?: string;
}

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

function AllProviders({ children, initialRoute = "/" }: WrapperProps) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>
        <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
      </ProjectProvider>
    </QueryClientProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  initialRoute?: string;
}

export function renderWithProviders(
  ui: ReactElement,
  { initialRoute, ...options }: CustomRenderOptions = {},
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders initialRoute={initialRoute}>{children}</AllProviders>
    ),
    ...options,
  });
}

const ACTIVE_PROJECT_STORAGE_KEY = "canon-builder-active-project";

export function seedActiveProject(
  project: Partial<Project> & { id: string; name: string },
) {
  const full: Project = {
    id: project.id,
    name: project.name,
    description: project.description ?? null,
    document_count: project.document_count ?? 0,
    created_at: project.created_at ?? "2026-01-01T00:00:00Z",
    updated_at: project.updated_at ?? "2026-01-01T00:00:00Z",
  };
  localStorage.setItem(ACTIVE_PROJECT_STORAGE_KEY, JSON.stringify(full));
}

export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";
