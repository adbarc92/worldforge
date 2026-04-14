import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { OutlineEditor } from "./OutlineEditor";
import type { SynthesisOutlineSection } from "@/lib/api";

const outline: SynthesisOutlineSection[] = [
  { title: "Introduction", description: "The setting" },
  { title: "Characters", description: "Main cast" },
];

describe("OutlineEditor", () => {
  it("renders outline sections with editable inputs", () => {
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={vi.fn()} onApprove={vi.fn()} />,
    );
    expect(screen.getByDisplayValue("Introduction")).toBeInTheDocument();
    expect(screen.getByDisplayValue("The setting")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Characters")).toBeInTheDocument();
  });

  it("renders read-only view without inputs", () => {
    renderWithProviders(
      <OutlineEditor outline={outline} readOnly onSave={vi.fn()} onApprove={vi.fn()} />,
    );
    expect(screen.getByText("Introduction")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("Introduction")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /save changes/i })).not.toBeInTheDocument();
  });

  it("calls onSave with current sections when Save Changes is clicked", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={onSave} onApprove={vi.fn()} />,
    );
    await user.click(screen.getByRole("button", { name: /save changes/i }));
    expect(onSave).toHaveBeenCalledWith(outline);
  });

  it("calls onApprove when Approve & Generate is clicked", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={vi.fn()} onApprove={onApprove} />,
    );
    await user.click(screen.getByRole("button", { name: /approve/i }));
    expect(onApprove).toHaveBeenCalled();
  });

  it("adds a new empty section when Add Section is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={vi.fn()} onApprove={vi.fn()} />,
    );
    const before = screen.getAllByPlaceholderText(/section title/i).length;
    await user.click(screen.getByRole("button", { name: /add section/i }));
    const after = screen.getAllByPlaceholderText(/section title/i).length;
    expect(after).toBe(before + 1);
  });
});
