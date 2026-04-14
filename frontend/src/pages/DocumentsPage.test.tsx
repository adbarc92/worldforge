import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, seedActiveProject } from "@/test/test-utils";
import { DocumentsPage } from "./DocumentsPage";

describe("DocumentsPage", () => {
  it("prompts to select a project when none is active", () => {
    renderWithProviders(<DocumentsPage />);
    expect(
      screen.getByText(/select a project to view and manage documents/i),
    ).toBeInTheDocument();
  });

  describe("with active project", () => {
    beforeEach(() => {
      seedActiveProject({ id: "proj-1", name: "Test Project" });
    });

    it("loads and displays documents", async () => {
      renderWithProviders(<DocumentsPage />);
      await waitFor(() => {
        expect(screen.getByText("Test Document")).toBeInTheDocument();
      });
      expect(screen.getByText(/drop files here or click to upload/i)).toBeInTheDocument();
    });

    it("shows empty state when no documents", async () => {
      server.use(
        http.get("/api/v1/projects/:pid/documents", () => HttpResponse.json([])),
      );
      renderWithProviders(<DocumentsPage />);
      await waitFor(() => {
        expect(screen.getByText(/no documents uploaded yet/i)).toBeInTheDocument();
      });
    });
  });
});
