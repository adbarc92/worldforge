const BASE = "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || res.statusText);
  }
  return res.json();
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  services: { generator: boolean; embedder: boolean };
}

export interface Document {
  id: string;
  title: string;
  status: string;
  chunk_count: number;
  file_path?: string;
  created_at?: string;
  error_message?: string;
}

export interface QueryResult {
  answer: string;
  citations: { title: string; relevance_score: number }[];
}

export interface SettingsResponse {
  anthropic_api_key: string;
  openai_api_key: string;
  anthropic_model: string;
  openai_embedding_model: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Contradiction {
  id: string;
  chunk_a_text: string;
  chunk_b_text: string;
  document_a_id: string | null;
  document_b_id: string | null;
  document_a_title: string;
  document_b_title: string;
  explanation: string;
  status: "open" | "resolved" | "dismissed";
  resolution_note: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface ContradictionList {
  items: Contradiction[];
  total: number;
}

export interface SynthesisOutlineSection {
  title: string;
  description: string;
}

export interface Synthesis {
  id: string;
  project_id: string;
  title: string;
  outline: SynthesisOutlineSection[] | null;
  outline_approved: boolean;
  content: string | null;
  status: "outline_pending" | "outline_ready" | "generating" | "completed" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  projects: {
    list: () => request<Project[]>("/api/v1/projects"),
    get: (id: string) => request<Project>(`/api/v1/projects/${id}`),
    create: (data: { name: string; description?: string }) =>
      request<Project>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: { name?: string; description?: string }) =>
      request<Project>(`/api/v1/projects/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<{ status: string }>(`/api/v1/projects/${id}`, { method: "DELETE" }),
  },

  documents: {
    list: (projectId: string, skip = 0, limit = 50) =>
      request<Document[]>(`/api/v1/projects/${projectId}/documents?skip=${skip}&limit=${limit}`),
    get: (projectId: string, id: string) =>
      request<Document>(`/api/v1/projects/${projectId}/documents/${id}`),
    delete: (projectId: string, id: string) =>
      request<{ status: string }>(`/api/v1/projects/${projectId}/documents/${id}`, { method: "DELETE" }),
    upload: async (projectId: string, file: File): Promise<Document> => {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${BASE}/api/v1/projects/${projectId}/documents/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || res.statusText);
      }
      return res.json();
    },
  },

  query: (projectId: string, question: string, top_k = 10) =>
    request<QueryResult>(`/api/v1/projects/${projectId}/query`, {
      method: "POST",
      body: JSON.stringify({ question, top_k }),
    }),

  settings: {
    get: () => request<SettingsResponse>("/api/v1/settings"),
    update: (data: Partial<SettingsResponse>) =>
      request<{ settings: SettingsResponse; health: HealthResponse }>(
        "/api/v1/settings",
        { method: "PUT", body: JSON.stringify(data) }
      ),
  },

  contradictions: {
    list: (projectId: string, status = "open", skip = 0, limit = 50) =>
      request<ContradictionList>(
        `/api/v1/projects/${projectId}/contradictions?status=${status}&skip=${skip}&limit=${limit}`
      ),
    scan: (projectId: string) =>
      request<{ status: string; project_id: string }>(
        `/api/v1/projects/${projectId}/contradictions/scan`,
        { method: "POST" }
      ),
    resolve: (projectId: string, id: string, note?: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/projects/${projectId}/contradictions/${id}/resolve`,
        { method: "PATCH", body: JSON.stringify({ note: note || null }) }
      ),
    dismiss: (projectId: string, id: string, note?: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/projects/${projectId}/contradictions/${id}/dismiss`,
        { method: "PATCH", body: JSON.stringify({ note: note || null }) }
      ),
    reopen: (projectId: string, id: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/projects/${projectId}/contradictions/${id}/reopen`,
        { method: "PATCH" }
      ),
  },

  synthesis: {
    list: (projectId: string) =>
      request<Synthesis[]>(`/api/v1/projects/${projectId}/synthesis`),
    get: (projectId: string, id: string) =>
      request<Synthesis>(`/api/v1/projects/${projectId}/synthesis/${id}`),
    create: (projectId: string, auto = false) =>
      request<Synthesis>(
        `/api/v1/projects/${projectId}/synthesis?auto=${auto}`,
        { method: "POST" }
      ),
    updateOutline: (projectId: string, id: string, outline: SynthesisOutlineSection[]) =>
      request<Synthesis>(
        `/api/v1/projects/${projectId}/synthesis/${id}/outline`,
        { method: "PATCH", body: JSON.stringify({ outline }) }
      ),
    approve: (projectId: string, id: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/projects/${projectId}/synthesis/${id}/approve`,
        { method: "POST" }
      ),
    download: (projectId: string, id: string) =>
      `/api/v1/projects/${projectId}/synthesis/${id}/download`,
  },
};
