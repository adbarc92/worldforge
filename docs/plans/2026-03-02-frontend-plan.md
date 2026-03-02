# Canon Builder Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a React frontend with chat, document management, and settings pages — served as static files by FastAPI in a single container.

**Architecture:** React + Vite + TypeScript SPA using shadcn/ui. Built to static files at Docker build time, served by FastAPI's StaticFiles mount. Backend gets two new settings endpoints and a catch-all HTML route for SPA routing.

**Tech Stack:** React 18, Vite, TypeScript, Tailwind CSS v4, shadcn/ui, React Router v7, TanStack React Query v5

---

### Task 1: Scaffold React + Vite + TypeScript Project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/vite-env.d.ts`

**Step 1: Create the Vite project**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
```

Accept overwrite prompts. This creates the standard Vite + React + TypeScript scaffold.

**Step 2: Install core dependencies**

```bash
cd frontend
npm install react-router-dom @tanstack/react-query
npm install -D tailwindcss @tailwindcss/vite
```

**Step 3: Configure Vite with Tailwind and API proxy**

Replace `frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8080",
      "/v1": "http://localhost:8080",
      "/health": "http://localhost:8080",
    },
  },
});
```

**Step 4: Set up Tailwind CSS v4**

Replace `frontend/src/index.css`:

```css
@import "tailwindcss";
```

**Step 5: Create minimal App with routing**

Replace `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<div>Chat</div>} />
          <Route path="/documents" element={<div>Documents</div>} />
          <Route path="/settings" element={<div>Settings</div>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

**Step 6: Update main.tsx**

Replace `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

**Step 7: Verify it runs**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 — should see "Chat" text. Navigate to /documents and /settings.

**Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React + Vite + TypeScript frontend"
```

---

### Task 2: Set Up shadcn/ui

**Files:**
- Create: `frontend/components.json`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/input.tsx`
- Create: `frontend/src/components/ui/card.tsx`
- Create: `frontend/src/components/ui/badge.tsx`
- Create: `frontend/src/components/ui/textarea.tsx`
- Create: `frontend/src/components/ui/dialog.tsx`
- Create: `frontend/src/components/ui/label.tsx`
- Create: `frontend/src/components/ui/sonner.tsx` (toast notifications)
- Modify: `frontend/src/index.css`

**Step 1: Initialize shadcn/ui**

```bash
cd frontend
npx shadcn@latest init
```

When prompted:
- Style: Default
- Base color: Neutral
- CSS variables: Yes

**Step 2: Add required components**

```bash
cd frontend
npx shadcn@latest add button input card badge textarea dialog label sonner
```

**Step 3: Verify build**

```bash
cd frontend && npm run build
```

Should complete with no errors.

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: add shadcn/ui components"
```

---

### Task 3: Layout Shell with Sidebar Navigation

**Files:**
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/Shell.tsx`
- Create: `frontend/src/components/layout/HealthIndicator.tsx`
- Create: `frontend/src/hooks/useHealth.ts`
- Create: `frontend/src/lib/api.ts`
- Modify: `frontend/src/App.tsx`

**Step 1: Create the API client**

Create `frontend/src/lib/api.ts`:

```typescript
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

export const api = {
  health: () => request<HealthResponse>("/health"),

  documents: {
    list: (skip = 0, limit = 50) =>
      request<Document[]>(`/api/v1/documents?skip=${skip}&limit=${limit}`),
    get: (id: string) => request<Document>(`/api/v1/documents/${id}`),
    delete: (id: string) =>
      request<{ status: string }>(`/api/v1/documents/${id}`, { method: "DELETE" }),
    upload: async (file: File): Promise<Document> => {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${BASE}/api/v1/documents/upload`, {
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

  query: (question: string, top_k = 10) =>
    request<QueryResult>("/api/v1/query", {
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
```

**Step 2: Create the health hook**

Create `frontend/src/hooks/useHealth.ts`:

```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 30000,
  });
}
```

**Step 3: Create the HealthIndicator component**

Create `frontend/src/components/layout/HealthIndicator.tsx`:

```tsx
import { useHealth } from "@/hooks/useHealth";

export function HealthIndicator() {
  const { data, isError } = useHealth();

  const color = isError
    ? "bg-red-500"
    : data?.status === "healthy"
      ? "bg-green-500"
      : "bg-yellow-500";

  const label = isError
    ? "Disconnected"
    : data?.status === "healthy"
      ? "All services up"
      : "Degraded";

  return (
    <div className="flex items-center gap-2 px-3 py-1 text-xs text-muted-foreground">
      <div className={`h-2 w-2 rounded-full ${color}`} />
      {label}
    </div>
  );
}
```

**Step 4: Create the Sidebar**

Create `frontend/src/components/layout/Sidebar.tsx`:

```tsx
import { NavLink } from "react-router-dom";
import { HealthIndicator } from "./HealthIndicator";

const links = [
  { to: "/", label: "Chat", icon: "💬" },
  { to: "/documents", label: "Documents", icon: "📄" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-muted/40">
      <div className="p-4 font-semibold text-lg">Canon Builder</div>
      <nav className="flex-1 space-y-1 px-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50"
              }`
            }
          >
            <span>{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
      <HealthIndicator />
    </aside>
  );
}
```

**Step 5: Create the Shell layout**

Create `frontend/src/components/layout/Shell.tsx`:

```tsx
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";

export function Shell() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
```

**Step 6: Update App.tsx to use Shell layout**

Replace `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { Shell } from "@/components/layout/Shell";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Shell />}>
            <Route path="/" element={<div className="p-6">Chat page coming soon</div>} />
            <Route path="/documents" element={<div className="p-6">Documents page coming soon</div>} />
            <Route path="/settings" element={<div className="p-6">Settings page coming soon</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
```

**Step 7: Verify**

```bash
cd frontend && npm run dev
```

Should see sidebar with three nav links, health indicator at bottom. Navigation between routes works.

**Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: add layout shell with sidebar navigation and health indicator"
```

---

### Task 4: Documents Page — Upload and List

**Files:**
- Create: `frontend/src/hooks/useDocuments.ts`
- Create: `frontend/src/components/documents/UploadDropzone.tsx`
- Create: `frontend/src/components/documents/DocumentCard.tsx`
- Create: `frontend/src/pages/DocumentsPage.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create documents hooks**

Create `frontend/src/hooks/useDocuments.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: () => api.documents.list(),
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.documents.upload(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.documents.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}
```

**Step 2: Create UploadDropzone component**

Create `frontend/src/components/documents/UploadDropzone.tsx`:

```tsx
import { useCallback, useState } from "react";
import { useUploadDocument } from "@/hooks/useDocuments";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";

export function UploadDropzone() {
  const upload = useUploadDocument();
  const [dragging, setDragging] = useState(false);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      Array.from(files).forEach((file) => {
        const ext = file.name.split(".").pop()?.toLowerCase();
        if (!["txt", "md", "pdf"].includes(ext || "")) {
          toast.error(`Unsupported file type: .${ext}`);
          return;
        }
        upload.mutate(file, {
          onSuccess: (doc) => toast.success(`Uploaded "${doc.title}"`),
          onError: (err) => toast.error(`Upload failed: ${err.message}`),
        });
      });
    },
    [upload]
  );

  return (
    <Card
      className={`border-2 border-dashed p-8 text-center cursor-pointer transition-colors ${
        dragging ? "border-primary bg-primary/5" : "border-muted-foreground/25"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".txt,.md,.pdf";
        input.multiple = true;
        input.onchange = () => handleFiles(input.files);
        input.click();
      }}
    >
      <div className="text-muted-foreground">
        <p className="text-lg font-medium">
          {upload.isPending ? "Uploading..." : "Drop files here or click to upload"}
        </p>
        <p className="text-sm mt-1">Supports .txt, .md, .pdf</p>
      </div>
    </Card>
  );
}
```

**Step 3: Create DocumentCard component**

Create `frontend/src/components/documents/DocumentCard.tsx`:

```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDeleteDocument } from "@/hooks/useDocuments";
import { toast } from "sonner";
import type { Document } from "@/lib/api";

export function DocumentCard({ doc }: { doc: Document }) {
  const deleteMutation = useDeleteDocument();

  const statusColor =
    doc.status === "processed"
      ? "bg-green-100 text-green-800"
      : doc.status === "error"
        ? "bg-red-100 text-red-800"
        : "bg-yellow-100 text-yellow-800";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{doc.title}</CardTitle>
            <CardDescription>
              {doc.created_at
                ? new Date(doc.created_at).toLocaleDateString()
                : ""}
            </CardDescription>
          </div>
          <Badge variant="outline" className={statusColor}>
            {doc.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {doc.chunk_count} chunks
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={() => {
              if (confirm(`Delete "${doc.title}"?`)) {
                deleteMutation.mutate(doc.id, {
                  onSuccess: () => toast.success("Document deleted"),
                  onError: (err) => toast.error(err.message),
                });
              }
            }}
          >
            Delete
          </Button>
        </div>
        {doc.error_message && (
          <p className="text-sm text-destructive mt-2">{doc.error_message}</p>
        )}
      </CardContent>
    </Card>
  );
}
```

**Step 4: Create DocumentsPage**

Create `frontend/src/pages/DocumentsPage.tsx`:

```tsx
import { useDocuments } from "@/hooks/useDocuments";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentCard } from "@/components/documents/DocumentCard";

export function DocumentsPage() {
  const { data: documents, isLoading } = useDocuments();

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Documents</h1>
      <UploadDropzone />
      {isLoading ? (
        <p className="text-muted-foreground">Loading documents...</p>
      ) : documents?.length === 0 ? (
        <p className="text-muted-foreground">No documents uploaded yet.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {documents?.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </div>
  );
}
```

**Step 5: Wire into App.tsx**

In `frontend/src/App.tsx`, replace the documents placeholder route:

```tsx
import { DocumentsPage } from "@/pages/DocumentsPage";
// ... in Routes:
<Route path="/documents" element={<DocumentsPage />} />
```

**Step 6: Verify**

```bash
cd frontend && npm run dev
```

Navigate to /documents. Should see upload dropzone and empty state. Upload will fail until backend is running — that's expected.

**Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: add documents page with upload dropzone and document cards"
```

---

### Task 5: Chat Page

**Files:**
- Create: `frontend/src/hooks/useChat.ts`
- Create: `frontend/src/components/chat/MessageBubble.tsx`
- Create: `frontend/src/components/chat/ChatInput.tsx`
- Create: `frontend/src/components/chat/ChatView.tsx`
- Create: `frontend/src/pages/ChatPage.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create chat hook**

Create `frontend/src/hooks/useChat.ts`:

```typescript
import { useState, useCallback } from "react";
import { api } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: { title: string; relevance_score: number }[];
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const send = useCallback(
    async (question: string) => {
      const userMsg: ChatMessage = { role: "user", content: question };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const result = await api.query(question);
        const assistantMsg: ChatMessage = {
          role: "assistant",
          content: result.answer,
          citations: result.citations,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const errorMsg: ChatMessage = {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Something went wrong"}`,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const clear = useCallback(() => setMessages([]), []);

  return { messages, isLoading, send, clear };
}
```

**Step 2: Create MessageBubble component**

Create `frontend/src/components/chat/MessageBubble.tsx`:

```tsx
import { Badge } from "@/components/ui/badge";
import type { ChatMessage } from "@/hooks/useChat";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.citations.map((c, i) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {c.title} ({Math.round(c.relevance_score * 100)}%)
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 3: Create ChatInput component**

Create `frontend/src/components/chat/ChatInput.tsx`:

```tsx
import { useState, useRef, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled) ref.current?.focus();
  }, [disabled]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="flex gap-2 p-4 border-t">
      <Textarea
        ref={ref}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        placeholder="Ask a question about your documents..."
        className="min-h-[44px] max-h-[120px] resize-none"
        disabled={disabled}
      />
      <Button onClick={handleSend} disabled={disabled || !value.trim()}>
        Send
      </Button>
    </div>
  );
}
```

**Step 4: Create ChatView component**

Create `frontend/src/components/chat/ChatView.tsx`:

```tsx
import { useRef, useEffect } from "react";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import type { ChatMessage } from "@/hooks/useChat";

interface ChatViewProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSend: (message: string) => void;
  onClear: () => void;
}

export function ChatView({ messages, isLoading, onSend, onClear }: ChatViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b">
        <h1 className="text-lg font-semibold">Chat</h1>
        {messages.length > 0 && (
          <button
            onClick={onClear}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Clear
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p>Ask a question about your uploaded documents.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-3 text-sm text-muted-foreground">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={onSend} disabled={isLoading} />
    </div>
  );
}
```

**Step 5: Create ChatPage**

Create `frontend/src/pages/ChatPage.tsx`:

```tsx
import { useChat } from "@/hooks/useChat";
import { ChatView } from "@/components/chat/ChatView";

export function ChatPage() {
  const { messages, isLoading, send, clear } = useChat();

  return (
    <ChatView
      messages={messages}
      isLoading={isLoading}
      onSend={send}
      onClear={clear}
    />
  );
}
```

**Step 6: Wire into App.tsx**

In `frontend/src/App.tsx`, replace the chat placeholder:

```tsx
import { ChatPage } from "@/pages/ChatPage";
// ... in Routes:
<Route path="/" element={<ChatPage />} />
```

**Step 7: Verify**

```bash
cd frontend && npm run dev
```

Chat page should show empty state with input. Sending a message will show user bubble + loading + error (backend not proxied yet in dev — that's fine).

**Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: add chat page with message bubbles and RAG query integration"
```

---

### Task 6: Settings Page

**Files:**
- Create: `frontend/src/hooks/useSettings.ts`
- Create: `frontend/src/pages/SettingsPage.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create settings hook**

Create `frontend/src/hooks/useSettings.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type SettingsResponse } from "@/lib/api";

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: api.settings.get,
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<SettingsResponse>) => api.settings.update(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] });
      qc.invalidateQueries({ queryKey: ["health"] });
    },
  });
}
```

**Step 2: Create SettingsPage**

Create `frontend/src/pages/SettingsPage.tsx`:

```tsx
import { useState, useEffect } from "react";
import { useSettings, useUpdateSettings } from "@/hooks/useSettings";
import { useHealth } from "@/hooks/useHealth";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export function SettingsPage() {
  const { data: settings, isLoading } = useSettings();
  const { data: health } = useHealth();
  const update = useUpdateSettings();

  const [form, setForm] = useState({
    anthropic_api_key: "",
    openai_api_key: "",
    anthropic_model: "",
    openai_embedding_model: "",
  });
  const [showKeys, setShowKeys] = useState(false);

  useEffect(() => {
    if (settings) {
      setForm({
        anthropic_api_key: settings.anthropic_api_key,
        openai_api_key: settings.openai_api_key,
        anthropic_model: settings.anthropic_model,
        openai_embedding_model: settings.openai_embedding_model,
      });
    }
  }, [settings]);

  const handleSave = () => {
    update.mutate(form, {
      onSuccess: (result) => {
        const status = result.health.status;
        if (status === "healthy") {
          toast.success("Settings saved — all services connected");
        } else {
          toast.warning("Settings saved — some services unavailable");
        }
      },
      onError: (err) => toast.error(err.message),
    });
  };

  if (isLoading) return <div className="p-6">Loading settings...</div>;

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Service Status</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <div className="flex items-center gap-2">
            <Badge variant={health?.services.generator ? "default" : "destructive"}>
              {health?.services.generator ? "Connected" : "Disconnected"}
            </Badge>
            <span className="text-sm">Generator (Anthropic)</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={health?.services.embedder ? "default" : "destructive"}>
              {health?.services.embedder ? "Connected" : "Disconnected"}
            </Badge>
            <span className="text-sm">Embedder (OpenAI)</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>API Keys</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setShowKeys(!showKeys)}>
              {showKeys ? "Hide" : "Show"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="anthropic_key">Anthropic API Key</Label>
            <Input
              id="anthropic_key"
              type={showKeys ? "text" : "password"}
              value={form.anthropic_api_key}
              onChange={(e) =>
                setForm({ ...form, anthropic_api_key: e.target.value })
              }
              placeholder="sk-ant-api03-..."
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="openai_key">OpenAI API Key</Label>
            <Input
              id="openai_key"
              type={showKeys ? "text" : "password"}
              value={form.openai_api_key}
              onChange={(e) =>
                setForm({ ...form, openai_api_key: e.target.value })
              }
              placeholder="sk-proj-..."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Models</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="anthropic_model">Anthropic Model</Label>
            <Input
              id="anthropic_model"
              value={form.anthropic_model}
              onChange={(e) =>
                setForm({ ...form, anthropic_model: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="embedding_model">OpenAI Embedding Model</Label>
            <Input
              id="embedding_model"
              value={form.openai_embedding_model}
              onChange={(e) =>
                setForm({ ...form, openai_embedding_model: e.target.value })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave} disabled={update.isPending} className="w-full">
        {update.isPending ? "Saving..." : "Save Settings"}
      </Button>
    </div>
  );
}
```

**Step 3: Wire into App.tsx**

In `frontend/src/App.tsx`, replace the settings placeholder:

```tsx
import { SettingsPage } from "@/pages/SettingsPage";
// ... in Routes:
<Route path="/settings" element={<SettingsPage />} />
```

**Step 4: Verify**

```bash
cd frontend && npm run dev
```

Settings page shows service status, API key fields (masked), model fields, and save button.

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: add settings page with API key and model configuration"
```

---

### Task 7: Backend Settings Endpoints

**Files:**
- Create: `backend/app/api/v1/settings.py`
- Modify: `backend/app/api/v1/__init__.py:3-8` (add settings router)
- Modify: `backend/app/dependencies.py:12-28` (add reset function)
- Create: `backend/tests/test_settings.py`

**Step 1: Write the failing tests**

Create `backend/tests/test_settings.py`:

```python
import pytest
from unittest.mock import patch, AsyncMock


def test_mask_api_key():
    from app.api.v1.settings import mask_key

    assert mask_key("sk-ant-api03-abcdefghijk") == "sk-ant-***-hijk"
    assert mask_key("sk-proj-abcdefghijklmnop") == "sk-pr***-mnop"
    assert mask_key("short") == "****"
    assert mask_key("") == ""


@pytest.mark.asyncio
async def test_get_settings():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "anthropic_api_key" in data
        assert "anthropic_model" in data
        # Keys should be masked
        if data["anthropic_api_key"]:
            assert "***" in data["anthropic_api_key"]
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/test_settings.py -v
```

Expected: FAIL (module not found)

**Step 3: Add reset function to dependencies.py**

In `backend/app/dependencies.py`, after the `get_llm_service` function, add:

```python
def reset_llm_service():
    global _llm_service
    _llm_service = None
```

**Step 4: Create settings router**

Create `backend/app/api/v1/settings.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.dependencies import get_llm_service, reset_llm_service

router = APIRouter(prefix="/settings", tags=["settings"])


def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:5]}***{key[-4:]}"


class SettingsResponse(BaseModel):
    anthropic_api_key: str
    openai_api_key: str
    anthropic_model: str
    openai_embedding_model: str


class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_model: str | None = None
    openai_embedding_model: str | None = None


@router.get("", response_model=SettingsResponse)
async def get_settings():
    return SettingsResponse(
        anthropic_api_key=mask_key(settings.ANTHROPIC_API_KEY),
        openai_api_key=mask_key(settings.OPENAI_API_KEY),
        anthropic_model=settings.ANTHROPIC_MODEL,
        openai_embedding_model=settings.OPENAI_EMBEDDING_MODEL,
    )


@router.put("")
async def update_settings(data: SettingsUpdate):
    if data.anthropic_api_key and "***" not in data.anthropic_api_key:
        settings.ANTHROPIC_API_KEY = data.anthropic_api_key
    if data.openai_api_key and "***" not in data.openai_api_key:
        settings.OPENAI_API_KEY = data.openai_api_key
    if data.anthropic_model:
        settings.ANTHROPIC_MODEL = data.anthropic_model
    if data.openai_embedding_model:
        settings.OPENAI_EMBEDDING_MODEL = data.openai_embedding_model

    # Reset LLM service so it picks up new settings
    reset_llm_service()

    # Check new health
    llm = get_llm_service()
    health = await llm.check_available()

    return {
        "settings": SettingsResponse(
            anthropic_api_key=mask_key(settings.ANTHROPIC_API_KEY),
            openai_api_key=mask_key(settings.OPENAI_API_KEY),
            anthropic_model=settings.ANTHROPIC_MODEL,
            openai_embedding_model=settings.OPENAI_EMBEDDING_MODEL,
        ),
        "health": {
            "status": "healthy" if all(health.values()) else "degraded",
            "services": health,
        },
    }
```

**Step 5: Register settings router**

In `backend/app/api/v1/__init__.py`, add:

```python
from app.api.v1.settings import router as settings_router

router.include_router(settings_router)
```

**Step 6: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/test_settings.py -v
```

Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/api/v1/settings.py backend/app/api/v1/__init__.py backend/app/dependencies.py backend/tests/test_settings.py
git commit -m "feat: add GET/PUT settings endpoints with key masking"
```

---

### Task 8: Backend Static File Serving + SPA Catch-All

**Files:**
- Modify: `backend/app/main.py:1-71` (add static mount and catch-all)

**Step 1: Modify main.py to serve frontend static files**

After the `app.include_router(openai_router)` line (line 71), add:

```python
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve frontend static files (production only)
frontend_dist = Path(__file__).resolve().parent.parent / "frontend_dist"
if frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="static")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = frontend_dist / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
```

**Key details:**
- Only mounts if `frontend_dist/` directory exists (so backend-only dev still works)
- `/assets` mount handles Vite's hashed static files
- Catch-all route serves `index.html` for SPA routing
- API routes (`/api/v1/*`, `/v1/*`, `/health`) are registered first, so they take priority

**Step 2: Add localhost:5173 to default CORS origins**

In `backend/app/core/config.py`, update the CORS_ORIGINS default:

```python
CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
```

**Step 3: Verify backend still starts**

```bash
cd backend && uv run uvicorn app.main:app --port 8080
```

Should start without errors (no frontend_dist directory exists yet, so no static mount).

**Step 4: Commit**

```bash
git add backend/app/main.py backend/app/core/config.py
git commit -m "feat: add SPA static file serving and CORS for frontend dev"
```

---

### Task 9: Multi-Stage Dockerfile

**Files:**
- Modify: `backend/Dockerfile`

**Step 1: Rewrite Dockerfile with multi-stage build**

Replace `backend/Dockerfile`:

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.11-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN useradd --create-home appuser

WORKDIR /app

# Install dependencies (cached layer)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY backend/ .

# Copy built frontend
COPY --from=frontend-build /build/dist ./frontend_dist

# Create upload directory
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Step 2: Update docker-compose.yml build context**

Since the Dockerfile now needs both `frontend/` and `backend/`, update `docker-compose.yml`:

```yaml
  canon_api:
    build:
      context: .
      dockerfile: backend/Dockerfile
```

The build context moves from `./backend` to `.` (project root) so the Dockerfile can access both `frontend/` and `backend/`.

**Step 3: Move Dockerfile to project root** (or adjust COPY paths)

Actually, it's cleaner to move the Dockerfile to the project root. Rename `backend/Dockerfile` to `Dockerfile` at the project root, and update docker-compose.yml:

```yaml
  canon_api:
    build:
      context: .
      dockerfile: Dockerfile
```

**Step 4: Add frontend/node_modules to .dockerignore**

Create `.dockerignore` at project root:

```
frontend/node_modules
backend/__pycache__
backend/.venv
.git
.worktrees
*.pyc
```

**Step 5: Verify Docker build**

```bash
docker compose build canon_api
```

Should build both stages successfully.

**Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git rm backend/Dockerfile
git commit -m "feat: multi-stage Dockerfile builds frontend + backend in single image"
```

---

### Task 10: Integration Test — Full Stack

**Step 1: Build and start everything**

```bash
docker compose down
docker compose up -d --build
```

**Step 2: Wait for healthy**

```bash
# Wait for API to be ready
sleep 20
curl http://localhost:8080/health
```

Expected: `{"status":"healthy","services":{"generator":true,"embedder":true}}`

**Step 3: Verify frontend is served**

```bash
curl -s http://localhost:8080/ | head -5
```

Expected: HTML containing `<div id="root">` and a `<script>` tag pointing to `/assets/`.

**Step 4: Verify SPA routing**

```bash
curl -s http://localhost:8080/documents | head -5
curl -s http://localhost:8080/settings | head -5
```

Expected: Same HTML (index.html served for all routes).

**Step 5: Verify API still works**

```bash
curl http://localhost:8080/api/v1/documents
curl http://localhost:8080/api/v1/settings
```

Expected: JSON responses (empty documents array, masked settings).

**Step 6: Manual browser test**

Open http://localhost:8080 in browser:
1. Sidebar navigation works
2. Documents page: upload a .txt file, see it appear
3. Chat page: ask a question about the uploaded document
4. Settings page: see masked API keys, change model name, save

**Step 7: Commit any fixes needed**

```bash
git add -A
git commit -m "fix: integration test fixes"
```

---

### Task 11: Cleanup and Final Polish

**Files:**
- Remove: `frontend/src/App.css` (if exists, unused)
- Remove: `frontend/public/vite.svg` (unused)
- Remove: `frontend/src/assets/react.svg` (unused)

**Step 1: Remove Vite scaffold artifacts**

```bash
rm -f frontend/src/App.css frontend/public/vite.svg frontend/src/assets/react.svg
```

**Step 2: Verify build**

```bash
cd frontend && npm run build
```

Should succeed with no warnings about missing files.

**Step 3: Update .gitignore**

Add to `.gitignore`:

```
# Frontend
frontend/node_modules/
frontend/dist/
```

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: clean up scaffold artifacts and update gitignore"
```

---

## Task Dependency Order

Tasks 1-6 (frontend) are sequential — each builds on the previous.
Task 7 (backend settings) is independent and can be done in parallel with frontend tasks.
Task 8 (static serving) depends on Task 7.
Task 9 (Dockerfile) depends on Tasks 1-8.
Task 10 (integration) depends on Task 9.
Task 11 (cleanup) depends on Task 10.
