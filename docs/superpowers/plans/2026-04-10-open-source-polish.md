# Open-Source Polish Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take WorldForge from working personal tool to professional open-source release: frontend test suite, CI/CD pipelines, contributor infrastructure, metadata cleanup, merge `feat/multiple-projects` → `main`, tag v1.0.0.

**Architecture:** Three parallel workstreams (A: frontend tests, B: CI/CD, C: docs & metadata) followed by a sequential integration phase (D). All workstreams commit directly to `feat/multiple-projects`. Workstreams A and B have no file overlap. Workstreams A and C both touch `frontend/package.json` — A owns the `scripts` section, C owns the top-level metadata fields; each agent is instructed to preserve the other's concurrent edits and the integration step resolves conflicts if they occur.

**Tech Stack:** Vitest, React Testing Library, MSW (frontend testing); GitHub Actions + UV + Node 20 + GHCR (CI/CD); Markdown for contributor docs; UV + npm for package management.

**Reference spec:** `docs/superpowers/specs/2026-04-10-open-source-polish-design.md`

---

## Execution Order

```
[Phase 1: parallel]
  Workstream A: Frontend Tests (Tasks A1-A10)
  Workstream B: CI/CD          (Tasks B1-B6)
  Workstream C: Docs & Metadata (Tasks C1-C8)

[Phase 2: sequential, after all of A+B+C complete]
  Workstream D: Integration    (Tasks D1-D7)
```

---

# Workstream A: Frontend Tests

**Owner:** Agent A
**Files owned:** `frontend/vitest.config.ts`, `frontend/src/test/**`, `frontend/src/**/*.test.ts[x]`, `frontend/package.json` (scripts + devDependencies sections only — NOT top-level metadata)
**Concurrent edits:** Agent C may also edit `frontend/package.json` (metadata fields). Agent A must re-read the file before each edit and preserve any changes from Agent C.

## Task A1: Install test dependencies

**Files:**
- Modify: `frontend/package.json` (devDependencies + scripts sections only)

- [ ] **Step 1: Install Vitest and testing libraries**

```bash
cd frontend
npm install -D vitest @vitest/ui @vitest/coverage-v8 jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event msw
```

- [ ] **Step 2: Verify package.json was updated**

Open `frontend/package.json` and confirm these appear in `devDependencies`:
- `vitest`
- `@vitest/ui`
- `@vitest/coverage-v8`
- `jsdom`
- `@testing-library/react`
- `@testing-library/jest-dom`
- `@testing-library/user-event`
- `msw`

- [ ] **Step 3: Add test and typecheck scripts to package.json**

Re-read `frontend/package.json` (Agent C may have edited it concurrently). In the `scripts` section, add:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui",
    "typecheck": "tsc -b --noEmit"
  }
}
```

Preserve all other fields exactly as they are.

- [ ] **Step 4: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(frontend): add Vitest and testing library dependencies"
```

---

## Task A2: Create Vitest configuration

**Files:**
- Create: `frontend/vitest.config.ts`

- [ ] **Step 1: Create Vitest config**

Create `frontend/vitest.config.ts` with this exact content:

```typescript
/// <reference types="vitest" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.{ts,tsx}",
        "src/test/**",
        "src/main.tsx",
        "src/vite-env.d.ts",
        "src/**/*.d.ts",
      ],
      thresholds: {
        lines: 70,
        branches: 65,
        functions: 70,
        statements: 70,
      },
    },
  },
});
```

**Note:** We explicitly do NOT load `tailwindcss()` in the test plugins list — it's unnecessary overhead for tests.

- [ ] **Step 2: Update tsconfig to include vitest types**

Open `frontend/tsconfig.app.json`. Find the `types` array:

```json
"types": ["vite/client"],
```

Replace with:

```json
"types": ["vite/client", "vitest/globals", "@testing-library/jest-dom"],
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend
npm run typecheck
```

Expected: exit code 0 (no errors). If errors, they will be about missing test files — that's fine for now; we'll add them in subsequent tasks.

- [ ] **Step 4: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/vitest.config.ts frontend/tsconfig.app.json
git commit -m "chore(frontend): add Vitest config with coverage thresholds"
```

---

## Task A3: Create test setup and utilities

**Files:**
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/test/test-utils.tsx`
- Create: `frontend/src/test/mocks/handlers.ts`
- Create: `frontend/src/test/mocks/server.ts`

- [ ] **Step 1: Create test setup file**

Create `frontend/src/test/setup.ts`:

```typescript
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "./mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
```

- [ ] **Step 2: Create MSW server**

Create `frontend/src/test/mocks/server.ts`:

```typescript
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

- [ ] **Step 3: Create MSW default handlers**

Create `frontend/src/test/mocks/handlers.ts`:

```typescript
import { http, HttpResponse } from "msw";

const mockProject = {
  id: "proj-1",
  name: "Test Project",
  description: "A test project",
  document_count: 2,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockDocument = {
  id: "doc-1",
  title: "Test Document",
  status: "completed",
  chunk_count: 10,
  file_path: "/data/test.md",
  created_at: "2026-01-01T00:00:00Z",
};

const mockHealth = {
  status: "healthy" as const,
  services: { generator: true, embedder: true },
};

const mockSettings = {
  anthropic_api_key: "sk-ant-***",
  openai_api_key: "sk-***",
  anthropic_model: "claude-sonnet-4-20250514",
  openai_embedding_model: "text-embedding-3-large",
};

const mockContradiction = {
  id: "contra-1",
  chunk_a_text: "Alice is tall.",
  chunk_b_text: "Alice is short.",
  document_a_id: "doc-1",
  document_b_id: "doc-2",
  document_a_title: "Doc A",
  document_b_title: "Doc B",
  explanation: "Height conflict",
  status: "open" as const,
  resolution_note: null,
  created_at: "2026-01-01T00:00:00Z",
  resolved_at: null,
};

const mockSynthesis = {
  id: "synth-1",
  project_id: "proj-1",
  title: "World Synthesis",
  outline: [{ title: "Introduction", description: "Overview" }],
  outline_approved: false,
  content: null,
  status: "outline_ready" as const,
  error_message: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

export const handlers = [
  http.get("/health", () => HttpResponse.json(mockHealth)),

  // Projects
  http.get("/api/v1/projects", () => HttpResponse.json([mockProject])),
  http.get("/api/v1/projects/:id", () => HttpResponse.json(mockProject)),
  http.post("/api/v1/projects", () => HttpResponse.json(mockProject)),
  http.put("/api/v1/projects/:id", () => HttpResponse.json(mockProject)),
  http.delete("/api/v1/projects/:id", () => HttpResponse.json({ status: "deleted" })),

  // Documents
  http.get("/api/v1/projects/:pid/documents", () => HttpResponse.json([mockDocument])),
  http.get("/api/v1/projects/:pid/documents/:id", () => HttpResponse.json(mockDocument)),
  http.delete("/api/v1/projects/:pid/documents/:id", () =>
    HttpResponse.json({ status: "deleted" }),
  ),
  http.post("/api/v1/projects/:pid/documents/upload", () => HttpResponse.json(mockDocument)),

  // Query
  http.post("/api/v1/projects/:pid/query", () =>
    HttpResponse.json({
      answer: "An answer.",
      citations: [{ title: "Test Document", relevance_score: 0.9 }],
    }),
  ),

  // Settings
  http.get("/api/v1/settings", () => HttpResponse.json(mockSettings)),
  http.put("/api/v1/settings", () =>
    HttpResponse.json({ settings: mockSettings, health: mockHealth }),
  ),

  // Contradictions
  http.get("/api/v1/projects/:pid/contradictions", () =>
    HttpResponse.json({ items: [mockContradiction], total: 1 }),
  ),
  http.post("/api/v1/projects/:pid/contradictions/scan", () =>
    HttpResponse.json({ status: "scanning", project_id: "proj-1" }),
  ),
  http.patch("/api/v1/projects/:pid/contradictions/:id/resolve", () =>
    HttpResponse.json({ id: "contra-1", status: "resolved" }),
  ),
  http.patch("/api/v1/projects/:pid/contradictions/:id/dismiss", () =>
    HttpResponse.json({ id: "contra-1", status: "dismissed" }),
  ),
  http.patch("/api/v1/projects/:pid/contradictions/:id/reopen", () =>
    HttpResponse.json({ id: "contra-1", status: "open" }),
  ),
  http.post("/api/v1/projects/:pid/contradictions/bulk", () =>
    HttpResponse.json({ updated: 1, status: "resolved" }),
  ),

  // Synthesis
  http.get("/api/v1/projects/:pid/synthesis", () => HttpResponse.json([mockSynthesis])),
  http.get("/api/v1/projects/:pid/synthesis/:id", () => HttpResponse.json(mockSynthesis)),
  http.post("/api/v1/projects/:pid/synthesis", () => HttpResponse.json(mockSynthesis)),
  http.patch("/api/v1/projects/:pid/synthesis/:id/outline", () =>
    HttpResponse.json(mockSynthesis),
  ),
  http.post("/api/v1/projects/:pid/synthesis/:id/approve", () =>
    HttpResponse.json({ id: "synth-1", status: "generating" }),
  ),
  http.post("/api/v1/projects/:pid/synthesis/:id/retry", () =>
    HttpResponse.json({ id: "synth-1", status: "generating" }),
  ),
];
```

- [ ] **Step 4: Create test-utils with providers**

Create `frontend/src/test/test-utils.tsx`:

```typescript
import { ReactElement, ReactNode } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

interface WrapperProps {
  children: ReactNode;
  initialRoute?: string;
}

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

function AllProviders({ children, initialRoute = "/" }: WrapperProps) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  initialRoute?: string;
}

export function renderWithProviders(
  ui: ReactElement,
  { initialRoute, ...options }: CustomRenderOptions = {},
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders initialRoute={initialRoute}>{children}</AllProviders>
    ),
    ...options,
  });
}

