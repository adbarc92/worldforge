import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { createTestQueryClient } from "@/test/test-utils";
import {
  useProjects,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
} from "./useProjects";

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe("useProjects", () => {
  it("fetches the projects list", async () => {
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useProjects(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].id).toBe("proj-1");
  });

  it("propagates errors from the projects endpoint", async () => {
    server.use(
      http.get("/api/v1/projects", () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useProjects(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe("boom");
  });
});

describe("useCreateProject", () => {
  it("creates a project and invalidates the projects query", async () => {
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useCreateProject(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync({ name: "New", description: "d" });
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["projects"] });
  });

  it("propagates creation errors", async () => {
    server.use(
      http.post("/api/v1/projects", () =>
        HttpResponse.json({ detail: "name required" }, { status: 422 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useCreateProject(), {
      wrapper: makeWrapper(qc),
    });
    await expect(
      result.current.mutateAsync({ name: "" }),
    ).rejects.toThrow("name required");
  });
});

describe("useUpdateProject", () => {
  it("updates a project and invalidates the projects query", async () => {
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useUpdateProject(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync({
        id: "proj-1",
        data: { name: "Renamed" },
      });
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["projects"] });
  });
});

describe("useDeleteProject", () => {
  it("deletes a project and invalidates the projects query", async () => {
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useDeleteProject(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync("proj-1");
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["projects"] });
  });
});
