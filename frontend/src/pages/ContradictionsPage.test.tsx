import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, seedActiveProject } from "@/test/test-utils";
import { ContradictionsPage } from "./ContradictionsPage";

describe("ContradictionsPage", () => {
  it("prompts to select a project when none is active", () => {
    renderWithProviders(<ContradictionsPage />);
    expect(
      screen.getByText(/select a project to view and scan for contradictions/i),
    ).toBeInTheDocument();
  });

  describe("with active project", () => {
    beforeEach(() => {
      seedActiveProject({ id: "proj-1", name: "Test Project" });
    });

    it("loads contradictions and groups them by document pair", async () => {
      renderWithProviders(<ContradictionsPage />);
      await waitFor(() => {
        expect(screen.getByText(/alice is tall/i)).toBeInTheDocument();
      });
      expect(screen.getByText(/alice is short/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /scan project/i })).toBeInTheDocument();
    });

    it("shows empty state when there are no open contradictions", async () => {
      server.use(
        http.get("/api/v1/projects/:pid/contradictions", () =>
          HttpResponse.json({ items: [], total: 0 }),
        ),
      );
      renderWithProviders(<ContradictionsPage />);
      await waitFor(() => {
        expect(screen.getByText(/no open contradictions/i)).toBeInTheDocument();
      });
    });
  });
});
