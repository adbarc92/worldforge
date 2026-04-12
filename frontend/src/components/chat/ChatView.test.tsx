import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { ChatView } from "./ChatView";
import type { ChatMessage } from "@/hooks/useChat";

beforeEach(() => {
  // jsdom doesn't implement scrollIntoView
  Element.prototype.scrollIntoView = vi.fn();
});

describe("ChatView", () => {
  it("shows empty-state prompt when there are no messages", () => {
    renderWithProviders(
      <ChatView messages={[]} isLoading={false} onSend={vi.fn()} onClear={vi.fn()} />,
    );
    expect(screen.getByText(/ask a question about your uploaded documents/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /clear/i })).not.toBeInTheDocument();
  });

  it("renders messages and clear button", async () => {
    const user = userEvent.setup();
    const onClear = vi.fn();
    const messages: ChatMessage[] = [
      { role: "user", content: "Hi" },
      { role: "assistant", content: "Hello there" },
    ];
    renderWithProviders(
      <ChatView messages={messages} isLoading={false} onSend={vi.fn()} onClear={onClear} />,
    );
    expect(screen.getByText("Hi")).toBeInTheDocument();
    expect(screen.getByText("Hello there")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /clear/i }));
    expect(onClear).toHaveBeenCalled();
  });

  it("shows 'Thinking...' while loading", () => {
    renderWithProviders(
      <ChatView
        messages={[{ role: "user", content: "Hi" }]}
        isLoading={true}
        onSend={vi.fn()}
        onClear={vi.fn()}
      />,
    );
    expect(screen.getByText(/thinking/i)).toBeInTheDocument();
  });
});
