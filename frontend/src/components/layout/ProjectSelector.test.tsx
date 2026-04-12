import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { ProjectSelector } from "./ProjectSelector";

describe("ProjectSelector", () => {
  it("renders the project dropdown with the list of projects", async () => {
    renderWithProviders(<ProjectSelector />);
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "Test Project" })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /manage projects/i })).toBeInTheDocument();
  });

  it("shows loading state while fetching projects", () => {
    server.use(
      http.get("/api/v1/projects", async () => {
        await new Promise((resolve) => setTimeout(resolve, 50));
        return HttpResponse.json([]);
      }),
    );
    renderWithProviders(<ProjectSelector />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("allows selecting a project from the dropdown", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProjectSelector />);
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "Test Project" })).toBeInTheDocument();
    });
    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "proj-1");
    expect((select as HTMLSelectElement).value).toBe("proj-1");
  });
});
