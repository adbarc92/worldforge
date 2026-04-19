import { beforeEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { waitFor } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { server } from "@/test/mocks/server";
import { useActiveProject } from "./ProjectContext";

function ActiveProjectProbe() {
  const { activeProject } = useActiveProject();
  return (
    <div>
      <span data-testid="active-id">{activeProject?.id ?? "none"}</span>
      <span data-testid="active-name">{activeProject?.name ?? "none"}</span>
    </div>
  );
}

const STORAGE_KEY = "canon-builder-active-project";

describe("ProjectContext reconciliation", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("clears activeProject when the stored project no longer exists on the server", async () => {
    // Seed localStorage with a project the server will not return
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        id: "deleted-project",
        name: "Ghost Project",
        description: null,
        document_count: 0,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      }),
    );

    // Server only returns "proj-1" (the default mock), not the stored one
    const { getByTestId } = renderWithProviders(<ActiveProjectProbe />);

    // Initially hydrated from localStorage
    expect(getByTestId("active-id").textContent).toBe("deleted-project");

    // After projects load, reconciliation should clear it
    await waitFor(() => {
      expect(getByTestId("active-id").textContent).toBe("none");
    });
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it("keeps activeProject when the stored project still exists on the server", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        id: "proj-1",
        name: "Seeded",
        description: null,
        document_count: 0,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      }),
    );

    const { getByTestId } = renderWithProviders(<ActiveProjectProbe />);

    // Give projects query a chance to resolve
    await waitFor(() => {
      expect(getByTestId("active-id").textContent).toBe("proj-1");
    });
    expect(localStorage.getItem(STORAGE_KEY)).not.toBeNull();
  });

  it("does not touch localStorage if no active project is set", async () => {
    server.use(
      http.get("/api/v1/projects", () => HttpResponse.json([])),
    );
    const { getByTestId } = renderWithProviders(<ActiveProjectProbe />);
    await waitFor(() => {
      expect(getByTestId("active-id").textContent).toBe("none");
    });
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});