export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";
```

- [ ] **Step 5: Run the test runner with no tests to verify setup works**

```bash
cd frontend
npx vitest run --passWithNoTests
```

Expected: exits successfully with "No test files found" or similar — confirms the config loads without errors.

- [ ] **Step 6: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/src/test/
git commit -m "chore(frontend): add test setup, MSW handlers, and render utilities"
```

---

## Task A4: API client tests

**Files:**
- Create: `frontend/src/lib/api.test.ts`

- [ ] **Step 1: Write API client tests**

Create `frontend/src/lib/api.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { api } from "./api";

describe("api.health", () => {
  it("fetches health status", async () => {
    const result = await api.health();
    expect(result.status).toBe("healthy");
    expect(result.services.generator).toBe(true);
  });

  it("throws on error responses", async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json({ detail: "server error" }, { status: 500 }),
      ),
    );
    await expect(api.health()).rejects.toThrow("server error");
  });

  it("throws with statusText when response has no detail", async () => {
    server.use(http.get("/health", () => new HttpResponse(null, { status: 503 })));
    await expect(api.health()).rejects.toThrow();
  });
});

describe("api.projects", () => {
  it("list fetches all projects", async () => {
    const result = await api.projects.list();
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("proj-1");
  });

  it("get fetches a single project", async () => {
    const result = await api.projects.get("proj-1");
    expect(result.id).toBe("proj-1");
  });

  it("create posts project data", async () => {
    let receivedBody: unknown;
    server.use(
      http.post("/api/v1/projects", async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          id: "new-proj",
          name: "New",
          description: null,
          document_count: 0,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        });
      }),
    );
    const result = await api.projects.create({ name: "New", description: "desc" });
    expect(receivedBody).toEqual({ name: "New", description: "desc" });
    expect(result.id).toBe("new-proj");
  });

  it("update puts project changes", async () => {
    let receivedBody: unknown;
    server.use(
      http.put("/api/v1/projects/:id", async ({ request, params }) => {
        receivedBody = await request.json();
        expect(params.id).toBe("proj-1");
        return HttpResponse.json({
          id: "proj-1",
          name: "Updated",
          description: null,
          document_count: 0,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        });
      }),
    );
    await api.projects.update("proj-1", { name: "Updated" });
    expect(receivedBody).toEqual({ name: "Updated" });
  });

  it("delete removes a project", async () => {
    const result = await api.projects.delete("proj-1");
    expect(result.status).toBe("deleted");
  });
});

describe("api.documents", () => {
  it("list uses pagination parameters", async () => {
    let receivedUrl = "";
    server.use(
      http.get("/api/v1/projects/:pid/documents", ({ request }) => {
        receivedUrl = request.url;
        return HttpResponse.json([]);
      }),
    );
    await api.documents.list("proj-1", 10, 20);
    expect(receivedUrl).toContain("skip=10");
    expect(receivedUrl).toContain("limit=20");
  });

  it("list uses defaults when skip/limit not provided", async () => {
    let receivedUrl = "";
    server.use(
      http.get("/api/v1/projects/:pid/documents", ({ request }) => {
        receivedUrl = request.url;
        return HttpResponse.json([]);
      }),
    );
    await api.documents.list("proj-1");
    expect(receivedUrl).toContain("skip=0");
    expect(receivedUrl).toContain("limit=50");
  });

  it("get fetches a single document", async () => {
    const result = await api.documents.get("proj-1", "doc-1");
    expect(result.id).toBe("doc-1");
  });

  it("delete removes a document", async () => {
    const result = await api.documents.delete("proj-1", "doc-1");
    expect(result.status).toBe("deleted");
  });

  it("upload sends FormData with file", async () => {
    let receivedHeaders: Headers | null = null;
    server.use(
      http.post("/api/v1/projects/:pid/documents/upload", ({ request }) => {
        receivedHeaders = request.headers;
        return HttpResponse.json({
          id: "doc-new",
          title: "test.md",
          status: "pending",
          chunk_count: 0,
        });
      }),
    );
    const file = new File(["content"], "test.md", { type: "text/markdown" });
    const result = await api.documents.upload("proj-1", file);
    expect(result.id).toBe("doc-new");
    // FormData requests set multipart/form-data; ensure we did NOT set JSON
    expect(receivedHeaders?.get("content-type")).toContain("multipart/form-data");
  });

  it("upload throws on failure", async () => {
    server.use(
      http.post("/api/v1/projects/:pid/documents/upload", () =>
        HttpResponse.json({ detail: "upload failed" }, { status: 400 }),
      ),
    );
    const file = new File(["x"], "x.md");
    await expect(api.documents.upload("proj-1", file)).rejects.toThrow("upload failed");
  });
});

describe("api.query", () => {
  it("posts question with top_k", async () => {
    let receivedBody: unknown;
    server.use(
      http.post("/api/v1/projects/:pid/query", async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ answer: "ok", citations: [] });
      }),
    );
    await api.query("proj-1", "who is Alice?", 5);
    expect(receivedBody).toEqual({ question: "who is Alice?", top_k: 5 });
  });

  it("defaults top_k to 10", async () => {
    let receivedBody: { top_k?: number } = {};
    server.use(
      http.post("/api/v1/projects/:pid/query", async ({ request }) => {
        receivedBody = (await request.json()) as { top_k?: number };
        return HttpResponse.json({ answer: "ok", citations: [] });
      }),
    );
    await api.query("proj-1", "question");
    expect(receivedBody.top_k).toBe(10);
  });
});

describe("api.settings", () => {
  it("get fetches settings", async () => {
    const result = await api.settings.get();
    expect(result.anthropic_model).toBe("claude-sonnet-4-20250514");
  });

  it("update puts settings", async () => {
    const result = await api.settings.update({ anthropic_model: "new-model" });
    expect(result.settings).toBeDefined();
    expect(result.health).toBeDefined();
  });
});

describe("api.contradictions", () => {
  it("list uses query parameters", async () => {
    let receivedUrl = "";
    server.use(
      http.get("/api/v1/projects/:pid/contradictions", ({ request }) => {
        receivedUrl = request.url;
        return HttpResponse.json({ items: [], total: 0 });
      }),
    );
    await api.contradictions.list("proj-1", "resolved", 5, 25);
    expect(receivedUrl).toContain("status=resolved");
    expect(receivedUrl).toContain("skip=5");
    expect(receivedUrl).toContain("limit=25");
  });

  it("scan posts to scan endpoint", async () => {
    const result = await api.contradictions.scan("proj-1");
    expect(result.status).toBe("scanning");
  });

  it("resolve sends note", async () => {
    let receivedBody: unknown;
    server.use(
      http.patch("/api/v1/projects/:pid/contradictions/:id/resolve", async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ id: "contra-1", status: "resolved" });
      }),
    );
    await api.contradictions.resolve("proj-1", "contra-1", "fixed it");
    expect(receivedBody).toEqual({ note: "fixed it" });
  });

  it("resolve sends null note when omitted", async () => {
    let receivedBody: { note?: string | null } = {};
    server.use(
      http.patch("/api/v1/projects/:pid/contradictions/:id/resolve", async ({ request }) => {
        receivedBody = (await request.json()) as { note: string | null };
        return HttpResponse.json({ id: "contra-1", status: "resolved" });
      }),
    );
    await api.contradictions.resolve("proj-1", "contra-1");
    expect(receivedBody.note).toBeNull();
  });

  it("dismiss sends PATCH", async () => {
    const result = await api.contradictions.dismiss("proj-1", "contra-1");
    expect(result.status).toBe("dismissed");
  });

  it("reopen sends PATCH", async () => {
    const result = await api.contradictions.reopen("proj-1", "contra-1");
    expect(result.status).toBe("open");
  });

  it("bulk sends ids and status", async () => {
    let receivedBody: unknown;
    server.use(
      http.post("/api/v1/projects/:pid/contradictions/bulk", async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ updated: 2, status: "resolved" });
      }),
    );
    await api.contradictions.bulk("proj-1", ["a", "b"], "resolved", "batch");
    expect(receivedBody).toEqual({ ids: ["a", "b"], status: "resolved", note: "batch" });
  });
});

describe("api.synthesis", () => {
  it("list fetches all syntheses", async () => {
    const result = await api.synthesis.list("proj-1");
    expect(result).toHaveLength(1);
  });

  it("get fetches a single synthesis", async () => {
    const result = await api.synthesis.get("proj-1", "synth-1");
    expect(result.id).toBe("synth-1");
  });

  it("create with auto=true adds query param", async () => {
    let receivedUrl = "";
    server.use(
      http.post("/api/v1/projects/:pid/synthesis", ({ request }) => {
        receivedUrl = request.url;
        return HttpResponse.json({
          id: "s",
          project_id: "proj-1",
          title: "t",
          outline: null,
          outline_approved: false,
          content: null,
          status: "outline_pending",
          error_message: null,
          created_at: "",
          updated_at: "",
        });
      }),
    );
    await api.synthesis.create("proj-1", true);
    expect(receivedUrl).toContain("auto=true");
  });

  it("updateOutline sends outline array", async () => {
    let receivedBody: unknown;
    server.use(
      http.patch("/api/v1/projects/:pid/synthesis/:id/outline", async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          id: "s",
          project_id: "proj-1",
          title: "t",
          outline: null,
          outline_approved: false,
          content: null,
          status: "outline_ready",
          error_message: null,
          created_at: "",
          updated_at: "",
        });
      }),
    );
    const outline = [{ title: "S1", description: "d" }];
    await api.synthesis.updateOutline("proj-1", "synth-1", outline);
    expect(receivedBody).toEqual({ outline });
  });

  it("approve sends POST", async () => {
    const result = await api.synthesis.approve("proj-1", "synth-1");
    expect(result.status).toBe("generating");
  });

  it("retry sends POST", async () => {
    const result = await api.synthesis.retry("proj-1", "synth-1");
    expect(result.status).toBe("generating");
  });

  it("download returns a URL string (not a fetch)", () => {
    const url = api.synthesis.download("proj-1", "synth-1");
    expect(url).toBe("/api/v1/projects/proj-1/synthesis/synth-1/download");
  });
});
```

