import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { createTestQueryClient } from "@/test/test-utils";
import { useHealth } from "./useHealth";

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe("useHealth", () => {
  it("fetches health status", async () => {
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useHealth(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.status).toBe("healthy");
    expect(result.current.data?.services.generator).toBe(true);
  });

  it("surfaces errors from the health endpoint", async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json({ detail: "bad health" }, { status: 500 }),
      ),
    );
    const qc = createTestQueryClient();
    const { result } = renderHook(() => useHealth(), {
      wrapper: makeWrapper(qc),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe("bad health");
  });
});
