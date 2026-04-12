import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { Sidebar } from "./Sidebar";

describe("Sidebar", () => {
  it("renders the app title and all nav links", async () => {
    renderWithProviders(<Sidebar />);
    expect(screen.getByText("Canon Builder")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /chat/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /documents/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /contradictions/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /synthesis/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /projects/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /settings/i })).toBeInTheDocument();
  });

  it("renders the health indicator", async () => {
    renderWithProviders(<Sidebar />);
    await waitFor(() => {
      expect(screen.getByText(/all services up/i)).toBeInTheDocument();
    });
  });
});
