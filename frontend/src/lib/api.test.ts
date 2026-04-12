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
    let receivedContentType: string | null = null;
    server.use(
      http.post("/api/v1/projects/:pid/documents/upload", ({ request }) => {
        receivedContentType = request.headers.get("content-type");
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
    expect(receivedContentType).toContain("multipart/form-data");
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
