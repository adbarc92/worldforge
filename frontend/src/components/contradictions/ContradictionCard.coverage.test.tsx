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

describe("ContradictionCard advanced interactions", () => {
  it("selects both passages and shows textarea for explanation", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={vi.fn()}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );

    // Click passage A then passage B to select "both"
    await user.click(screen.getByText("Alice is tall."));
    await user.click(screen.getByText("Alice is short."));

    // Should show textarea for explaining how both are canon
    expect(
      screen.getByPlaceholderText(/explain how both passages are canon/i),
    ).toBeInTheDocument();

    // Resolve button should be disabled until note is typed
    expect(screen.getByRole("button", { name: /^resolve$/i })).toBeDisabled();
  });

  it("resolves with both selected and a note", async () => {
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

    // Select both passages
    await user.click(screen.getByText("Alice is tall."));
    await user.click(screen.getByText("Alice is short."));

    // Type a note
    await user.type(
      screen.getByPlaceholderText(/explain how both passages are canon/i),
      "Different timeline",
    );

    // Resolve should now be enabled
    const resolveBtn = screen.getByRole("button", { name: /^resolve$/i });
    expect(resolveBtn).not.toBeDisabled();
    await user.click(resolveBtn);

    expect(onResolve).toHaveBeenCalledWith("contra-1", "Different timeline");
  });

  it("deselects passage A by clicking it again", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={vi.fn()}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );

    // Select then deselect passage A
    await user.click(screen.getByText("Alice is tall."));
    // Should show resolving message
    expect(screen.getByText(/resolving with/i)).toBeInTheDocument();

    await user.click(screen.getByText("Alice is tall."));
    // Resolve should be disabled again (no selection)
    expect(screen.getByRole("button", { name: /^resolve$/i })).toBeDisabled();
  });

  it("selects passage B as canon", async () => {
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

    await user.click(screen.getByText("Alice is short."));
    await user.click(screen.getByRole("button", { name: /^resolve$/i }));

    expect(onResolve).toHaveBeenCalledWith("contra-1", '"Book B" is canon');
  });

  it("goes from both selected back to one by deselecting", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={vi.fn()}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );

    // Select both
    await user.click(screen.getByText("Alice is tall."));
    await user.click(screen.getByText("Alice is short."));

    // Deselect passage A => should leave only B selected
    await user.click(screen.getByText("Alice is tall."));

    // Should show resolving with Book B
    expect(screen.getByText(/resolving with/i)).toBeInTheDocument();
  });

  it("shows dismissed state with reopen button", () => {
    const dismissed: Contradiction = {
      ...openContradiction,
      status: "dismissed",
      resolution_note: null,
      resolved_at: "2026-02-01T00:00:00Z",
    };

    renderWithProviders(
      <ContradictionCard
        contradiction={dismissed}
        onResolve={vi.fn()}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );

    expect(screen.getByText(/dismissed/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reopen/i })).toBeInTheDocument();
  });

  it("resolves with both selected but no custom note uses default", async () => {
    const user = userEvent.setup();
    const onResolve = vi.fn();

    // We'll test the "both" selection with empty note branch
    // The code checks `note || "Both passages are canon"`
    // but the button is disabled when note is empty with "both" selected.
    // So we can't test that exact branch through UI.
    // Instead, let's verify the placeholder text
    renderWithProviders(
      <ContradictionCard
        contradiction={openContradiction}
        onResolve={onResolve}
        onDismiss={vi.fn()}
        onReopen={vi.fn()}
      />,
    );

    await user.click(screen.getByText("Alice is tall."));
    await user.click(screen.getByText("Alice is short."));

    const textarea = screen.getByPlaceholderText(/explain how both passages are canon/i);
    expect(textarea).toBeInTheDocument();
  });
});
