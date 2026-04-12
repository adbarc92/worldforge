import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { createTestQueryClient } from "@/test/test-utils";
import { ProjectProvider } from "@/contexts/ProjectContext";
import {
  useContradictions,
  useScanContradictions,
  useResolveContradiction,
  useDismissContradiction,
  useReopenContradiction,
  useBulkUpdateContradictions,
} from "./useContradictions";

const STORAGE_KEY = "canon-builder-active-project";
const activeProject = {
  id: "proj-1",
  name: "Test Project",
  description: null,
  document_count: 0,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function seedActiveProject() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(activeProject));
}

function clearActiveProject() {
  localStorage.removeItem(STORAGE_KEY);
}

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

describe("useContradictions", () => {
  it("fetches contradictions for the active project with default status", async () => {
    seedActiveProject();
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useContradictions(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].id).toBe("contra-1");
  });

  it("passes the status argument through to the API", async () => {
    seedActiveProject();
    let receivedStatus: string | null = null;
    server.use(
      http.get("/api/v1/projects/:pid/contradictions", ({ request }) => {
        const url = new URL(request.url);
        receivedStatus = url.searchParams.get("status");
        return HttpResponse.json({ items: [], total: 0 });
      }),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useContradictions("resolved"), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receivedStatus).toBe("resolved");
  });

  it("is disabled when no active project is set", () => {
    clearActiveProject();
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useContradictions(), {
      wrapper: makeWrapper(qc),
    });
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("propagates errors", async () => {
    seedActiveProject();
    server.use(
      http.get("/api/v1/projects/:pid/contradictions", () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useContradictions(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe("boom");
  });
});

describe("useScanContradictions", () => {
  it("scans and invalidates contradictions queries", async () => {
    seedActiveProject();
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useScanContradictions(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync();
    });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["contradictions", "proj-1"],
    });
  });
});

describe("useResolveContradiction", () => {
  it("resolves and invalidates contradictions queries", async () => {
    seedActiveProject();
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useResolveContradiction(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync({ id: "contra-1", note: "done" });
    });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["contradictions", "proj-1"],
    });
  });

  it("propagates resolve errors", async () => {
    seedActiveProject();
    server.use(
      http.patch("/api/v1/projects/:pid/contradictions/:id/resolve", () =>
        HttpResponse.json({ detail: "cannot resolve" }, { status: 409 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useResolveContradiction(), {
      wrapper: makeWrapper(qc),
    });
    await expect(
      result.current.mutateAsync({ id: "contra-1" }),
    ).rejects.toThrow("cannot resolve");
  });
});

describe("useDismissContradiction", () => {
  it("dismisses and invalidates contradictions queries", async () => {
    seedActiveProject();
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useDismissContradiction(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync({ id: "contra-1" });
    });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["contradictions", "proj-1"],
    });
  });
});

describe("useReopenContradiction", () => {
  it("reopens and invalidates contradictions queries", async () => {
    seedActiveProject();
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useReopenContradiction(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync("contra-1");
    });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["contradictions", "proj-1"],
    });
  });
});

describe("useBulkUpdateContradictions", () => {
  it("bulk updates and invalidates contradictions queries", async () => {
    seedActiveProject();
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useBulkUpdateContradictions(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync({
        ids: ["contra-1", "contra-2"],
        status: "resolved",
        note: "cleanup",
      });
    });
    expect(spy).toHaveBeenCalledWith({
      queryKey: ["contradictions", "proj-1"],
    });
  });
});
