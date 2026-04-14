import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, seedActiveProject, userEvent } from "@/test/test-utils";
import { SynthesisPage } from "./SynthesisPage";

describe("SynthesisPage interactions", () => {
  beforeEach(() => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
  });

  it("shows generate buttons when no synthesis exists and no contradictions", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () => HttpResponse.json([])),
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({ items: [], total: 0 }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<SynthesisPage />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /generate world primer/i }),
      ).not.toBeDisabled();
    });

    // Also verify Quick Generate button is present
    expect(
      screen.getByRole("button", { name: /quick generate/i }),
    ).toBeInTheDocument();

    // Click Generate World Primer
    await user.click(
      screen.getByRole("button", { name: /generate world primer/i }),
    );

    // After clicking, synthesis should be created and auto-selected
    await waitFor(() => {
      expect(screen.getByText(/edit outline/i)).toBeInTheDocument();
    });
  });

  it("shows completed synthesis with viewer", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-2",
            project_id: "proj-1",
            title: "Completed World",
            outline: [{ title: "Introduction", description: "Overview" }],
            outline_approved: true,
            content: "# World Primer\n\nThis is the world primer content.",
            status: "completed",
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
      http.get("/api/v1/projects/:pid/synthesis/:id", () =>
        HttpResponse.json({
          id: "synth-2",
          project_id: "proj-1",
          title: "Completed World",
          outline: [{ title: "Introduction", description: "Overview" }],
          outline_approved: true,
          content: "# World Primer\n\nThis is the world primer content.",
          status: "completed",
          error_message: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }),
      ),
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({ items: [], total: 0 }),
      ),
    );

    renderWithProviders(<SynthesisPage />);

    await waitFor(() => {
      expect(screen.getByText(/world primer content/i)).toBeInTheDocument();
    });
  });

  it("shows failed synthesis with retry options", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-3",
            project_id: "proj-1",
            title: "Failed Synthesis",
            outline: [{ title: "Introduction", description: "Overview" }],
            outline_approved: true,
            content: null,
            status: "failed",
            error_message: "API timeout",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
      http.get("/api/v1/projects/:pid/synthesis/:id", () =>
        HttpResponse.json({
          id: "synth-3",
          project_id: "proj-1",
          title: "Failed Synthesis",
          outline: [{ title: "Introduction", description: "Overview" }],
          outline_approved: true,
          content: null,
          status: "failed",
          error_message: "API timeout",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }),
      ),
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({ items: [], total: 0 }),
      ),
    );

    renderWithProviders(<SynthesisPage />);

    await waitFor(() => {
      expect(screen.getByText(/synthesis failed: api timeout/i)).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /retry with same outline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /start fresh/i }),
    ).toBeInTheDocument();
  });

  it("shows generating state with spinner and reset button", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-4",
            project_id: "proj-1",
            title: "In Progress",
            outline: [{ title: "Introduction", description: "Overview" }],
            outline_approved: true,
            content: null,
            status: "generating",
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
      http.get("/api/v1/projects/:pid/synthesis/:id", () =>
        HttpResponse.json({
          id: "synth-4",
          project_id: "proj-1",
          title: "In Progress",
          outline: [{ title: "Introduction", description: "Overview" }],
          outline_approved: true,
          content: null,
          status: "generating",
          error_message: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }),
      ),
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({ items: [], total: 0 }),
      ),
    );

    renderWithProviders(<SynthesisPage />);

    await waitFor(() => {
      expect(screen.getByText(/generating sections/i)).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /stuck\? reset to outline/i }),
    ).toBeInTheDocument();
  });

  it("shows outline_pending state", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-5",
            project_id: "proj-1",
            title: "Pending",
            outline: [],
            outline_approved: false,
            content: null,
            status: "outline_pending",
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
      http.get("/api/v1/projects/:pid/synthesis/:id", () =>
        HttpResponse.json({
          id: "synth-5",
          project_id: "proj-1",
          title: "Pending",
          outline: [],
          outline_approved: false,
          content: null,
          status: "outline_pending",
          error_message: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }),
      ),
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({ items: [], total: 0 }),
      ),
    );

    renderWithProviders(<SynthesisPage />);

    await waitFor(() => {
      expect(screen.getByText(/generating outline/i)).toBeInTheDocument();
    });
  });

  it("shows previous syntheses list and allows switching", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json([
          {
            id: "synth-1",
            project_id: "proj-1",
            title: "Latest Synthesis",
            outline: [{ title: "Introduction", description: "Overview" }],
            outline_approved: false,
            content: null,
            status: "outline_ready",
            error_message: null,
            created_at: "2026-01-02T00:00:00Z",
            updated_at: "2026-01-02T00:00:00Z",
          },
          {
            id: "synth-old",
            project_id: "proj-1",
            title: "Older Synthesis",
            outline: [],
            outline_approved: true,
            content: "Old content",
            status: "completed",
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({ items: [], total: 0 }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<SynthesisPage />);

    await waitFor(() => {
      expect(screen.getByText(/previous syntheses/i)).toBeInTheDocument();
    });

    expect(screen.getByText("Older Synthesis")).toBeInTheDocument();

    // Click to switch to older synthesis
    await user.click(screen.getByText("Older Synthesis"));
  });
});
