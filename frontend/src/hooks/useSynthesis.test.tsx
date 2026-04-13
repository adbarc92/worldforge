import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { createTestQueryClient, seedActiveProject } from "@/test/test-utils";
import { ProjectProvider } from "@/contexts/ProjectContext";
import {
  useSyntheses,
  useSynthesis,
  useCreateSynthesis,
  useUpdateOutline,
  useApproveSynthesis,
  useRetrySynthesis,
} from "./useSynthesis";

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <ProjectProvider>{children}</ProjectProvider>
      </QueryClientProvider>
    );
  };
}

beforeEach(() => {
  localStorage.clear();
});

describe("useSyntheses", () => {
  it("fetches syntheses for the active project", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSyntheses(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].id).toBe("synth-1");
  });

  it("is disabled when no active project is set", () => {
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSyntheses(), {
      wrapper: makeWrapper(qc),
    });
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("propagates list errors", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    server.use(
      http.get("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSyntheses(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe("boom");
  });
});

describe("useSynthesis", () => {
  it("fetches a single synthesis by id", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSynthesis("synth-1"), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.id).toBe("synth-1");
  });

  it("is disabled when id is null", () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSynthesis(null), {
      wrapper: makeWrapper(qc),
    });
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("is disabled when no active project is set", () => {
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSynthesis("synth-1"), {
      wrapper: makeWrapper(qc),
    });
    expect(result.current.fetchStatus).toBe("idle");
  });
});

describe("useCreateSynthesis", () => {
  it("creates a synthesis and invalidates the syntheses list", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useCreateSynthesis(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync(false);
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["syntheses", "proj-1"] });
  });

  it("passes the auto flag through as a query param", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    let receivedAuto: string | null = null;
    server.use(
      http.post("/api/v1/projects/:pid/synthesis", ({ request }) => {
        const url = new URL(request.url);
        receivedAuto = url.searchParams.get("auto");
        return HttpResponse.json({
          id: "synth-1",
          project_id: "proj-1",
          title: "s",
          outline: null,
          outline_approved: false,
          content: null,
          status: "outline_pending",
          error_message: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        });
      }),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useCreateSynthesis(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync(true);
    });
    expect(receivedAuto).toBe("true");
  });

  it("propagates create errors", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    server.use(
      http.post("/api/v1/projects/:pid/synthesis", () =>
        HttpResponse.json({ detail: "no docs" }, { status: 400 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useCreateSynthesis(), {
      wrapper: makeWrapper(qc),
    });
    await expect(result.current.mutateAsync(false)).rejects.toThrow("no docs");
  });
});

describe("useUpdateOutline", () => {
  it("updates the outline and invalidates the specific synthesis query", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useUpdateOutline(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync({
        id: "synth-1",
        outline: [{ title: "A", description: "B" }],
      });
    });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["synthesis", "proj-1", "synth-1"],
    });
  });
});

describe("useApproveSynthesis", () => {
  it("approves and invalidates the specific synthesis query", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useApproveSynthesis(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync("synth-1");
    });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["synthesis", "proj-1", "synth-1"],
    });
  });
});

describe("useRetrySynthesis", () => {
  it("retries and invalidates both syntheses list and specific synthesis", async () => {
    seedActiveProject({ id: "proj-1", name: "Test Project" });
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useRetrySynthesis(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync("synth-1");
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["syntheses", "proj-1"] });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["synthesis", "proj-1", "synth-1"],
    });
  });
});
