# Canon Builder Frontend Design

**Goal:** Build a React frontend for document uploading, RAG-powered chat, and runtime API configuration — served as static files by FastAPI in a single container.

**Architecture:** React + Vite + TypeScript SPA with shadcn/ui components. Built to static files, served by FastAPI. Three pages: Chat (primary), Documents, Settings.

**Tech Stack:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Router, React Query

---

## Component Architecture

```
frontend/
  src/
    components/
      layout/         — Shell, Sidebar, Header
      chat/           — ChatView, MessageBubble, ChatInput
      documents/      — DocumentList, UploadDropzone, DocumentCard
      settings/       — SettingsForm, ApiKeyInput
      ui/             — shadcn components (button, input, card, etc.)
    lib/
      api.ts          — API client (fetch wrapper, typed endpoints)
    hooks/
      useDocuments.ts — React Query hooks for document CRUD
      useChat.ts      — Chat state + API calls
      useHealth.ts    — Service health polling
      useSettings.ts  — Runtime settings read/update
    pages/
      ChatPage.tsx
      DocumentsPage.tsx
      SettingsPage.tsx
    App.tsx           — Router + layout
    main.tsx          — Entry point
```

**Key decisions:**
- React Query for all server state (documents, health, settings)
- Local state only for chat messages (no persistence yet)
- API client is a thin typed wrapper around fetch
- shadcn/ui components copied into components/ui/ as source files

---

## Pages & Features

### Chat Page (`/`)
- Default landing page
- Message list with user/assistant bubbles
- Input bar at bottom with send button
- Citation badges on assistant responses (document title + relevance score)
- New conversation clears history (no persistence)
- Health indicator (green/yellow/red from `/health`)

### Documents Page (`/documents`)
- Drag-and-drop upload zone (accepts .txt, .md, .pdf)
- Document cards: title, status, chunk count, created date
- Click for details, delete with confirmation
- Auto-refreshes after upload (React Query invalidation)

### Settings Page (`/settings`)
- Fields: Anthropic API Key, OpenAI API Key, Anthropic Model, OpenAI Embedding Model
- Password-masked API key fields with show/hide toggle
- Save applies changes at runtime via `PUT /api/v1/settings`
- Test Connection button hits `/health`
- Current values loaded from `GET /api/v1/settings` (keys masked)

---

## Integration & Serving

### Production (Docker)
- Multi-stage Dockerfile: Node builds frontend, Python image serves it
- FastAPI mounts `frontend/dist/` as static files at `/`
- API routes (`/api/v1/*`, `/v1/*`, `/health`) take priority
- Catch-all route serves `index.html` for client-side routing

### Development
- `npm run dev` in frontend/ for Vite dev server on port 5173
- Vite proxies `/api/v1/*` and `/v1/*` to localhost:8080
- Add localhost:5173 to CORS origins

### Docker Changes
- Multi-stage build in Dockerfile (no new container/service)
- OpenWebUI remains as separate optional service

---

## Backend Changes

### New Endpoints
- `GET /api/v1/settings` — Returns current model names and masked API keys
- `PUT /api/v1/settings` — Partial updates, recreates LLM service singleton, returns new health status

### Static File Serving
- Mount built frontend assets at `/`
- Catch-all HTML response for SPA routing

---

## Testing Strategy

- No frontend unit tests initially (thin UI layer, manual testing sufficient)
- Backend unit tests for new settings endpoints
- Manual verification: upload doc, query in chat, change settings, docker compose from clean state
