import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders, userEvent, seedActiveProject } from "@/test/test-utils";
import { ChatPage } from "./ChatPage";

beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

describe("ChatPage", () => {
  it("prompts to select a project when no project is active", () => {
    renderWithProviders(<ChatPage />);
    expect(screen.getByText(/select a project to start chatting/i)).toBeInTheDocument();
  });

  it("renders the chat view when a project is active", () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    renderWithProviders(<ChatPage />);
    expect(
      screen.getByPlaceholderText(/ask a question about your documents/i),
    ).toBeInTheDocument();
  });

  it("sends a message and renders the response", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const user = userEvent.setup();
    renderWithProviders(<ChatPage />);
    const input = screen.getByPlaceholderText(/ask a question about your documents/i);
    await user.type(input, "What is canon?");
    await user.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText("An answer.")).toBeInTheDocument();
    });
    expect(screen.getByText("What is canon?")).toBeInTheDocument();
  });
});
