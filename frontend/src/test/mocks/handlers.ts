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
