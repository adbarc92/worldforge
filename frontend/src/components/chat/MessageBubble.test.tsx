import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { MessageBubble } from "./MessageBubble";
import type { ChatMessage } from "@/hooks/useChat";

describe("MessageBubble", () => {
  it("renders a user message", () => {
    const msg: ChatMessage = { role: "user", content: "What is canon?" };
    renderWithProviders(<MessageBubble message={msg} />);
    expect(screen.getByText("What is canon?")).toBeInTheDocument();
  });

  it("renders an assistant message with citations", () => {
    const msg: ChatMessage = {
      role: "assistant",
      content: "Canon is the authoritative text.",
      citations: [
        { title: "Lore Bible", relevance_score: 0.87 },
        { title: "Side Notes", relevance_score: 0.42 },
      ],
    };
    renderWithProviders(<MessageBubble message={msg} />);
    expect(screen.getByText(/canon is the authoritative text/i)).toBeInTheDocument();
    expect(screen.getByText(/Lore Bible \(87%\)/)).toBeInTheDocument();
    expect(screen.getByText(/Side Notes \(42%\)/)).toBeInTheDocument();
  });

  it("renders an assistant message without citations", () => {
    const msg: ChatMessage = { role: "assistant", content: "No citations here." };
    renderWithProviders(<MessageBubble message={msg} />);
    expect(screen.getByText("No citations here.")).toBeInTheDocument();
  });
});
