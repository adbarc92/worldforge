import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders } from "@/test/test-utils";
import { SettingsPage } from "./SettingsPage";

describe("SettingsPage", () => {
  it("loads settings and shows service status + model inputs", async () => {
    renderWithProviders(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/service status/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/anthropic api key/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue("claude-sonnet-4-20250514")).toBeInTheDocument();
    expect(screen.getByDisplayValue("text-embedding-3-large")).toBeInTheDocument();
  });

  it("shows loading state before settings resolve", () => {
    server.use(
      http.get("/api/v1/settings", async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return HttpResponse.json({});
      }),
    );
    renderWithProviders(<SettingsPage />);
    expect(screen.getByText(/loading settings/i)).toBeInTheDocument();
  });
});
