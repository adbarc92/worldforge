import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { createTestQueryClient } from "@/test/test-utils";
import { useSettings, useUpdateSettings } from "./useSettings";

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe("useSettings", () => {
  it("fetches settings", async () => {
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSettings(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.anthropic_model).toBe("claude-sonnet-4-20250514");
    expect(result.current.data?.openai_embedding_model).toBe(
      "text-embedding-3-large",
    );
  });

  it("propagates errors from the settings endpoint", async () => {
    server.use(
      http.get("/api/v1/settings", () =>
        HttpResponse.json({ detail: "nope" }, { status: 500 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useSettings(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe("nope");
  });
});

describe("useUpdateSettings", () => {
  it("updates settings and invalidates settings + health queries", async () => {
    const qc = createTestQueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useUpdateSettings(), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync({ anthropic_model: "claude-opus-4" });
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["settings"] });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["health"] });
  });

  it("propagates update errors", async () => {
    server.use(
      http.put("/api/v1/settings", () =>
        HttpResponse.json({ detail: "invalid key" }, { status: 400 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useUpdateSettings(), {
      wrapper: makeWrapper(qc),
    });
    await expect(
      result.current.mutateAsync({ anthropic_api_key: "bad" }),
    ).rejects.toThrow("invalid key");
  });
});
