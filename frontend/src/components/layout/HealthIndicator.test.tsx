import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders } from "@/test/test-utils";
import { HealthIndicator } from "./HealthIndicator";

describe("HealthIndicator", () => {
  it("shows 'All services up' when healthy", async () => {
    renderWithProviders(<HealthIndicator />);
    await waitFor(() => {
      expect(screen.getByText(/all services up/i)).toBeInTheDocument();
    });
  });

  it("shows 'Degraded' when status is degraded", async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json({
          status: "degraded",
          services: { generator: true, embedder: false },
        }),
      ),
    );
    renderWithProviders(<HealthIndicator />);
    await waitFor(() => {
      expect(screen.getByText(/degraded/i)).toBeInTheDocument();
    });
  });

  it("shows 'Disconnected' on error", async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    renderWithProviders(<HealthIndicator />);
    await waitFor(() => {
      expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    });
  });
});
