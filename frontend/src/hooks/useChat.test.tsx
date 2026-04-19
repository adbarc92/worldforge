import { describe, it, expect } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/mocks/server";
import { createTestQueryClient } from "@/test/test-utils";
import { ProjectProvider } from "@/contexts/ProjectContext";
import { useChat } from "./useChat";

const STORAGE_KEY = "canon-builder-active-project";

function makeWrapper() {
  const queryClient = createTestQueryClient();
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>{children}</ProjectProvider>
    </QueryClientProvider>
  );
}

describe("useChat", () => {
  it("starts empty and not loading", () => {
    const { result } = renderHook(() => useChat("proj-1"), {
      wrapper: makeWrapper(),
    });
    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it("appends the user message and assistant response on successful send", async () => {
    const { result } = renderHook(() => useChat("proj-1"), {
      wrapper: makeWrapper(),
    });
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
    const { result } = renderHook(() => useChat("proj-1"), {
      wrapper: makeWrapper(),
    });
    await act(async () => {
      await result.current.send("Who is Bob?");
    });
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("Error: query failed");
    expect(result.current.isLoading).toBe(false);
  });

  it("clears all messages", async () => {
    const { result } = renderHook(() => useChat("proj-1"), {
      wrapper: makeWrapper(),
    });
    await act(async () => {
      await result.current.send("hi");
    });
    expect(result.current.messages.length).toBeGreaterThan(0);
    act(() => {
      result.current.clear();
    });
    expect(result.current.messages).toEqual([]);
  });

  it("clears activeProject on 404 so the UI self-heals from a deleted project", async () => {
    // Seed a stored active project the server will report as missing
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        id: "deleted-proj",
        name: "Ghost",
        description: null,
        document_count: 0,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      }),
    );

    server.use(
      http.post("/api/v1/projects/:pid/query", () =>
        HttpResponse.json({ detail: "Project not found" }, { status: 404 }),
      ),
    );

    const { result } = renderHook(() => useChat("deleted-proj"), {
      wrapper: makeWrapper(),
    });
    await act(async () => {
      await result.current.send("anything");
    });

    // Error shown to user
    expect(result.current.messages[1].content).toBe("Error: Project not found");
    // And activeProject cleared from storage
    await waitFor(() => {
      expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });

    localStorage.clear();
  });
});