- [ ] **Step 2: Run the API tests**

```bash
cd frontend
npx vitest run src/lib/api.test.ts
```

Expected: All tests pass. If any fail because the actual `api.ts` signature differs from my assumptions above, fix the test to match the real signature.

- [ ] **Step 3: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/src/lib/api.test.ts
git commit -m "test(frontend): add comprehensive API client tests"
```

---

## Task A5: Hook tests

**Files:**
- Create: `frontend/src/hooks/useHealth.test.ts`
- Create: `frontend/src/hooks/useDocuments.test.ts`
- Create: `frontend/src/hooks/useProjects.test.ts`
- Create: `frontend/src/hooks/useSettings.test.ts`
- Create: `frontend/src/hooks/useContradictions.test.ts`
- Create: `frontend/src/hooks/useSynthesis.test.ts`
- Create: `frontend/src/hooks/useChat.test.ts`

**Context:** Before writing each test file, read the corresponding hook source to confirm its exported names and signatures. The pattern below is the template. `useDocuments.ts` is fully-shown for reference.

- [ ] **Step 1: Read each hook source file**

```bash
ls frontend/src/hooks/
```

For each hook, `cat` or open the file and note: exported function names, input parameters, return structure.

- [ ] **Step 2: Write `useHealth.test.ts`**

Create `frontend/src/hooks/useHealth.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { createTestQueryClient } from "@/test/test-utils";
import { useHealth } from "./useHealth";

function wrapper({ children }: { children: ReactNode }) {
  const qc = createTestQueryClient();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("useHealth", () => {
  it("fetches health status on mount", async () => {
    const { result } = renderHook(() => useHealth(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.status).toBe("healthy");
  });
});
```

If `useHealth` takes arguments or returns differently, adapt accordingly.

- [ ] **Step 3: Write `useDocuments.test.ts`**

Create `frontend/src/hooks/useDocuments.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { createTestQueryClient } from "@/test/test-utils";
import { useDocuments, useUploadDocument, useDeleteDocument } from "./useDocuments";

function makeWrapper(qc: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useDocuments", () => {
  it("returns documents for a project", async () => {
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
  });
});

describe("useUploadDocument", () => {
  it("invalidates documents query on success", async () => {
    const qc = createTestQueryClient();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useUploadDocument("proj-1"), {
      wrapper: makeWrapper(qc),
    });

    const file = new File(["x"], "x.md");
    await act(async () => {
      await result.current.mutateAsync(file);
    });

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["documents", "proj-1"],
    });
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
  it("calls delete endpoint and invalidates", async () => {
    const qc = createTestQueryClient();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");
    const { result } = renderHook(() => useDeleteDocument("proj-1"), {
      wrapper: makeWrapper(qc),
    });
    await act(async () => {
      await result.current.mutateAsync("doc-1");
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["documents", "proj-1"],
    });
  });
});
```

Add `import { vi } from "vitest";` at the top.

- [ ] **Step 4: Apply the same pattern to the remaining hooks**

For each of `useProjects`, `useSettings`, `useContradictions`, `useSynthesis`, `useChat`:

1. Read the hook source (`cat frontend/src/hooks/<name>.ts`)
2. Note every exported function (queries and mutations)
3. Create `<name>.test.ts` using the patterns above:
   - For queries: render hook → wait for `isSuccess` → assert on `data`
   - For mutations: spy on `qc.invalidateQueries` or track side effects → call `mutateAsync` in `act` → assert
   - Include one error-path test per file using `server.use()` to override a handler

Minimum per file:
- One "happy path" test per exported function
- One error-path test
- Any parameter-variation tests relevant to the function (e.g., optional args, default values)

- [ ] **Step 5: Run all hook tests**

```bash
cd frontend
npx vitest run src/hooks/
```

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/src/hooks/
git commit -m "test(frontend): add hook tests with MSW-mocked API"
```

---

## Task A6: Layout and UI component tests

**Files:**
- Create: `frontend/src/components/layout/HealthIndicator.test.tsx`
- Create: `frontend/src/components/layout/Sidebar.test.tsx`
- Create: `frontend/src/components/layout/Shell.test.tsx`
- Create: `frontend/src/components/layout/ProjectSelector.test.tsx`

**Context:** Read each component's source before writing its test — the tests below are patterns you adapt to the actual props/structure.

- [ ] **Step 1: Read the layout components**

```bash
cat frontend/src/components/layout/HealthIndicator.tsx
cat frontend/src/components/layout/Sidebar.tsx
cat frontend/src/components/layout/Shell.tsx
cat frontend/src/components/layout/ProjectSelector.tsx
```

Note: exact prop names, what text/labels are rendered, what sub-components are used.

- [ ] **Step 2: Write `HealthIndicator.test.tsx`**

Pattern template — adapt to the actual component:

```typescript
import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { renderWithProviders } from "@/test/test-utils";
import { HealthIndicator } from "./HealthIndicator";

describe("HealthIndicator", () => {
  it("shows healthy state when API reports healthy", async () => {
    renderWithProviders(<HealthIndicator />);
    // Adapt: check for whatever visible indicator the component uses
    // e.g. await waitFor(() => expect(screen.getByLabelText(/healthy/i)).toBeInTheDocument());
    await waitFor(() => {
      // Replace with the actual assertion after reading the component
      expect(document.body.textContent).toBeTruthy();
    });
  });

  it("shows degraded/error state when API returns error", async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json({ detail: "down" }, { status: 503 }),
      ),
    );
    renderWithProviders(<HealthIndicator />);
    await waitFor(() => {
      // Adapt the assertion to match actual degraded-state rendering
      expect(document.body.textContent).toBeTruthy();
    });
  });
});
```

Replace both the "adapt" comments with real assertions based on the component's actual rendered output.

- [ ] **Step 3: Write `Sidebar.test.tsx`**

```typescript
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { Sidebar } from "./Sidebar";

describe("Sidebar", () => {
  it("renders navigation links", () => {
    renderWithProviders(<Sidebar />);
    // After reading Sidebar.tsx, assert on each nav link's text.
    // Example pattern — replace with actual link texts:
    // expect(screen.getByRole("link", { name: /chat/i })).toBeInTheDocument();
    // expect(screen.getByRole("link", { name: /documents/i })).toBeInTheDocument();
    // expect(screen.getByRole("link", { name: /projects/i })).toBeInTheDocument();
    // expect(screen.getByRole("link", { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { hidden: true })).toBeTruthy();
  });
});
```

- [ ] **Step 4: Write `Shell.test.tsx`**

```typescript
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { Shell } from "./Shell";

describe("Shell", () => {
  it("renders its children inside the layout", () => {
    renderWithProviders(
      <Shell>
        <div data-testid="test-child">child content</div>
      </Shell>,
    );
    expect(screen.getByTestId("test-child")).toBeInTheDocument();
    expect(screen.getByText("child content")).toBeInTheDocument();
  });
});
```

