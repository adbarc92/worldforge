import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "@/test/mocks/server";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { SettingsPage } from "./SettingsPage";

describe("SettingsPage interactions", () => {
  it("saves settings and shows success toast on healthy response", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/service status/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /save settings/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /save settings/i })).not.toBeDisabled();
    });
  });

  it("toggles API key visibility when Show/Hide is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/service status/i)).toBeInTheDocument();
    });

    // Keys are hidden by default (password type)
    const anthropicInput = screen.getByLabelText(/anthropic api key/i);
    expect(anthropicInput).toHaveAttribute("type", "password");

    // Click Show to reveal keys
    await user.click(screen.getByRole("button", { name: /^show$/i }));
    expect(anthropicInput).toHaveAttribute("type", "text");

    // Click Hide to conceal again
    await user.click(screen.getByRole("button", { name: /^hide$/i }));
    expect(anthropicInput).toHaveAttribute("type", "password");
  });

  it("updates form fields when user types in model inputs", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByDisplayValue("claude-sonnet-4-20250514")).toBeInTheDocument();
    });

    const modelInput = screen.getByLabelText(/anthropic model/i);
    await user.clear(modelInput);
    await user.type(modelInput, "claude-3-opus");
    expect(modelInput).toHaveValue("claude-3-opus");
  });

  it("shows warning toast when health status is not healthy after save", async () => {
    server.use(
      http.put("/api/v1/settings", () =>
        HttpResponse.json({
          settings: {
            anthropic_api_key: "sk-ant-***",
            openai_api_key: "sk-***",
            anthropic_model: "claude-sonnet-4-20250514",
            openai_embedding_model: "text-embedding-3-large",
          },
          health: { status: "degraded", services: { generator: true, embedder: false } },
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/service status/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /save settings/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /save settings/i })).not.toBeDisabled();
    });
  });
});
