import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent, seedActiveProject } from "@/test/test-utils";
import { SynthesisViewer } from "./SynthesisViewer";

describe("SynthesisViewer", () => {
  it("renders title and markdown content", () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    renderWithProviders(
      <SynthesisViewer
        synthesisId="synth-1"
        title="World Primer"
        content={"# Heading\n\nSome body text."}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.getByText("World Primer")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Heading" })).toBeInTheDocument();
    expect(screen.getByText(/some body text/i)).toBeInTheDocument();
  });

  it("calls onRegenerate when Regenerate is clicked", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const user = userEvent.setup();
    const onRegenerate = vi.fn();
    renderWithProviders(
      <SynthesisViewer
        synthesisId="synth-1"
        title="World Primer"
        content="body"
        onRegenerate={onRegenerate}
      />,
    );
    await user.click(screen.getByRole("button", { name: /regenerate/i }));
    expect(onRegenerate).toHaveBeenCalled();
  });

  it("opens the download URL in a new window", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
    const user = userEvent.setup();
    renderWithProviders(
      <SynthesisViewer
        synthesisId="synth-1"
        title="World Primer"
        content="body"
        onRegenerate={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: /download/i }));
    expect(openSpy).toHaveBeenCalledWith(
      "/api/v1/projects/proj-1/synthesis/synth-1/download",
      "_blank",
    );
    openSpy.mockRestore();
  });
});
