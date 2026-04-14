import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, seedActiveProject } from "@/test/test-utils";
import { Sidebar } from "./Sidebar";

describe("Sidebar synthesis status", () => {
  beforeEach(() => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
  });

  it("shows spinner when synthesis is generating", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-1",
            project_id: "proj-1",
            title: "Generating",
            status: "generating",
            outline: [],
            outline_approved: true,
            content: null,
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
    );

    renderWithProviders(<Sidebar />);

    // Wait for the synthesis data to load
    await waitFor(() => {
      // The spinner should be visible (an animate-spin element)
      const synthesisLink = screen.getByRole("link", { name: /synthesis/i });
      const spinner = synthesisLink.querySelector(".animate-spin");
      expect(spinner).toBeInTheDocument();
    });
  });

  it("shows check mark when synthesis is completed", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-1",
            project_id: "proj-1",
            title: "Complete",
            status: "completed",
            outline: [],
            outline_approved: true,
            content: "Done",
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
    );

    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      expect(screen.getByText("✓")).toBeInTheDocument();
    });
  });

  it("shows error mark when synthesis has failed", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-1",
            project_id: "proj-1",
            title: "Failed",
            status: "failed",
            outline: [],
            outline_approved: true,
            content: null,
            error_message: "Error",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
    );

    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      expect(screen.getByText("✕")).toBeInTheDocument();
    });
  });

  it("shows no status icon when synthesis is outline_ready", async () => {
    // The default handler returns outline_ready status, so no icon should be shown
    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      expect(screen.getByText("Canon Builder")).toBeInTheDocument();
    });

    // outline_ready falls through to "return null", so no spinner, check, or error
    const synthesisLink = screen.getByRole("link", { name: /synthesis/i });
    expect(synthesisLink.querySelector(".animate-spin")).not.toBeInTheDocument();
    expect(screen.queryByText("✓")).not.toBeInTheDocument();
    expect(screen.queryByText("✕")).not.toBeInTheDocument();
  });
});
