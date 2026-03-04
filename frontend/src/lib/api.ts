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
};
