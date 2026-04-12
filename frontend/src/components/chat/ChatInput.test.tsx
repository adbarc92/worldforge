import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { ChatInput } from "./ChatInput";

describe("ChatInput", () => {
  it("renders the textarea and send button", () => {
    renderWithProviders(<ChatInput onSend={vi.fn()} disabled={false} />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });

  it("calls onSend when the user clicks send", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderWithProviders(<ChatInput onSend={onSend} disabled={false} />);
    await user.type(screen.getByPlaceholderText(/ask a question/i), "Hello?");
    await user.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).toHaveBeenCalledWith("Hello?");
  });

  it("calls onSend when the user presses Enter", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderWithProviders(<ChatInput onSend={onSend} disabled={false} />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    await user.type(input, "Question{Enter}");
    expect(onSend).toHaveBeenCalledWith("Question");
  });

  it("does not send empty messages", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderWithProviders(<ChatInput onSend={onSend} disabled={false} />);
    await user.type(screen.getByPlaceholderText(/ask a question/i), "   ");
    const button = screen.getByRole("button", { name: /send/i });
    expect(button).toBeDisabled();
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables input and button when disabled prop is true", () => {
    renderWithProviders(<ChatInput onSend={vi.fn()} disabled={true} />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });
});
