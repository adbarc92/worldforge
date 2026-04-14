import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { createTestQueryClient } from "@/test/test-utils";
import {
  useDocuments,
  useUploadDocument,
  useDeleteDocument,
} from "./useDocuments";

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe("useDocuments", () => {
  it("fetches the documents list for a project", async () => {
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useDocuments("proj-1"), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].id).toBe("doc-1");
  });

  it("does not fetch when projectId is empty", () => {
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useDocuments(""), {
      wrapper: makeWrapper(qc),
    });
    expect(result.current.fetchStatus).toBe("idle");
    expect(result.current.data).toBeUndefined();
  });

  it("propagates errors from the documents endpoint", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/documents", () =>
        HttpResponse.json({ detail: "not found" }, { status: 404 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useDocuments("proj-1"), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe("not found");
  });
});

describe("useUploadDocument", () => {
  it("uploads a file and invalidates the documents query", async () => {
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useUploadDocument("proj-1"), {
      wrapper: makeWrapper(qc),
    });
    const file = new File(["hello"], "hello.md", { type: "text/markdown" });
    await act(async () => {
      await result.current.mutateAsync(file);
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["documents", "proj-1"] });
  });

  it("propagates upload errors", async () => {
    server.use(
      http.post("/api/v1/projects/:pid/documents/upload", () =>
        HttpResponse.json({ detail: "bad file" }, { status: 400 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useUploadDocument("proj-1"), {
      wrapper: makeWrapper(qc),
    });
    const file = new File(["x"], "x.md");
    await expect(result.current.mutateAsync(file)).rejects.toThrow("bad file");
  });
});

describe("useDeleteDocument", () => {
  it("deletes a document and invalidates the documents query", async () => {
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useDeleteDocument("proj-1"), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync("doc-1");
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["documents", "proj-1"] });
  });
});