If `Shell` does not take `children` as a prop (e.g., uses React Router's `<Outlet>`), adapt by using `MemoryRouter` with route definitions in `test-utils` — read the source first.

- [ ] **Step 5: Write `ProjectSelector.test.tsx`**

```typescript
import { describe, it, expect } from "vitest";
import { waitFor, screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { ProjectSelector } from "./ProjectSelector";

describe("ProjectSelector", () => {
  it("shows project list after loading", async () => {
    renderWithProviders(<ProjectSelector />);
    await waitFor(() => {
      expect(screen.getByText(/Test Project/)).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 6: Run layout tests**

```bash
cd frontend
npx vitest run src/components/layout/
```

Fix any failing tests by adapting assertions to the actual component structure.

- [ ] **Step 7: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/src/components/layout/
git commit -m "test(frontend): add layout component tests"
```

---

## Task A7: Feature component tests

**Files:**
- Create: `frontend/src/components/chat/ChatInput.test.tsx`
- Create: `frontend/src/components/chat/MessageBubble.test.tsx`
- Create: `frontend/src/components/chat/ChatView.test.tsx`
- Create: `frontend/src/components/documents/DocumentCard.test.tsx`
- Create: `frontend/src/components/documents/UploadDropzone.test.tsx`
- Create: `frontend/src/components/contradictions/ContradictionCard.test.tsx`
- Create: `frontend/src/components/synthesis/OutlineEditor.test.tsx`
- Create: `frontend/src/components/synthesis/SynthesisViewer.test.tsx`

**Pattern:** Read each component first, then write tests covering: rendering with happy-path props, user interaction (click, type, submit), and at least one edge case (empty state, error state, or loading state).

- [ ] **Step 1: Read each component file**

```bash
cat frontend/src/components/chat/ChatInput.tsx
cat frontend/src/components/chat/MessageBubble.tsx
cat frontend/src/components/chat/ChatView.tsx
cat frontend/src/components/documents/DocumentCard.tsx
cat frontend/src/components/documents/UploadDropzone.tsx
cat frontend/src/components/contradictions/ContradictionCard.tsx
cat frontend/src/components/synthesis/OutlineEditor.tsx
cat frontend/src/components/synthesis/SynthesisViewer.tsx
```

- [ ] **Step 2: Write `ChatInput.test.tsx`**

Template (adapt to real props):

```typescript
import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { ChatInput } from "./ChatInput";

describe("ChatInput", () => {
  it("calls onSubmit with typed text", async () => {
    const onSubmit = vi.fn();
    renderWithProviders(<ChatInput onSubmit={onSubmit} disabled={false} />);

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "hello world");
    await userEvent.keyboard("{Enter}");

    expect(onSubmit).toHaveBeenCalledWith("hello world");
  });

  it("does not submit when disabled", async () => {
    const onSubmit = vi.fn();
    renderWithProviders(<ChatInput onSubmit={onSubmit} disabled={true} />);
    const input = screen.getByRole("textbox");
    await userEvent.type(input, "hi{Enter}");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("does not submit empty input", async () => {
    const onSubmit = vi.fn();
    renderWithProviders(<ChatInput onSubmit={onSubmit} disabled={false} />);
    await userEvent.keyboard("{Enter}");
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 3: Write `MessageBubble.test.tsx`**

```typescript
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { MessageBubble } from "./MessageBubble";

describe("MessageBubble", () => {
  it("renders user message text", () => {
    renderWithProviders(
      <MessageBubble role="user" content="Hello there" />,
    );
    expect(screen.getByText("Hello there")).toBeInTheDocument();
  });

  it("renders assistant message with markdown", () => {
    renderWithProviders(
      <MessageBubble role="assistant" content="**bold** text" />,
    );
    // react-markdown renders bold as <strong>
    expect(screen.getByText("bold").tagName).toBe("STRONG");
  });

  it("shows citations when provided", () => {
    renderWithProviders(
      <MessageBubble
        role="assistant"
        content="An answer"
        citations={[{ title: "Source Doc", relevance_score: 0.9 }]}
      />,
    );
    expect(screen.getByText(/Source Doc/)).toBeInTheDocument();
  });
});
```

If the component prop shape differs, adjust to match.

- [ ] **Step 4: Write `ChatView.test.tsx`**

```typescript
import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { ChatView } from "./ChatView";

describe("ChatView", () => {
  it("renders an empty state initially", () => {
    renderWithProviders(<ChatView projectId="proj-1" />);
    // Adapt: assert on whatever the empty state shows
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("displays answer after submitting a question", async () => {
    renderWithProviders(<ChatView projectId="proj-1" />);
    const input = screen.getByRole("textbox");
    await userEvent.type(input, "who is Alice?");
    await userEvent.keyboard("{Enter}");

    await waitFor(() => {
      expect(screen.getByText("An answer.")).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 5: Write `DocumentCard.test.tsx`**

```typescript
import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { DocumentCard } from "./DocumentCard";
import type { Document } from "@/lib/api";

const doc: Document = {
  id: "doc-1",
  title: "Test Doc",
  status: "completed",
  chunk_count: 10,
  file_path: "/data/test.md",
  created_at: "2026-01-01T00:00:00Z",
};

describe("DocumentCard", () => {
  it("shows the document title and chunk count", () => {
    renderWithProviders(<DocumentCard document={doc} onDelete={vi.fn()} />);
    expect(screen.getByText("Test Doc")).toBeInTheDocument();
    expect(screen.getByText(/10/)).toBeInTheDocument();
  });

  it("triggers delete on delete button click", async () => {
    const onDelete = vi.fn();
    renderWithProviders(<DocumentCard document={doc} onDelete={onDelete} />);
    const deleteBtn = screen.getByRole("button", { name: /delete/i });
    await userEvent.click(deleteBtn);
    // If there's a confirmation dialog, advance through it first:
    // const confirm = await screen.findByRole("button", { name: /confirm|yes/i });
    // await userEvent.click(confirm);
    expect(onDelete).toHaveBeenCalledWith("doc-1");
  });

  it("shows error status when document failed", () => {
    renderWithProviders(
      <DocumentCard
        document={{ ...doc, status: "failed", error_message: "bad file" }}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText(/failed|bad file/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: Write `UploadDropzone.test.tsx`**

```typescript
import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { UploadDropzone } from "./UploadDropzone";

describe("UploadDropzone", () => {
  it("renders drop zone label", () => {
    renderWithProviders(<UploadDropzone onUpload={vi.fn()} />);
    expect(
      screen.getByText(/drop|drag|upload/i),
    ).toBeInTheDocument();
  });

  it("calls onUpload when a file is selected via input", async () => {
    const onUpload = vi.fn();
    renderWithProviders(<UploadDropzone onUpload={onUpload} />);
    const file = new File(["content"], "test.md", { type: "text/markdown" });
    const input = screen.getByLabelText(/upload|file/i, { selector: "input[type='file']" });
    await userEvent.upload(input, file);
    expect(onUpload).toHaveBeenCalledWith(file);
  });
});
```

- [ ] **Step 7: Write remaining feature component tests**

For `ContradictionCard`, `OutlineEditor`, `SynthesisViewer`: follow the same pattern:
1. Read the component source
2. Render with minimal realistic props
3. Assert on visible content
4. Test one interaction (click, edit, submit)
5. Test one state variation (error/loading/empty)

Each test file should have at least 3 test cases.

- [ ] **Step 8: Run feature component tests**

```bash
cd frontend
npx vitest run src/components/chat/ src/components/documents/ src/components/contradictions/ src/components/synthesis/
```

Fix failing assertions to match actual component structure.

- [ ] **Step 9: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/src/components/chat/ frontend/src/components/documents/ frontend/src/components/contradictions/ frontend/src/components/synthesis/
git commit -m "test(frontend): add feature component tests"
```

---

## Task A8: Page integration tests

**Files:**
- Create: `frontend/src/pages/ChatPage.test.tsx`
- Create: `frontend/src/pages/DocumentsPage.test.tsx`
- Create: `frontend/src/pages/ProjectsPage.test.tsx`
- Create: `frontend/src/pages/SettingsPage.test.tsx`
- Create: `frontend/src/pages/ContradictionsPage.test.tsx`
- Create: `frontend/src/pages/SynthesisPage.test.tsx`

**Context:** Page-level tests are integration-style — they render the full page with providers and MSW-mocked API, then assert on rendered output and user flows.

- [ ] **Step 1: Read each page**

```bash
cat frontend/src/pages/ChatPage.tsx
cat frontend/src/pages/DocumentsPage.tsx
cat frontend/src/pages/ProjectsPage.tsx
cat frontend/src/pages/SettingsPage.tsx
cat frontend/src/pages/ContradictionsPage.tsx
cat frontend/src/pages/SynthesisPage.tsx
```

Note: any route params (`useParams`), any context dependencies (`ProjectContext`).

- [ ] **Step 2: Check ProjectContext usage**

```bash
cat frontend/src/contexts/ProjectContext.tsx
```

If pages depend on `ProjectContext`, extend `test-utils.tsx` to include a `ProjectProvider` wrapper. Add this step to `test-utils.tsx` only if needed:

```typescript
// In test-utils.tsx, if ProjectContext is required:
import { ProjectProvider } from "@/contexts/ProjectContext";

function AllProviders({ children, initialRoute = "/" }: WrapperProps) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>
        <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
      </ProjectProvider>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 3: Write `DocumentsPage.test.tsx`**

```typescript
import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { renderWithProviders } from "@/test/test-utils";
import { DocumentsPage } from "./DocumentsPage";

describe("DocumentsPage", () => {
  it("loads and shows documents", async () => {
    renderWithProviders(<DocumentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Document")).toBeInTheDocument();
    });
  });

  it("shows empty state when no documents", async () => {
    server.use(
      http.get("/api/v1/projects/:pid/documents", () => HttpResponse.json([])),
    );
    renderWithProviders(<DocumentsPage />);
    await waitFor(() => {
      // Adapt to the empty-state text used in the component
      expect(screen.getByText(/no documents|upload/i)).toBeInTheDocument();
    });
  });
});
```

If `DocumentsPage` depends on a route param for project ID, use `initialRoute="/projects/proj-1/documents"` or similar — read the page first to confirm.

- [ ] **Step 4: Write the other page tests**

Apply the same pattern to the remaining pages. Each page test file should include:
1. A "happy path" load-and-render test
2. An empty or error state test

- [ ] **Step 5: Run page tests**

```bash
cd frontend
npx vitest run src/pages/
```

- [ ] **Step 6: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/src/pages/ frontend/src/test/test-utils.tsx
git commit -m "test(frontend): add page-level integration tests"
```

---

## Task A9: Run full test suite with coverage and verify thresholds

- [ ] **Step 1: Run the full suite with coverage**

```bash
cd frontend
npm run test:coverage
```

Expected:
- All tests pass
- Coverage report appears at the end
- Global thresholds (lines ≥70%, branches ≥65%) are met

- [ ] **Step 2: If coverage is below threshold, add targeted tests**

Look at the coverage report for files < 70%. Options:
1. Add tests for uncovered branches (preferred)
2. If a file is pure glue/main-entry code with no logic to test, add it to the `exclude` list in `vitest.config.ts`

**Do not** lower the thresholds — the whole point of this task is to enforce meaningful coverage.

- [ ] **Step 3: Verify in watch mode that tests re-run on file changes**

```bash
cd frontend
npx vitest --run=false
# Modify a test file in another terminal, save, observe re-run
# Press q to quit
```

- [ ] **Step 4: Commit any additional tests**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/
git commit -m "test(frontend): achieve ≥70% line coverage"
```

(If no changes were needed, skip this commit.)

---

## Task A10: Add typecheck script and verify

**Context:** CI will run `npm run typecheck` — make sure it's in place and passes.

- [ ] **Step 1: Verify typecheck script exists**

Open `frontend/package.json`. Confirm the `scripts` section contains:

```json
"typecheck": "tsc -b --noEmit"
```

If missing, add it (preserve all other scripts).

- [ ] **Step 2: Run typecheck**

```bash
cd frontend
npm run typecheck
```

Expected: exit code 0.

- [ ] **Step 3: Run lint**

```bash
cd frontend
npm run lint
```

Expected: exit code 0. Fix any new lint errors introduced by the test files (e.g., add `// eslint-disable-next-line` only as a last resort; prefer fixing the underlying issue).

- [ ] **Step 4: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/package.json
git commit -m "chore(frontend): ensure typecheck script is present" --allow-empty
```

(Use `--allow-empty` because the script may have already been added in Task A1; this task just verifies.)

---

# Workstream B: CI/CD

**Owner:** Agent B
**Files owned:** `.github/workflows/**`, `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md`
**No concurrent edits.** This workstream's files don't overlap with A or C.

## Task B1: Remove outdated workflow

**Files:**
- Delete: `.github/workflows/test.yml`

- [ ] **Step 1: Delete the old workflow**

The existing `.github/workflows/test.yml` uses `pip install -r backend/requirements.txt`, but the project uses UV with `pyproject.toml`. It also has no frontend steps. Delete it.

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
rm .github/workflows/test.yml
```

- [ ] **Step 2: Commit the deletion**

```bash
git add .github/workflows/test.yml
git commit -m "ci: remove outdated pip-based workflow (replaced in subsequent commits)"
```

---

## Task B2: Backend CI workflow

**Files:**
- Create: `.github/workflows/backend.yml`

- [ ] **Step 1: Create the backend workflow**

Create `.github/workflows/backend.yml`:

```yaml
name: Backend

on:
  workflow_call:
  push:
    branches: [main]
    paths:
      - "backend/**"
      - ".github/workflows/backend.yml"
  pull_request:
    paths:
      - "backend/**"
      - ".github/workflows/backend.yml"

jobs:
  test:
    name: Backend tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
          cache-dependency-glob: "backend/uv.lock"

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-groups

      - name: Run tests (non-integration)
        run: uv run pytest tests/ -v -m "not integration"

      - name: Run tests with coverage
        if: matrix.python-version == '3.11'
        run: uv run pytest tests/ -m "not integration" --cov=app --cov-report=xml --cov-report=term

      - name: Upload coverage
        if: matrix.python-version == '3.11'
        uses: actions/upload-artifact@v4
        with:
          name: backend-coverage
          path: backend/coverage.xml
          retention-days: 7
```

- [ ] **Step 2: Validate the YAML syntax**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
# If yamllint or similar is available:
python -c "import yaml; yaml.safe_load(open('.github/workflows/backend.yml'))"
```

Expected: No error.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/backend.yml
git commit -m "ci: add backend workflow (UV + pytest matrix)"
```

---

## Task B3: Frontend CI workflow

**Files:**
- Create: `.github/workflows/frontend.yml`

- [ ] **Step 1: Create the frontend workflow**

Create `.github/workflows/frontend.yml`:

```yaml
name: Frontend

on:
  workflow_call:
  push:
    branches: [main]
    paths:
      - "frontend/**"
      - ".github/workflows/frontend.yml"
  pull_request:
    paths:
      - "frontend/**"
      - ".github/workflows/frontend.yml"

jobs:
  build-and-test:
    name: Build, lint, typecheck, test
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run typecheck

      - name: Run tests with coverage
        run: npm run test:coverage

      - name: Build
        run: npm run build

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: frontend-coverage
          path: frontend/coverage/
          retention-days: 7
```

- [ ] **Step 2: Validate YAML**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/frontend.yml'))"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/frontend.yml
git commit -m "ci: add frontend workflow (lint, typecheck, test, build)"
```

---

## Task B4: Docker CI workflow

**Files:**
- Create: `.github/workflows/docker.yml`

- [ ] **Step 1: Create the Docker workflow**

Create `.github/workflows/docker.yml`:

```yaml
name: Docker

on:
  workflow_call:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    paths:
      - "Dockerfile"
      - "docker-compose.yml"
      - ".dockerignore"
      - ".github/workflows/docker.yml"

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    name: Build Docker image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        if: github.event_name == 'push'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name == 'push' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

- [ ] **Step 2: Validate YAML**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/docker.yml'))"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/docker.yml
git commit -m "ci: add Docker build workflow with GHCR publishing"
```

---

## Task B5: Umbrella CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the umbrella workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend:
    name: Backend
    uses: ./.github/workflows/backend.yml

  frontend:
    name: Frontend
    uses: ./.github/workflows/frontend.yml

  docker:
    name: Docker
    uses: ./.github/workflows/docker.yml
    permissions:
      contents: read
      packages: write
```

- [ ] **Step 2: Validate YAML**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add umbrella workflow for PR status checks"
```

---

## Task B6: Issue and PR templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 1: Create bug report template**

Create `.github/ISSUE_TEMPLATE/bug_report.yml`:

```yaml
name: Bug report
description: Report a bug in WorldForge
title: "[Bug]: "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report a bug! The more detail you provide, the faster we can help.
  - type: textarea
    id: description
    attributes:
      label: What happened?
      description: A clear description of the bug.
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Steps to reproduce
      description: How can we reproduce the bug?
      placeholder: |
        1. Start WorldForge with `docker compose up -d`
        2. Upload a file via ...
        3. Observe ...
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual behavior
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: WorldForge version
      description: Git SHA, tag, or "main"
    validations:
      required: true
  - type: dropdown
    id: os
    attributes:
      label: Operating system
      options:
        - Linux
        - macOS
        - Windows
        - Other
    validations:
      required: true
  - type: input
    id: docker-version
    attributes:
      label: Docker version
      description: Output of `docker --version`
  - type: textarea
    id: logs
    attributes:
      label: Relevant logs
      description: API logs, browser console, etc. Use fenced code blocks.
      render: shell
```

- [ ] **Step 2: Create feature request template**

Create `.github/ISSUE_TEMPLATE/feature_request.yml`:

```yaml
name: Feature request
description: Suggest a new feature or enhancement
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting an improvement! Before filing, please check the [roadmap](../blob/main/docs/ROADMAP.md) — your idea may already be planned.
  - type: textarea
    id: problem
    attributes:
      label: What problem does this solve?
      description: Describe the user problem, not the solution yet.
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
  - type: dropdown
    id: phase
    attributes:
      label: Roadmap phase (if known)
      options:
        - "Not sure"
        - "Phase 2 — Knowledge graph"
        - "Phase 3 — Proposals & consistency"
        - "Phase 4 — Multi-user & auth"
        - "Phase 5 — Advanced features"
```

- [ ] **Step 3: Create issue config**

Create `.github/ISSUE_TEMPLATE/config.yml`:

```yaml
blank_issues_enabled: false
contact_links:
  - name: Questions and discussion
    url: https://github.com/adbarc92/worldforge/discussions
    about: Ask questions or discuss ideas before filing an issue
```

**Note:** If GitHub Discussions is not enabled for the repo, this link will 404. Either enable Discussions manually in GitHub settings or change this entry to point to Issues. This is flagged in the spec's Open Questions section.

- [ ] **Step 4: Create PR template**

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Summary

<!-- What does this PR change? Why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation
- [ ] CI / build
- [ ] Other:

## How was this tested?

<!-- Describe the tests you ran. Include commands and results. -->

## Screenshots (UI changes only)

<!-- Attach before/after screenshots if the UI changed. -->

## Linked issue

<!-- Closes #123 -->

## Checklist

- [ ] Tests pass locally (`uv run pytest` and `npm run test`)
- [ ] Lint passes (`uv run ruff check` and `npm run lint`)
- [ ] Type check passes (`npm run typecheck`)
- [ ] I've added tests for new behavior
- [ ] I've updated documentation where needed
- [ ] The PR is focused on a single change
```

- [ ] **Step 5: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add .github/ISSUE_TEMPLATE/ .github/PULL_REQUEST_TEMPLATE.md
git commit -m "ci: add issue and PR templates"
```

---

# Workstream C: Docs & Metadata

**Owner:** Agent C
**Files owned:** `CONTRIBUTING.md`, `README.md`, `frontend/package.json` (top-level metadata only — NOT scripts or devDependencies), `backend/pyproject.toml`, `config/config.dev.yaml`, `.gitignore`, git-add for untracked docs and scripts.
**Concurrent edits:** Agent A may also edit `frontend/package.json` (scripts + devDependencies). Agent C must re-read the file before each edit and preserve any changes from Agent A.

## Task C1: Update frontend package.json metadata

**Files:**
- Modify: `frontend/package.json` (top-level fields only)

- [ ] **Step 1: Read the current package.json**

```bash
cat frontend/package.json
```

Note whatever is currently in `scripts` and `devDependencies` — preserve those exactly.

- [ ] **Step 2: Update top-level fields**

Replace the top-level fields so the file becomes:

```json
{
  "name": "worldforge-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "description": "React frontend for WorldForge, a RAG-powered worldbuilding knowledge system",
  "repository": {
    "type": "git",
    "url": "https://github.com/adbarc92/worldforge.git",
    "directory": "frontend"
  },
  "license": "MIT",
  "author": "Alex Barclay",
  "scripts": { ... existing scripts ... },
  "dependencies": { ... existing dependencies ... },
  "devDependencies": { ... existing devDependencies ... }
}
```

**Do not** touch the `scripts`, `dependencies`, or `devDependencies` objects — copy them verbatim from the previous read.

- [ ] **Step 3: Verify the JSON is valid**

```bash
cd frontend
node -e "JSON.parse(require('fs').readFileSync('package.json', 'utf8')); console.log('OK');"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add frontend/package.json
git commit -m "chore(frontend): add open-source metadata to package.json"
```

---

## Task C2: Update backend pyproject.toml metadata

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Update the `[project]` table**

Open `backend/pyproject.toml`. The current `[project]` table starts:

```toml
[project]
name = "canon-builder"
version = "0.1.0"
description = "RAG-powered worldbuilding knowledge system"
requires-python = ">=3.11"
dependencies = [ ... ]
```

Update it to:

```toml
[project]
name = "canon-builder"
version = "1.0.0"
description = "RAG-powered worldbuilding knowledge system"
requires-python = ">=3.11"
authors = [{ name = "Alex Barclay" }]
license = { text = "MIT" }
readme = "../README.md"
keywords = ["rag", "worldbuilding", "llm", "fastapi", "qdrant"]
dependencies = [ ... (unchanged) ... ]

[project.urls]
Repository = "https://github.com/adbarc92/worldforge"
Issues = "https://github.com/adbarc92/worldforge/issues"
```

Preserve the `dependencies` list and `[dependency-groups]` section exactly as they are.

- [ ] **Step 2: Validate TOML**

```bash
cd backend
uv run python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Verify UV can still parse and sync**

```bash
cd backend
uv sync --all-groups
```

Expected: Completes without errors.

- [ ] **Step 4: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore(backend): add open-source metadata and bump to 1.0.0"
```

---

## Task C3: Update config.dev.yaml model reference

**Files:**
- Modify: `config/config.dev.yaml`

- [ ] **Step 1: Update the Claude model**

Open `config/config.dev.yaml`. Find:

```yaml
  claude:
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 4096
    temperature: 0.0
```

Replace with:

```yaml
  claude:
    model: "claude-sonnet-4-20250514"
    max_tokens: 4096
    temperature: 0.0
```

- [ ] **Step 2: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add config/config.dev.yaml
git commit -m "chore(config): update dev config to current Claude Sonnet model"
```

---

## Task C4: Update .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Check current state of .gitignore**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
cat .gitignore
```

Note: the file already has `test-docs*` (staged), and `.env` is already excluded. The existing `.gitignore` may have `.claude/` — verify.

- [ ] **Step 2: Add exclusions for internal artifacts**

Append to the bottom of `.gitignore` (if not already present):

```
# Local Claude Code settings
.claude/

# Internal launch material (not part of the public repo)
docs/LAUNCH_TWEETS.md
```

If `.claude/` is already excluded, only add the `docs/LAUNCH_TWEETS.md` line. Check first with `grep`:

```bash
grep -E "^\.claude" .gitignore
grep "LAUNCH_TWEETS" .gitignore
```

- [ ] **Step 3: Verify the files are now ignored**

```bash
git status --ignored | grep -E "LAUNCH_TWEETS|\.claude"
```

Expected: Both appear under "Ignored files" (or not in the untracked list at all).

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: exclude .claude/ and launch-tweets from public repo"
```

---

## Task C5: Write CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Create the contributing guide**

Create `CONTRIBUTING.md`:

````markdown
# Contributing to WorldForge

Thanks for your interest in contributing to WorldForge! This is a RAG-powered worldbuilding knowledge system built as a single-user personal tool that grew into something worth sharing. Contributions of all kinds are welcome — bug reports, feature suggestions, documentation improvements, and code.

See [README.md](README.md) for a project overview and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design details.

## Code of conduct

Be kind. Assume good faith. Focus on the work. If someone is making WorldForge better — even if you disagree with how — remember there's a human on the other side. Personal attacks, harassment, or dismissive behavior are not welcome. Maintainers may moderate or remove contributions that violate this spirit.

## Development setup

### Prerequisites

- **Docker Desktop** (or Docker Engine + Compose v2)
- **[UV](https://docs.astral.sh/uv/)** for Python package management
- **Node.js 20+** and npm
- An Anthropic API key and an OpenAI API key (for Claude generation and embeddings)

### Clone and install

```bash
git clone https://github.com/adbarc92/worldforge.git
cd worldforge

# Backend dependencies
cd backend && uv sync --all-groups && cd ..

# Frontend dependencies
cd frontend && npm install && cd ..

# Environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and OPENAI_API_KEY
```

### Run with Docker (recommended)

```bash
docker compose up -d --build
```

- API + frontend: http://localhost:8080
- OpenWebUI: http://localhost:3000
- Qdrant: http://localhost:6333
- PostgreSQL: port 5432

### Run without Docker (development)

Two terminals:

```bash
# Terminal 1 — backend
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8080
```

```bash
# Terminal 2 — frontend with hot reload
cd frontend
npm run dev
# Vite proxies /api, /v1, /health to localhost:8080
```

Frontend dev server runs on http://localhost:5173.

### Apply database migrations

```bash
cd backend
uv run alembic upgrade head
```

### Seed test data

WorldForge includes a bulk-upload script for loading existing `.md`, `.txt`, or `.pdf` files into a project:

```bash
cd scripts
uv run python bulk_upload.py <path-to-folder> --project "My Project"
```

## Project structure

```
backend/          # FastAPI + SQLAlchemy async, Qdrant, Anthropic/OpenAI SDKs
  app/
    api/v1/       # Route handlers
    models/       # SQLAlchemy + Pydantic schemas
    services/     # Business logic (LLM, ingestion, RAG, synthesis)
    core/         # Config
  tests/          # pytest (unit + integration)

frontend/         # React 19 + Vite + TanStack Query + Tailwind v4 + shadcn/ui
  src/
    components/   # UI by feature (chat, documents, contradictions, synthesis, layout)
    hooks/        # React Query hooks (one per resource)
    lib/          # API client
    pages/        # Route-level components
    test/         # Vitest setup, MSW handlers, test utilities

docs/             # Architecture, roadmap, design specs
scripts/          # Utility scripts (bulk upload, etc.)
.github/workflows/# CI pipelines
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture walkthrough.

## Running tests

### Backend

```bash
cd backend
uv run pytest tests/ -v              # all tests
uv run pytest tests/ -v -m "not integration"  # skip integration
uv run pytest tests/test_basic.py -v  # single file
```

### Frontend

```bash
cd frontend
npm run test              # run once
npm run test:watch        # watch mode
npm run test:coverage     # with coverage report
npm run test:ui           # Vitest UI
```

## Code style

### Python (backend)

- **Ruff** for linting and formatting (`uv run ruff check backend/` / `uv run ruff format backend/`)
- Type hints everywhere (Pydantic models for API, SQLAlchemy 2.0 typing for DB)
- Async-first — database, vector DB, and LLM calls are `async def`

### TypeScript (frontend)

- **ESLint** (`npm run lint`)
- **tsc --noEmit** for type checking (`npm run typecheck`)
- Strict mode enabled
- Follow existing patterns: one hook per resource, colocated tests, shadcn/ui for primitives

### Commit messages

Use conventional prefixes:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — tests only
- `chore:` — tooling, deps, config
- `refactor:` — code change that's not a fix or feature
- `ci:` — CI/CD changes

Keep commits focused — one logical change per commit. We use squash merges on PRs, but clean individual commits make review easier.

## PR workflow

1. **Fork** the repository and clone your fork
2. **Create a branch**: `git checkout -b feat/your-feature` or `fix/bug-name`
3. **Make changes** — keep PRs focused on one thing
4. **Run the test suite** locally (`uv run pytest` + `npm run test`)
5. **Run lint and typecheck** (`uv run ruff check backend/` + `npm run lint` + `npm run typecheck`)
6. **Commit** with a clear message (see conventions above)
7. **Push** to your fork and **open a PR** against `main`
8. **Link the issue** the PR addresses (if any)
9. Wait for **CI** to pass — all checks must be green before review
10. Respond to review feedback — don't force-push; add new commits so reviewers can see what changed

### Branch protection (maintainer reference)

The `main` branch is protected:

- Requires the `ci` check to pass
- No direct pushes — merge via PR
- Squash merge is the default

## What we're looking for

**Great first contributions:**

- Bug fixes with reproduction steps and a failing test
- Documentation improvements (typos, clearer explanations, missing sections)
- Frontend tests for components that aren't yet covered
- Backend tests for edge cases

**High-value areas:**

- Better PDF parsing and extraction
- Additional LLM providers (local, Ollama, etc.)
- Alternative embedding models
- Performance improvements to ingestion/query

**Check the roadmap:** [docs/ROADMAP.md](docs/ROADMAP.md) — Phase 2 (knowledge graph) and Phase 3 (proposals & consistency) are where most feature work is happening.

## What not to work on without discussion

Please open an issue or discussion first if you're thinking about:

- **Authentication / multi-user support** — this is Phase 4 work with significant scope. We want to plan it carefully.
- **Major architectural changes** — replacing a core dependency (Qdrant, FastAPI, React Query), restructuring the service layer, etc.
- **New pages or top-level features** — talk through the shape first so the PR doesn't land in surprising territory.

## Questions?

- [GitHub Discussions](https://github.com/adbarc92/worldforge/discussions) — questions, ideas, show-and-tell
- [GitHub Issues](https://github.com/adbarc92/worldforge/issues) — bugs and concrete feature requests

Thanks for contributing!
````

- [ ] **Step 2: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md"
```

---

## Task C6: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current README**

```bash
cat README.md
```

- [ ] **Step 2: Add CI status badge at top**

Find the first heading (`# Canon Builder`). Immediately after the heading and the first description paragraphs, add a line with the CI badge:

```markdown
[![CI](https://github.com/adbarc92/worldforge/actions/workflows/ci.yml/badge.svg)](https://github.com/adbarc92/worldforge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

- [ ] **Step 3: Add "Bulk upload" section**

Find a natural spot after the Quick Start and before Development. Add:

```markdown
## Bulk upload

WorldForge includes a helper script for loading an existing folder of `.md`, `.txt`, or `.pdf` files into a project:

```bash
cd scripts
uv run python bulk_upload.py ./path/to/folder --project "My Worldbuilding Project"
```

The script creates the project if it doesn't exist and uploads every supported file it finds.
```

- [ ] **Step 4: Add "Contributing" section**

Near the bottom, before the License section, add:

```markdown
## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to set up a development environment, run tests, and submit pull requests.
```

- [ ] **Step 5: Verify README renders correctly**

Scan the file for any broken markdown (unbalanced backticks, broken tables).

- [ ] **Step 6: Commit**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add README.md
git commit -m "docs: add CI badge, bulk-upload usage, and contributing section"
```

---

## Task C7: Commit untracked docs and scripts

**Files:**
- git-add: `docs/ARCHITECTURE.md`
- git-add: `docs/superpowers/plans/2026-04-04-contradiction-detection.md`
- git-add: `docs/superpowers/plans/2026-04-05-world-synthesis.md`
- git-add: `docs/superpowers/specs/2026-04-04-contradiction-detection-design.md`
- git-add: `docs/superpowers/specs/2026-04-05-world-synthesis-design.md`
- git-add: `scripts/bulk_upload.py`

**Note:** `docs/superpowers/specs/2026-04-10-open-source-polish-design.md` and this plan file are already committed.

- [ ] **Step 1: Verify files exist**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
ls docs/ARCHITECTURE.md
ls docs/superpowers/plans/
ls docs/superpowers/specs/
ls scripts/bulk_upload.py
```

- [ ] **Step 2: Add ARCHITECTURE.md**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs: add comprehensive architecture guide"
```

- [ ] **Step 3: Add design specs and plans**

```bash
git add docs/superpowers/plans/2026-04-04-contradiction-detection.md
git add docs/superpowers/plans/2026-04-05-world-synthesis.md
git add docs/superpowers/specs/2026-04-04-contradiction-detection-design.md
git add docs/superpowers/specs/2026-04-05-world-synthesis-design.md
git commit -m "docs: commit contradiction detection and world synthesis design docs"
```

- [ ] **Step 4: Add bulk_upload script**

```bash
git add scripts/bulk_upload.py
git commit -m "feat: add bulk_upload helper script"
```

- [ ] **Step 5: Verify no relevant untracked files remain**

```bash
git status
```

Expected: `.claude/` and `docs/LAUNCH_TWEETS.md` remain ignored (per Task C4). No other untracked files from the original polish scope.

---

## Task C8: Verify backend lint is clean

**Context:** CI will run `ruff check backend/`. If the existing code has ruff errors, CI will fail on first push. Preemptively check.

- [ ] **Step 1: Run ruff**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
cd backend
uv run ruff check app/ 2>&1 | head -50
```

- [ ] **Step 2: Decide based on result**

If ruff finds errors:
- **Autofix-safe issues** (unused imports, simple formatting): run `uv run ruff check app/ --fix`
- **Non-autofixable errors**: fix manually
- **If there's a large volume of errors**: report back — this becomes a blocker that needs user decision, don't silently mass-fix

If ruff is clean: skip to Step 4.

- [ ] **Step 3: Commit fixes (if any)**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git add backend/app/
git commit -m "chore(backend): fix ruff lint errors"
```

- [ ] **Step 4: Confirm typecheck also passes if mypy is configured**

```bash
cd backend
uv run mypy app/ --ignore-missing-imports 2>&1 | tail -20
```

If mypy finds errors: note them but don't block — CI workflow only runs pytest, not mypy. Report findings in the final status so Agent D knows.

---

# Workstream D: Integration & Release

**Runs sequentially after Workstreams A, B, and C all complete.**

**Owner:** Orchestrator (not a subagent — the main session handles these steps with direct user checkpoints since they involve destructive/irreversible actions like merging and tagging).

## Task D1: Local verification

- [ ] **Step 1: Backend tests**

```bash
cd "D:\MajorProjects\CURRENT\worldforge\backend"
uv run pytest tests/ -v -m "not integration"
```

Expected: All tests pass.

- [ ] **Step 2: Frontend tests with coverage**

```bash
cd "D:\MajorProjects\CURRENT\worldforge\frontend"
npm run test:coverage
```

Expected: All tests pass; coverage meets thresholds (≥70% lines, ≥65% branches).

- [ ] **Step 3: Frontend typecheck**

```bash
npm run typecheck
```

Expected: exit code 0.

- [ ] **Step 4: Frontend lint**

```bash
npm run lint
```

Expected: exit code 0.

- [ ] **Step 5: Frontend build**

```bash
npm run build
```

Expected: build succeeds, `dist/` directory created.

- [ ] **Step 6: Docker build**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
docker compose build
```

Expected: image builds cleanly.

- [ ] **Step 7: If anything fails, STOP**

Report failures to user. Do not proceed to push until all verifications pass.

---

## Task D2: Push feature branch and verify CI

- [ ] **Step 1: Confirm on the right branch with clean state**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git status
git branch --show-current
```

Expected: branch is `feat/multiple-projects`, working tree clean.

- [ ] **Step 2: Push to origin**

```bash
git push origin feat/multiple-projects
```

This triggers the new CI workflows for the first time in GitHub Actions.

- [ ] **Step 3: Watch CI**

```bash
gh run watch
```

Or navigate to `https://github.com/adbarc92/worldforge/actions` in a browser.

- [ ] **Step 4: If CI fails, iterate**

Common first-push failures:
- Workflow YAML syntax error → fix file, commit, push
- Path filter not matching → adjust `paths:` in the workflow file
- GHCR permission error → check `permissions: packages: write` is set on the `docker` job
- Tests that pass locally but fail in CI → investigate (often env var differences)

Fix, commit (`ci: fix <specific issue>`), push, re-watch. Repeat until green.

- [ ] **Step 5: STOP and report status**

Once CI is green, report to user: "CI passing on `feat/multiple-projects`. Ready to open PR to main. Proceed?"

**Wait for user confirmation before continuing.**

---

## Task D3: Open PR to main

- [ ] **Step 1: Generate diff summary**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git log main..HEAD --oneline
git diff main...HEAD --stat
```

Review the output. It should show ~45+ commits and a wide file change set.

- [ ] **Step 2: Create the PR**

```bash
gh pr create --base main --head feat/multiple-projects --title "feat: multi-project support, contradiction detection, synthesis, open-source polish" --body "$(cat <<'EOF'
## Summary

This PR rolls up all work on `feat/multiple-projects` and polishes WorldForge for public open-source release.

### Major features

- **Multi-project support** — documents are scoped to projects; project selector in sidebar; per-project document/contradiction/synthesis views
- **Contradiction detection** — scan a project's canon for contradictions between chunks, review them grouped by document pair, resolve or dismiss individually or in bulk
- **World synthesis** — generate outlines and long-form synthesis from a project's canon with approval gates and retry support
- **Per-section logging** and retry endpoint for stuck syntheses

### Open-source polish pass

- **Frontend test suite** (Vitest + React Testing Library + MSW) — ≥70% line coverage, covering API client, hooks, components, and pages
- **CI/CD pipelines** — `backend.yml` (UV + pytest matrix), `frontend.yml` (lint/typecheck/test/build), `docker.yml` (GHCR publishing), `ci.yml` umbrella
- **Contributor infrastructure** — `CONTRIBUTING.md`, issue templates (bug report, feature request), PR template
- **Metadata cleanup** — frontend `package.json` and backend `pyproject.toml` filled out with proper fields
- **Documentation** — committed `docs/ARCHITECTURE.md`, design specs for contradiction detection and world synthesis

## Test plan

- [x] Backend tests pass (`uv run pytest tests/ -v -m "not integration"`)
- [x] Frontend tests pass with coverage (`npm run test:coverage`)
- [x] Frontend typecheck clean (`npm run typecheck`)
- [x] Frontend lint clean (`npm run lint`)
- [x] Frontend production build succeeds (`npm run build`)
- [x] Docker image builds (`docker compose build`)
- [x] CI workflows pass on GitHub Actions

## Merge strategy

Squash merge. After merge, tag `v1.0.0` as the initial open-source release.
EOF
)"
```

- [ ] **Step 3: Wait for PR CI to go green**

```bash
gh pr checks --watch
```

- [ ] **Step 4: STOP and report**

Report to user: "PR opened at <url>. CI passing. Ready to squash merge. Proceed?"

**Wait for user confirmation.**

---

## Task D4: Squash merge

- [ ] **Step 1: Squash merge via gh**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
gh pr merge --squash --delete-branch=false
```

Do NOT pass `--delete-branch=true` — let the user decide about the remote branch.

- [ ] **Step 2: Pull main locally**

```bash
git checkout main
git pull origin main
```

- [ ] **Step 3: Verify main is up to date**

```bash
git log --oneline -5
```

Expected: The top commit is the squash-merged PR.

---

## Task D5: Tag v1.0.0

- [ ] **Step 1: Create annotated tag**

```bash
git tag -a v1.0.0 -m "Initial open-source release

Features:
- Multi-project support
- Document upload and RAG queries with Claude
- Contradiction detection and resolution
- World synthesis with outline approval
- OpenWebUI integration
- Docker Compose deployment

This is the first public release of WorldForge (Canon Builder).
See CHANGELOG or commit history for details."
```

- [ ] **Step 2: STOP and ask user before pushing the tag**

The tag push triggers the `docker.yml` workflow, which will build and publish `ghcr.io/adbarc92/worldforge:v1.0.0`. Confirm with user before pushing.

Report: "v1.0.0 tag created locally. Pushing it will trigger the Docker build and GHCR publish. Proceed?"

**Wait for user confirmation.**

- [ ] **Step 3: Push the tag**

```bash
git push origin v1.0.0
```

- [ ] **Step 4: Watch the tag build**

```bash
gh run watch
```

Expected: `docker.yml` workflow builds and publishes to GHCR with tags `v1.0.0`, `1.0`, and `latest`.

---

## Task D6: Post-merge cleanup

- [ ] **Step 1: Delete local feature branch**

```bash
cd "D:\MajorProjects\CURRENT\worldforge"
git branch -d feat/multiple-projects
```

If git refuses (`not fully merged`), use `-D` only after confirming the squash merge contains all the work.

- [ ] **Step 2: Ask about remote branch**

Report to user: "Local feat/multiple-projects deleted. Should I also delete the remote branch on GitHub? (`git push origin --delete feat/multiple-projects`)"

**Do not delete the remote branch without explicit user confirmation.**

---

## Task D7: Final status report

- [ ] **Step 1: Summarize for user**

Report a final status:

```
Open-source polish pass complete.

- Merged feat/multiple-projects → main (squash)
- Tagged v1.0.0
- GHCR image published at ghcr.io/adbarc92/worldforge:v1.0.0
- CI workflows green: backend, frontend, docker, ci (umbrella)
- Frontend coverage: <X>% lines / <Y>% branches
- Untracked docs committed: ARCHITECTURE.md, design specs, bulk_upload.py
- CONTRIBUTING.md and issue/PR templates in place

Remaining user actions (not automated):
1. Rotate the API keys that may have been exposed locally (recommended before making repo heavily promoted)
2. Enable branch protection on main requiring the `ci` check
3. Enable GitHub Discussions (if you want the link in issue templates to work)
4. Optionally delete the remote feat/multiple-projects branch
5. Create a GitHub Release from the v1.0.0 tag (optional but nice)
6. Announce the launch (the LAUNCH_TWEETS.md draft is in your working dir but excluded from git)
```

Do not create a GitHub Release or announce the launch without explicit user direction.

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Frontend test suite (Section 1 of spec) → Tasks A1-A10
- ✅ CI/CD GitHub Actions (Section 2) → Tasks B1-B5
- ✅ Contributor infrastructure (Section 3) → Task B6, C5
- ✅ Metadata cleanup (Section 4) → Tasks C1, C2, C3, C4
- ✅ Documentation commits (Section 5) → Tasks C6, C7
- ✅ Integration & merge strategy (Section 6) → Tasks D1-D7
- ✅ Testing & error handling (Section 7) → Integration verification in D1, error-handling guidance throughout
- ✅ Agent coordination (Section 7) → Workstream ownership clearly defined, concurrent-edit warning on `frontend/package.json`

**Type/signature consistency:**
- `createTestQueryClient` defined in Task A3, used in A5, A6, A8 — consistent
- `renderWithProviders` defined in Task A3, used throughout
- `handlers` / `server` imports consistent
- Commit message prefixes consistent with the conventions in `CONTRIBUTING.md`
- `frontend/package.json` edits distributed between A1/A10 (scripts) and C1 (metadata) — explicit warnings in both agent prompts to preserve concurrent edits

**Known approximations:**
- Some component tests use pattern templates rather than exact assertions because the component source hasn't been read during plan authoring. Each affected task instructs the executing agent to read the component source first and adapt assertions accordingly. This is an intentional tradeoff — a fully-specified plan would require reading 20+ component files, and the agent can trivially replicate the pattern.
- Task C8 (backend ruff check) could surface a large volume of pre-existing errors. Task C8 explicitly instructs: do not mass-fix silently; if the volume is large, report back for user decision.
- Task D2 (first CI push) is expected to require one or two rounds of iteration — the plan explicitly calls this out and gives common failure modes.
