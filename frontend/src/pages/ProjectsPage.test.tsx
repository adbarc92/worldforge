import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders } from "@/test/test-utils";
import { ProjectsPage } from "./ProjectsPage";

describe("ProjectsPage", () => {
  it("loads and displays the list of projects", async () => {
    renderWithProviders(<ProjectsPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });
    expect(screen.getByText(/a test project/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new project/i })).toBeInTheDocument();
  });

  it("shows empty state when there are no projects", async () => {
    server.use(http.get("/api/v1/projects", () => HttpResponse.json([])));
    renderWithProviders(<ProjectsPage />);
    await waitFor(() => {
      expect(
        screen.getByText(/no projects yet\. create one to get started/i),
      ).toBeInTheDocument();
    });
  });
});
