import { describe, it, expect } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { useChat } from "./useChat";

describe("useChat", () => {
  it("starts empty and not loading", () => {
    const { result } = renderHook(() => useChat("proj-1"));
    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it("appends the user message and assistant response on successful send", async () => {
    const { result } = renderHook(() => useChat("proj-1"));
    await act(async () => {
      await result.current.send("Who is Alice?");
    });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]).toEqual({
      role: "user",
      content: "Who is Alice?",
    });
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("An answer.");
    expect(result.current.messages[1].citations).toEqual([
      { title: "Test Document", relevance_score: 0.9 },
    ]);
  });

  it("appends an error assistant message when the API fails", async () => {
    server.use(
      http.post("/api/v1/projects/:pid/query", () =>
        HttpResponse.json({ detail: "query failed" }, { status: 500 }),
      ),
    );
    const { result } = renderHook(() => useChat("proj-1"));
    await act(async () => {
      await result.current.send("Who is Bob?");
    });
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("Error: query failed");
    expect(result.current.isLoading).toBe(false);
  });

  it("clears all messages", async () => {
    const { result } = renderHook(() => useChat("proj-1"));
    await act(async () => {
      await result.current.send("hi");
    });
    expect(result.current.messages.length).toBeGreaterThan(0);
    act(() => {
      result.current.clear();
    });
    expect(result.current.messages).toEqual([]);
  });
});
