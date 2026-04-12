import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { DocumentCard } from "./DocumentCard";
import type { Document } from "@/lib/api";

const doc: Document = {
  id: "doc-1",
  title: "The Great Chronicle",
  status: "processed",
  chunk_count: 42,
  file_path: "/data/chronicle.md",
  created_at: "2026-01-01T00:00:00Z",
};

beforeEach(() => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
});

describe("DocumentCard", () => {
  it("renders title, status badge, and chunk count", () => {
    renderWithProviders(<DocumentCard doc={doc} projectId="proj-1" />);
    expect(screen.getByText("The Great Chronicle")).toBeInTheDocument();
    expect(screen.getByText("processed")).toBeInTheDocument();
    expect(screen.getByText(/42 chunks/)).toBeInTheDocument();
  });

  it("renders an error message when document has error status", () => {
    const errored: Document = {
      ...doc,
      status: "error",
      error_message: "Failed to process",
    };
    renderWithProviders(<DocumentCard doc={errored} projectId="proj-1" />);
    expect(screen.getByText(/failed to process/i)).toBeInTheDocument();
  });

  it("invokes the delete mutation when user confirms deletion", async () => {
    const user = userEvent.setup();
    renderWithProviders(<DocumentCard doc={doc} projectId="proj-1" />);
    await user.click(screen.getByRole("button", { name: /delete/i }));
    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalled();
    });
  });
});
