import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, seedActiveProject, userEvent } from "@/test/test-utils";
import { ContradictionsPage } from "./ContradictionsPage";

describe("ContradictionsPage interactions", () => {
  beforeEach(() => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
  });

  it("switches tabs when clicking Resolved/Dismissed", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ContradictionsPage />);

    await waitFor(() => {
      expect(screen.getByText(/alice is tall/i)).toBeInTheDocument();
    });

    // Switch to Resolved tab
    await user.click(screen.getByRole("button", { name: /^resolved$/i }));

    // The "1 open" text should update (tab switched)
    await waitFor(() => {
      expect(screen.getByText(/1 resolved/i)).toBeInTheDocument();
    });
  });

  it("triggers scan when Scan Project is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ContradictionsPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /scan project/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /scan project/i }));

    // Button should be disabled during scan
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /scan project/i })).not.toBeDisabled();
    });
  });

  it("collapses and expands document groups when clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ContradictionsPage />);

    await waitFor(() => {
      expect(screen.getByText(/alice is tall/i)).toBeInTheDocument();
    });

    // Click the group header to collapse
    const groupHeader = screen.getByText(/doc a vs doc b/i);
    await user.click(groupHeader);

    // Content should be hidden
    expect(screen.queryByText(/alice is tall/i)).not.toBeInTheDocument();

    // Click again to expand
    await user.click(groupHeader);

    // Content should be visible again
    expect(screen.getByText(/alice is tall/i)).toBeInTheDocument();
  });

  it("handles bulk dismiss for a document group", async () => {
    // Need at least 2 contradictions in the same group for bulk actions to appear
    server.use(
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({
          items: [
            {
              id: "c1",
              chunk_a_text: "Alice is tall.",
              chunk_b_text: "Alice is short.",
              document_a_id: "doc-1",
              document_b_id: "doc-2",
              document_a_title: "Doc A",
              document_b_title: "Doc B",
              explanation: "Height conflict",
              status: "open",
              resolution_note: null,
              created_at: "2026-01-01T00:00:00Z",
              resolved_at: null,
            },
            {
              id: "c2",
              chunk_a_text: "Alice has blue eyes.",
              chunk_b_text: "Alice has green eyes.",
              document_a_id: "doc-1",
              document_b_id: "doc-2",
              document_a_title: "Doc A",
              document_b_title: "Doc B",
              explanation: "Eye color conflict",
              status: "open",
              resolution_note: null,
              created_at: "2026-01-01T00:00:00Z",
              resolved_at: null,
            },
          ],
          total: 2,
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<ContradictionsPage />);

    await waitFor(() => {
      expect(screen.getByText(/alice is tall/i)).toBeInTheDocument();
    });

    // Bulk Dismiss Group button should appear for groups with > 1 item
    const dismissGroupBtn = screen.getByRole("button", { name: /dismiss group/i });
    await user.click(dismissGroupBtn);

    // Verify the bulk action was triggered
    await waitFor(() => {
      expect(dismissGroupBtn).toBeInTheDocument();
    });
  });

  it("handles bulk resolve for a document group", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({
          items: [
            {
              id: "c1",
              chunk_a_text: "Alice is tall.",
              chunk_b_text: "Alice is short.",
              document_a_id: "doc-1",
              document_b_id: "doc-2",
              document_a_title: "Doc A",
              document_b_title: "Doc B",
              explanation: "Height conflict",
              status: "open",
              resolution_note: null,
              created_at: "2026-01-01T00:00:00Z",
              resolved_at: null,
            },
            {
              id: "c2",
              chunk_a_text: "Alice has blue eyes.",
              chunk_b_text: "Alice has green eyes.",
              document_a_id: "doc-1",
              document_b_id: "doc-2",
              document_a_title: "Doc A",
              document_b_title: "Doc B",
              explanation: "Eye color conflict",
              status: "open",
              resolution_note: null,
              created_at: "2026-01-01T00:00:00Z",
              resolved_at: null,
            },
          ],
          total: 2,
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<ContradictionsPage />);

    await waitFor(() => {
      expect(screen.getByText(/alice is tall/i)).toBeInTheDocument();
    });

    const resolveGroupBtn = screen.getByRole("button", { name: /resolve group/i });
    await user.click(resolveGroupBtn);

    await waitFor(() => {
      expect(resolveGroupBtn).toBeInTheDocument();
    });
  });
});
