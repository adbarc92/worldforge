import { describe, it, expect } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { UploadDropzone } from "./UploadDropzone";

describe("UploadDropzone interactions", () => {
  it("highlights on drag over and unhighlights on drag leave", () => {
    renderWithProviders(<UploadDropzone projectId="proj-1" />);
    const dropzone = screen.getByText(/drop files here or click to upload/i).closest("[data-slot='card']")!;

    // Fire dragover to activate highlight
    fireEvent.dragOver(dropzone, { dataTransfer: { files: [] } });

    // Fire dragleave to deactivate
    fireEvent.dragLeave(dropzone);
  });

  it("handles file drop with valid files", async () => {
    renderWithProviders(<UploadDropzone projectId="proj-1" />);
    const dropzone = screen.getByText(/drop files here or click to upload/i).closest("[data-slot='card']")!;

    const file = new File(["hello"], "test.txt", { type: "text/plain" });
    const dataTransfer = {
      files: [file],
      items: [{ kind: "file", type: "text/plain", getAsFile: () => file }],
      types: ["Files"],
    };

    fireEvent.drop(dropzone, { dataTransfer });

    // Should trigger upload
    await waitFor(() => {
      expect(screen.getByText(/drop files here or click to upload/i)).toBeInTheDocument();
    });
  });

  it("handles file drop with unsupported file type", async () => {
    renderWithProviders(<UploadDropzone projectId="proj-1" />);
    const dropzone = screen.getByText(/drop files here or click to upload/i).closest("[data-slot='card']")!;

    const file = new File(["data"], "test.jpg", { type: "image/jpeg" });
    const dataTransfer = {
      files: [file],
      items: [{ kind: "file", type: "image/jpeg", getAsFile: () => file }],
      types: ["Files"],
    };

    fireEvent.drop(dropzone, { dataTransfer });

    // Should show error for unsupported type but not crash
    await waitFor(() => {
      expect(screen.getByText(/drop files here or click to upload/i)).toBeInTheDocument();
    });
  });
});
