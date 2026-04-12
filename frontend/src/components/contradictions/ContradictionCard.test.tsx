import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { ContradictionCard } from "./ContradictionCard";
import type { Contradiction } from "@/lib/api";

const openContradiction: Contradiction = {
  id: "contra-1",
  chunk_a_text: "Alice is tall.",
  chunk_b_text: "Alice is short.",
  document_a_id: "doc-a",
  document_b_id: "doc-b",
  document_a_title: "Book A",
  document_b_title: "Book B",
  explanation: "Height conflict",
  status: "open",
  resolution_note: null,
  created_at: "2026-01-01T00:00:00Z",
  resolved_at: null,
};

describe("ContradictionCard", () => {
  it("renders both passages, the explanation, and doc titles", () => {
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={vi.fn()}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );
    expect(screen.getByText("Alice is tall.")).toBeInTheDocument();
    expect(screen.getByText("Alice is short.")).toBeInTheDocument();
    expect(screen.getByText("Book A")).toBeInTheDocument();
    expect(screen.getByText("Book B")).toBeInTheDocument();
    expect(screen.getByText(/height conflict/i)).toBeInTheDocument();
  });

  it("disables Resolve until a passage is selected", () => {
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={vi.fn()}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /^resolve$/i })).toBeDisabled();
  });

  it("calls onResolve with canon note when a side is selected and Resolve clicked", async () => {
    const user = userEvent.setup();
    const onResolve = vi.fn();
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={onResolve}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );
    await user.click(screen.getByText("Alice is tall."));
    await user.click(screen.getByRole("button", { name: /^resolve$/i }));
    expect(onResolve).toHaveBeenCalledWith("contra-1", '"Book A" is canon');
  });

  it("calls onDismiss when Dismiss is clicked", async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={vi.fn()}
        onDismiss={onDismiss}
        onReopen={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: /^dismiss$/i }));
    expect(onDismiss).toHaveBeenCalledWith("contra-1");
  });

  it("renders resolved state with reopen button and resolution note", async () => {
    const user = userEvent.setup();
    const onReopen = vi.fn();
    const resolved: Contradiction = {
      ...openContradiction,
      status: "resolved",
      resolution_note: "Book A is canon",
      resolved_at: "2026-02-01T00:00:00Z",
    };
    renderWithProviders(
      <ContradictionCard
        contradiction={resolved}
        onResolve={vi.fn()}
        onDismiss={vi.fn()}
        onReopen={onReopen}
      />,
    );
    expect(screen.getByText(/resolved/i)).toBeInTheDocument();
    expect(screen.getByText(/book a is canon/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /reopen/i }));
    expect(onReopen).toHaveBeenCalledWith("contra-1");
  });
});
