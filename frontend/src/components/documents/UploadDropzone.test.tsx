import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { UploadDropzone } from "./UploadDropzone";

describe("UploadDropzone", () => {
  it("renders the drop-or-click prompt", () => {
    renderWithProviders(<UploadDropzone projectId="proj-1" />);
    expect(screen.getByText(/drop files here or click to upload/i)).toBeInTheDocument();
    expect(screen.getByText(/supports \.txt, \.md, \.pdf/i)).toBeInTheDocument();
  });
});
