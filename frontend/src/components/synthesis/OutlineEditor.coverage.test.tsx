import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { OutlineEditor } from "./OutlineEditor";
import type { SynthesisOutlineSection } from "@/lib/api";

const outline: SynthesisOutlineSection[] = [
  { title: "Introduction", description: "The setting" },
  { title: "Characters", description: "Main cast" },
  { title: "Timeline", description: "Key events" },
];

describe("OutlineEditor advanced interactions", () => {
  it("removes a section when the remove button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={vi.fn()} onApprove={vi.fn()} />,
    );

    const titleInputs = screen.getAllByPlaceholderText(/section title/i);
    expect(titleInputs).toHaveLength(3);

    // Click the first remove button (×)
    const removeButtons = screen.getAllByRole("button", { name: /×/i });
    await user.click(removeButtons[0]);

    // Should now have 2 sections
    expect(screen.getAllByPlaceholderText(/section title/i)).toHaveLength(2);
    // "Introduction" should be gone
    expect(screen.queryByDisplayValue("Introduction")).not.toBeInTheDocument();
  });

  it("moves a section down when the down arrow is clicked", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={onSave} onApprove={vi.fn()} />,
    );

    // Click the down arrow on the first section
    const downButtons = screen.getAllByRole("button", { name: /↓/i });
    await user.click(downButtons[0]);

    // Save to check the order
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(onSave).toHaveBeenCalledWith([
      { title: "Characters", description: "Main cast" },
      { title: "Introduction", description: "The setting" },
      { title: "Timeline", description: "Key events" },
    ]);
  });

  it("moves a section up when the up arrow is clicked", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={onSave} onApprove={vi.fn()} />,
    );

    // Click the up arrow on the second section (index 1)
    const upButtons = screen.getAllByRole("button", { name: /↑/i });
    await user.click(upButtons[1]);

    // Save to check the order
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(onSave).toHaveBeenCalledWith([
      { title: "Characters", description: "Main cast" },
      { title: "Introduction", description: "The setting" },
      { title: "Timeline", description: "Key events" },
    ]);
  });

  it("updates section title and description when user types", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(
      <OutlineEditor outline={[{ title: "Old Title", description: "Old Desc" }]} onSave={onSave} onApprove={vi.fn()} />,
    );

    const titleInput = screen.getByDisplayValue("Old Title");
    await user.clear(titleInput);
    await user.type(titleInput, "New Title");

    const descInput = screen.getByDisplayValue("Old Desc");
    await user.clear(descInput);
    await user.type(descInput, "New Desc");

    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(onSave).toHaveBeenCalledWith([
      { title: "New Title", description: "New Desc" },
    ]);
  });

  it("disables up arrow on first section and down arrow on last section", () => {
    renderWithProviders(
      <OutlineEditor outline={outline} onSave={vi.fn()} onApprove={vi.fn()} />,
    );

    const upButtons = screen.getAllByRole("button", { name: /↑/i });
    const downButtons = screen.getAllByRole("button", { name: /↓/i });

    // First section's up button should be disabled
    expect(upButtons[0]).toBeDisabled();
    // Last section's down button should be disabled
    expect(downButtons[downButtons.length - 1]).toBeDisabled();
  });
});
