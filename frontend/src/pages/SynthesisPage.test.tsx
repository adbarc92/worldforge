import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, seedActiveProject } from "@/test/test-utils";
import { SynthesisPage } from "./SynthesisPage";

describe("SynthesisPage", () => {
  it("prompts to select a project when none is active", () => {
    renderWithProviders(<SynthesisPage />);
    expect(
      screen.getByText(/select a project to generate a world primer/i),
    ).toBeInTheDocument();
  });

  describe("with active project", () => {
    beforeEach(() => {
      seedActiveProject({ id: "proj-1", name: "Test Project" });
    });

    it("loads syntheses and shows outline editor for outline_ready status", async () => {
      // No open contradictions so the generate gate is unblocked
      server.use(
        http.get("/api/v1/projects/:pid/contradictions", () =>
          HttpResponse.json({ items: [], total: 0 }),
        ),
      );
      renderWithProviders(<SynthesisPage />);
      await waitFor(() => {
        expect(screen.getByText(/edit outline/i)).toBeInTheDocument();
      });
      expect(screen.getByDisplayValue("Introduction")).toBeInTheDocument();
    });

    it("blocks generation when there are open contradictions and no synthesis exists", async () => {
      // Block contradictions gate and return empty synthesis list
      server.use(
        http.get("/api/v1/projects/:pid/synthesis", () => HttpResponse.json([])),
        http.get("/api/v1/projects/:pid/contradictions", () =>
          HttpResponse.json({
            items: [
              {
                id: "c1",
                chunk_a_text: "a",
                chunk_b_text: "b",
                document_a_id: "da",
                document_b_id: "db",
                document_a_title: "A",
                document_b_title: "B",
                explanation: "x",
                status: "open",
                resolution_note: null,
                created_at: "2026-01-01T00:00:00Z",
                resolved_at: null,
              },
            ],
            total: 1,
          }),
        ),
      );
      renderWithProviders(<SynthesisPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/there is 1 open/i),
        ).toBeInTheDocument();
      });
      // The "contradiction" word is now a link to /contradictions
      const link = screen.getByRole("link", { name: /contradiction/i });
      expect(link).toHaveAttribute("href", "/contradictions");
      expect(screen.getByRole("button", { name: /generate world primer/i })).toBeDisabled();
    });
  });
});
