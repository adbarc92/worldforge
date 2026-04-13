# WorldForge Architecture Guide

**Version:** 0.2.0
**Last Updated:** April 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Deployment Architecture](#2-deployment-architecture)
3. [Backend Architecture](#3-backend-architecture)
   - [Application Lifecycle](#31-application-lifecycle)
   - [API Layer](#32-api-layer)
   - [Service Layer](#33-service-layer)
   - [Data Access Layer](#34-data-access-layer)
   - [Dependency Injection](#35-dependency-injection)
   - [Configuration](#36-configuration)
4. [Frontend Architecture](#4-frontend-architecture)
   - [Component Hierarchy](#41-component-hierarchy)
   - [State Management](#42-state-management)
   - [Data Flow](#43-data-flow)
5. [Core Workflows](#5-core-workflows)
   - [Document Ingestion](#51-document-ingestion)
   - [RAG Query](#52-rag-query)
   - [Contradiction Detection](#53-contradiction-detection)
   - [OpenWebUI Integration](#54-openwebui-integration)
6. [LLM Provider System](#6-llm-provider-system)
7. [Data Architecture](#7-data-architecture)
   - [PostgreSQL Schema](#71-postgresql-schema)
   - [Qdrant Vector Storage](#72-qdrant-vector-storage)
   - [Dual-Store Relationship](#73-dual-store-relationship)
8. [Multi-Project Scoping](#8-multi-project-scoping)
9. [Runtime Settings](#9-runtime-settings)
10. [Build and Packaging](#10-build-and-packaging)
11. [API Reference](#11-api-reference)
12. [Design Decisions](#12-design-decisions)

---

## 1. System Overview

WorldForge (internally "Canon Builder") is a RAG-powered worldbuilding knowledge system. It lets you upload lore documents (text, markdown, PDF), chunks and embeds them into a vector database, then provides AI-generated answers grounded in your source material with full citations.

The system is designed as a **single-user personal tool** — there is no authentication layer. It prioritizes ease of deployment (one `docker compose up` command) and a self-contained packaging model where the React frontend and Python backend ship in a single container.

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Cluster                           │
│                                                                         │
│  ┌───────────────────────────────────────────────────┐                  │
│  │          canon_api (port 8080)                     │                  │
│  │  ┌─────────────────┐  ┌─────────────────────────┐ │                  │
│  │  │  React SPA       │  │  FastAPI Backend         │ │                  │
│  │  │  (static files)  │  │  ┌───────────────────┐  │ │                  │
│  │  │  - Chat UI       │  │  │ /api/v1/*          │  │ │                  │
│  │  │  - Documents     │  │  │ /health            │  │ │                  │
│  │  │  - Projects      │  │  │ /v1/* (OpenAI)     │  │ │                  │
│  │  │  - Settings      │  │  └───────────────────┘  │ │                  │
│  │  └─────────────────┘  └─────────────────────────┘ │                  │
│  └───────────────────────────────────────────────────┘                  │
│           │                    │                │                        │
│           │              ┌─────┴──────┐   ┌────┴────────┐               │
│           │              │ PostgreSQL  │   │   Qdrant    │               │
│           │              │ (port 5432) │   │ (port 6333) │               │
│           │              │ metadata,   │   │ vectors,    │               │
│           │              │ projects,   │   │ semantic    │               │
│           │              │ documents   │   │ search      │               │
│           │              └────────────┘   └─────────────┘               │
│           │                                                             │
│  ┌────────┴───────────────┐                                             │
│  │  OpenWebUI (port 3000) │  (optional — alternate chat frontend)       │
│  └────────────────────────┘                                             │
└─────────────────────────────────────────────────────────────────────────┘
                    │                         │
              Anthropic API              OpenAI API
              (Claude — generation)      (text-embedding-3-large)
```

---

## 2. Deployment Architecture

### Docker Compose Services

| Service      | Image                           | Port  | Purpose                                 |
|--------------|---------------------------------|-------|-----------------------------------------|
| `canon_api`  | Custom multi-stage Dockerfile   | 8080  | Backend API + frontend SPA (single image) |
| `postgres`   | `postgres:16-alpine`            | 5432  | Document metadata, projects, contradictions |
| `qdrant`     | `qdrant/qdrant:latest`          | 6333  | Vector embeddings, semantic search      |
| `openwebui`  | `ghcr.io/open-webui/open-webui` | 3000  | Optional alternate chat UI              |

**Health checks**: PostgreSQL and Qdrant expose health checks; `canon_api` depends on both being healthy before starting. The canon_api container itself has a health check hitting `/health`.

### Multi-Stage Dockerfile

The build uses a two-stage Dockerfile to produce a single deployable image:

```
Stage 1: node:20-alpine
  └── npm ci + npm run build → produces frontend/dist/

Stage 2: python:3.11-slim
  └── uv sync --frozen --no-dev → installs Python deps
  └── COPY backend code
  └── COPY frontend/dist → frontend_dist/
  └── CMD: uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The frontend is built as static assets and served by FastAPI at runtime. This means there is no separate Node.js process in production — the Python process serves everything.

### Development Mode

In development, the frontend runs as a separate Vite dev server on port 5173 with a proxy to the backend on port 8080. This enables hot module replacement for frontend development.

```
Vite dev server (localhost:5173) ──proxy──▶ FastAPI (localhost:8080)
```

---

## 3. Backend Architecture

### 3.1 Application Lifecycle

**Entry point:** `backend/app/main.py`

The FastAPI application uses a lifespan context manager that orchestrates startup and shutdown:

```
Startup sequence:
  1. Run Alembic migrations (auto-applies on every boot)
  2. Ensure Qdrant collection exists (creates if missing)
  3. Backfill project_id on legacy Qdrant points
  4. Verify LLM provider availability (generator + embedder)
  5. Log readiness

Shutdown sequence:
  1. Close Qdrant client connection
  2. Dispose SQLAlchemy engine
```

**Router registration order matters.** The FastAPI app registers routes in this order:

1. `/api/v1/*` — all business API routes
2. `/v1/*` — OpenAI-compatible endpoints
3. `/health` — health check
4. `/{path:path}` — SPA catch-all (only when `frontend_dist/` exists)

The catch-all route is registered last so it never intercepts API calls. It serves `index.html` for any path that doesn't match a static file, enabling client-side routing.

### 3.2 API Layer

All API routes live under `backend/app/api/v1/` and are mounted at the `/api/v1` prefix.

```
/api/v1/
├── /projects                          Projects CRUD
│   ├── POST   /                       Create project
│   ├── GET    /                       List all projects (with doc counts)
│   ├── GET    /{project_id}           Get single project
│   ├── PUT    /{project_id}           Update project
│   └── DELETE /{project_id}           Delete project (cascades to Qdrant)
│
├── /projects/{project_id}/documents   Document management (project-scoped)
│   ├── POST   /upload                 Upload and ingest document
│   ├── GET    /                       List documents in project
│   ├── GET    /{doc_id}               Get document details
│   └── DELETE /{doc_id}               Delete document + vectors
│
├── /projects/{project_id}/query       RAG query (project-scoped)
│   └── POST   /                       Ask a question against the canon
│
└── /settings                          Runtime configuration
    ├── GET    /                        Get settings (keys masked)
    └── PUT    /                        Update settings (resets LLM service)

/v1/                                   OpenAI-compatible API
├── POST /chat/completions             Chat completions (RAG-backed)
└── GET  /models                       List available models
```

**Pattern: Project verification.** All project-scoped routes call `_verify_project()` before processing, which loads the project from the database and raises HTTP 404 if it doesn't exist. Document routes additionally verify that the requested document belongs to the specified project.

**Pattern: Background tasks.** Document upload triggers a background contradiction scan using `asyncio.create_task()`. This runs independently after the upload response is returned to the client, so ingestion latency is not affected by contradiction detection.

### 3.3 Service Layer

The service layer contains the core business logic, organized by domain:

```
backend/app/services/
├── ingestion_service.py       Document processing pipeline
├── rag_service.py             Query + context assembly + generation
├── qdrant_service.py          Vector database operations
├── contradiction_service.py   Cross-document contradiction detection
└── llm/
    ├── base.py                LLMProvider abstract base class
    ├── anthropic_provider.py  Claude generation provider
    ├── openai_provider.py     OpenAI embedding provider
    └── service.py             LLMService (composes generator + embedder)
```

**IngestionService** — Orchestrates the full document processing pipeline: text extraction, chunking, embedding, and vector storage. On failure, it rolls back both database records and Qdrant vectors. Accepts txt, md, and pdf formats.

**RAGService** — Handles the query pipeline: embeds the question, searches Qdrant for relevant chunks (filtered by project), assembles a token-aware context window, and generates an answer via Claude with a grounding system prompt. Returns the answer plus citations with relevance scores.

**QdrantService** — Thin async wrapper around the Qdrant client. Manages collection creation, vector upsert, similarity search (with optional payload filters), scroll-based retrieval, and deletion by document or project.

**ContradictionService** — Compares document chunks against each other using LLM classification. For each new document, it retrieves the document's chunks from Qdrant, then compares them against all other chunks in the project. The LLM classifies each pair as contradictory or not, and stores results in the contradictions table.

### 3.4 Data Access Layer

Repositories follow the **repository pattern**, providing a clean abstraction over SQLAlchemy:

```
backend/app/models/
├── database.py                ORM models (Project, Document) + engine setup
├── repositories.py            DocumentRepository
├── project_repository.py      ProjectRepository
├── contradiction_repository.py ContradictionRepository
├── contradiction.py           Contradiction ORM model
├── synthesis.py               Synthesis ORM model
└── schemas.py                 Pydantic request/response schemas
```

Each repository takes an `AsyncSession` and exposes CRUD methods. The session is scoped per-request via FastAPI's `Depends(get_db)`.

### 3.5 Dependency Injection

`backend/app/dependencies.py` is the central dependency wiring module. It manages two categories of dependencies:

**Singletons** (created once, reused across requests):
- `LLMService` — the generator + embedder pair
- `QdrantService` — the vector DB client

**Per-request** (created fresh each request via `Depends()`):
- `IngestionService` — receives db session, LLM service, Qdrant service
- `RAGService` — receives LLM service, Qdrant service

```python
# Singleton pattern
_llm_service: LLMService | None = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(generator=..., embedder=...)
    return _llm_service
```

The `reset_llm_service()` function clears the singleton, forcing recreation with new settings on the next call. This is how runtime setting changes take effect immediately.

### 3.6 Configuration

`backend/app/core/config.py` uses pydantic-settings for environment-based configuration:

| Setting                 | Default                                   | Purpose                        |
|-------------------------|-------------------------------------------|--------------------------------|
| `ANTHROPIC_API_KEY`     | (required)                                | Claude API key for generation  |
| `OPENAI_API_KEY`        | (required)                                | OpenAI API key for embeddings  |
| `DATABASE_URL`          | `postgresql+asyncpg://...localhost:5432/` | PostgreSQL connection string   |
| `QDRANT_URL`            | `http://localhost:6333`                   | Qdrant connection URL          |
| `ANTHROPIC_MODEL`       | `claude-sonnet-4-20250514`                 | Generation model               |
| `OPENAI_EMBEDDING_MODEL`| `text-embedding-3-large`                  | Embedding model                |
| `EMBEDDING_DIMENSIONS`  | `3072`                                    | Embedding vector size          |
| `CHUNK_SIZE`            | `512`                                     | Tokens per chunk               |
| `CHUNK_OVERLAP`         | `50`                                      | Token overlap between chunks   |
| `TOP_K_RETRIEVAL`       | `10`                                      | Default number of chunks to retrieve |
| `CONTEXT_MAX_TOKENS`    | `4000`                                    | Max tokens in RAG context window |
| `CORS_ORIGINS`          | `[localhost:3000, :5173, :8080]`          | Allowed CORS origins           |
| `UPLOAD_DIR`            | `/app/uploads`                            | File upload directory          |

Settings are loaded from environment variables and `.env` files. In Docker Compose, environment variables are injected from the compose file and host `.env`.

---

## 4. Frontend Architecture

**Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, React Router v7, TanStack React Query v5

### 4.1 Component Hierarchy

```
App.tsx
└── QueryClientProvider          (TanStack React Query)
    └── ProjectProvider          (active project context)
        └── BrowserRouter
            └── Routes
                └── Shell        (sidebar + content area)
                    ├── Sidebar
                    │   ├── ProjectSelector
                    │   ├── Nav links (Chat, Documents, Projects, Settings, ...)
                    │   └── HealthIndicator
                    │
                    └── <Outlet>  (routed page content)
                        ├── /           → ChatPage
                        │                   └── ChatView
                        │                       ├── MessageBubble (per message)
                        │                       └── ChatInput
                        │
                        ├── /documents  → DocumentsPage
                        │                   ├── UploadDropzone
                        │                   └── DocumentCard (per document)
                        │
                        ├── /projects   → ProjectsPage
                        │                   └── Project cards + create/delete dialogs
                        │
                        └── /settings   → SettingsPage
                                            └── API key + model config form
```

### 4.2 State Management

The frontend uses a **two-tier state model**:

**Server state (React Query):** All data fetched from the API — documents, projects, health, settings — is managed through TanStack React Query via custom hooks. Query keys are scoped by `projectId` (e.g., `["documents", projectId]`) so that switching projects automatically invalidates and refetches data.

| Hook               | Query Key                  | Refetch Interval | Purpose                  |
|--------------------|----------------------------|-------------------|--------------------------|
| `useDocuments`     | `["documents", projectId]` | —                 | List project documents   |
| `useProjects`      | `["projects"]`             | —                 | List all projects        |
| `useHealth`        | `["health"]`               | 30 seconds        | Service health polling   |
| `useSettings`      | `["settings"]`             | —                 | API keys + model config  |

Mutations (upload, delete, create, update) automatically invalidate the relevant query caches on success.

**Client state:** Chat messages are managed with plain `useState` in `useChat`. Messages are not persisted server-side — they exist only for the duration of the browser session. This is a deliberate choice: the tool is for querying the canon, not for maintaining conversation history.

**Project context:** The active project is stored in React Context (`ProjectContext`) and persisted to `localStorage` so it survives page refreshes. The `ProjectSelector` component in the sidebar controls this globally.

### 4.3 Data Flow

```
User action
  │
  ▼
Page component reads activeProject from ProjectContext
  │
  ▼
Custom hook (e.g., useDocuments) scoped to activeProject.id
  │
  ▼
api.ts fetch wrapper → backend API
  │
  ▼
React Query cache updated → component re-renders
```

**Project guard pattern:** Pages that require an active project (Chat, Documents) show a guard message ("Select a project to get started") when `activeProject` is null.

**Chat flow specifically:**
1. User types question in `ChatInput`
2. `useChat.send()` appends user message to local state
3. Calls `api.query(projectId, question)` (RAG query)
4. Appends assistant response + citations to local state
5. `MessageBubble` renders the response with citation badges

### 4.4 API Client

`frontend/src/lib/api.ts` is a typed fetch wrapper. It defines TypeScript interfaces for all API responses and exports a single `api` object with methods organized by resource:

```typescript
api.health()                              // GET /health
api.projects.list()                       // GET /api/v1/projects
api.projects.create({name, description})  // POST /api/v1/projects
api.documents.list(projectId)             // GET /api/v1/projects/:id/documents
api.documents.upload(projectId, file)     // POST (multipart form)
api.query(projectId, question, top_k)     // POST /api/v1/projects/:id/query
api.settings.get()                        // GET /api/v1/settings
api.settings.update(data)                 // PUT /api/v1/settings
```

The `BASE` URL is empty (same origin), which works both in production (same container) and development (Vite proxy).

---

## 5. Core Workflows

### 5.1 Document Ingestion

```
            User uploads file via UI
                     │
                     ▼
         ┌──── documents.py ────┐
         │  1. Validate file type (.txt, .md, .pdf)
         │  2. Save file to UPLOAD_DIR
         │  3. Call IngestionService.process_document()
         └───────────┬──────────┘
                     │
         ┌──── IngestionService ────┐
         │                          │
         │  4. Create Document record (status: "pending")
         │  5. Update status → "processing"
         │  6. Extract text:
         │     - .txt/.md → read UTF-8
         │     - .pdf → PyPDF page extraction
         │  7. Chunk text:
         │     - LlamaIndex SentenceSplitter
         │     - 512 tokens/chunk, 50 token overlap
         │     - Each chunk gets a UUID
         │  8. Embed all chunks:
         │     - OpenAI text-embedding-3-large
         │     - 3072-dimensional vectors
         │  9. Upsert to Qdrant:
         │     - Vector + payload (text, doc_id, title, project_id)
         │ 10. Update Document → "completed" with chunk_count
         │                          │
         │  On failure:             │
         │  - Update Document → "failed" with error_message
         │  - Delete any vectors already stored in Qdrant
         └──────────┬───────────────┘
                    │
                    ▼
         Background task (fire-and-forget):
           ContradictionService.scan_document()
           → compares new chunks against all project chunks
           → stores any detected contradictions
```

### 5.2 RAG Query

```
         User asks: "Who rules the Northern Kingdom?"
                     │
                     ▼
         ┌──── query.py ────┐
         │  1. Verify project exists
         │  2. Call RAGService.query()
         └────────┬─────────┘
                  │
         ┌──── RAGService ────┐
         │                     │
         │  3. Embed the question
         │     → OpenAI text-embedding-3-large → 3072-dim vector
         │                     │
         │  4. Search Qdrant
         │     → Cosine similarity, top-k=10
         │     → Filtered by project_id
         │     → Returns scored chunks with payloads
         │                     │
         │  5. Assemble context (token-aware)
         │     → Iterate chunks in relevance order
         │     → Count tokens with tiktoken (cl100k_base)
         │     → Pack chunks until CONTEXT_MAX_TOKENS (4000) reached
         │     → Format as numbered [Source N] blocks
         │                     │
         │  6. Generate answer
         │     │
         │     ├─ If context found:
         │     │  System: "Answer using ONLY the provided source material..."
         │     │  User:   "Question: ... Sources: ... Answer based on sources."
         │     │  → Claude (temperature=0.3)
         │     │
         │     └─ If no context:
         │        System: "No relevant source material was found..."
         │        User:   "Question: ..."
         │        → Claude (temperature=0.3)
         │                     │
         │  7. Return:
         │     { answer, citations[], processing_time_ms }
         └─────────────────────┘
```

**Token-aware context assembly** is a key design feature. Rather than naively concatenating all retrieved chunks (which could overflow the LLM's context window), `_assemble_context()` uses tiktoken to count tokens and stops adding chunks when the budget (`CONTEXT_MAX_TOKENS = 4000`) is exhausted. Chunks are processed in relevance order, so the most relevant sources always make it in.

### 5.3 Contradiction Detection

```
         Triggered after document upload (background task)
                     │
                     ▼
         ┌──── ContradictionService ────┐
         │                              │
         │  1. Get all chunks for the new document (from Qdrant)
         │  2. Get all chunks for other documents in the project
         │  3. For each pair (new_chunk, existing_chunk):
         │     a. Skip if pair already checked
         │     b. Send both texts to LLM:
         │        "Do these passages contradict each other?"
         │     c. LLM returns: { is_contradiction, explanation }
         │     d. If contradictory → store in contradictions table
         │                              │
         │  Result: count of new contradictions found
         └──────────────────────────────┘
```

Contradiction records include the full text of both chunks, document titles, and the LLM's explanation. Users can review contradictions and mark them as "resolved" or "dismissed" with optional notes.

### 5.4 OpenWebUI Integration

The backend exposes an **OpenAI-compatible API** at `/v1/chat/completions` and `/v1/models`, allowing OpenWebUI (or any OpenAI-compatible client) to use WorldForge as a model provider.

```
OpenWebUI container
  │
  │  OPENAI_API_BASE_URL=http://canon_api:8080/v1
  │
  ▼
POST /v1/chat/completions
  │
  ├─ Extracts last user message from the messages array
  ├─ Runs the full RAG pipeline via RAGService.query()
  ├─ Appends formatted citation list to the answer
  └─ Returns OpenAI-format response:
     { id, object: "chat.completion", choices: [{message: {content}}] }

GET /v1/models
  └─ Returns single model: "canon-builder"
```

This design means OpenWebUI thinks it's talking to an OpenAI-compatible model, but every response is actually RAG-grounded in the user's canon.

---

## 6. LLM Provider System

The LLM layer uses a **strategy pattern** with composition:

```
                    ┌─────────────────┐
                    │  LLMProvider     │  (abstract base class)
                    │                 │
                    │  + generate()   │
                    │  + embed()      │
                    │  + check_available() │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │                             │
    ┌─────────┴─────────┐       ┌───────────┴───────────┐
    │ AnthropicProvider  │       │   OpenAIProvider      │
    │                    │       │                       │
    │ generate() ✓       │       │ generate() ✗ (raises) │
    │ embed() ✗ (raises) │       │ embed() ✓             │
    │ check_available()  │       │ check_available()     │
    └────────────────────┘       └───────────────────────┘

                    ┌─────────────────┐
                    │   LLMService    │  (composition)
                    │                 │
                    │ generator ──────┼──▶ AnthropicProvider
                    │ embedder  ──────┼──▶ OpenAIProvider
                    │                 │
                    │ generate() ─────┼──▶ generator.generate()
                    │ embed()    ─────┼──▶ embedder.embed()
                    │ check_available()│──▶ both providers
                    └─────────────────┘
```

**Design rationale:** Each provider implements the full `LLMProvider` interface but raises `NotImplementedError` for capabilities it doesn't support. `LLMService` composes a generator and an embedder, routing calls to the correct provider. This allows mixing providers freely (e.g., Claude for generation, OpenAI for embeddings) and makes it straightforward to add new providers (Ollama is on the roadmap).

**Health checking:** `check_available()` makes a minimal real API call (a 1-token generation for Anthropic, a single-word embedding for OpenAI) to verify connectivity and valid credentials. Results are exposed at `/health`.

---

## 7. Data Architecture

### 7.1 PostgreSQL Schema

PostgreSQL stores all structured metadata. The schema is managed by Alembic async migrations that run automatically on each application startup.

```
┌──────────────────────┐
│      projects        │
├──────────────────────┤
│ id          VARCHAR(36) PK
│ name        VARCHAR(200) UNIQUE
│ description TEXT
│ created_at  DATETIME
│ updated_at  DATETIME
├──────────────────────┤
│ ◄── documents (1:N)
│ ◄── contradictions (1:N)
│ ◄── syntheses (1:N)
└──────────────────────┘

┌──────────────────────┐
│      documents       │
├──────────────────────┤
│ id            VARCHAR(36) PK
│ title         VARCHAR(500)
│ file_path     VARCHAR(1000)
│ status        VARCHAR(50)   ["pending", "processing", "completed", "failed"]
│ chunk_count   INTEGER
│ error_message TEXT (nullable)
│ project_id    VARCHAR(36) FK → projects.id
│ created_at    DATETIME
│ updated_at    DATETIME
└──────────────────────┘

┌───────────────────────────┐
│     contradictions        │
├───────────────────────────┤
│ id               VARCHAR(36) PK
│ project_id       VARCHAR(36) FK → projects.id (indexed)
│ chunk_a_id       VARCHAR(36)
│ chunk_b_id       VARCHAR(36)
│ document_a_id    VARCHAR(36) FK → documents.id
│ document_b_id    VARCHAR(36) FK → documents.id
│ document_a_title VARCHAR(500)
│ document_b_title VARCHAR(500)
│ chunk_a_text     TEXT
│ chunk_b_text     TEXT
│ explanation      TEXT
│ status           VARCHAR(50)   ["open", "resolved", "dismissed"]
│ resolution_note  TEXT (nullable)
│ resolved_at      DATETIME (nullable)
│ created_at       DATETIME
│ updated_at       DATETIME
└───────────────────────────┘

┌──────────────────────┐
│     syntheses        │
├──────────────────────┤
│ id              VARCHAR(36) PK
│ project_id      VARCHAR(36) FK → projects.id (indexed)
│ title           VARCHAR(500) default="World Primer"
│ outline         JSON (nullable)
│ outline_approved BOOLEAN default=false
│ content         TEXT (nullable)
│ status          VARCHAR(50)   ["outline_pending", ...]
│ error_message   TEXT (nullable)
│ created_at      DATETIME
│ updated_at      DATETIME
└──────────────────────┘
```

**Migration history:**
1. `20260301_2105_initial_schema.py` — documents table
2. `20260303_multi_project.py` — projects table + FK on documents
3. `20260404_contradictions.py` — contradictions table
4. `20260405_add_resolution_note.py` — resolution_note column
5. `20260405_syntheses.py` — syntheses table

### 7.2 Qdrant Vector Storage

Qdrant stores the embedded document chunks in a single collection:

```
Collection: "canon_documents"
  Vector config: 3072 dimensions, cosine distance

Point structure:
  id:      UUID string (matches chunk_id)
  vector:  float[3072] (text-embedding-3-large output)
  payload:
    text:         string   (full chunk text)
    document_id:  string   (FK to PostgreSQL documents.id)
    title:        string   (document title, denormalized)
    chunk_index:  integer  (position within the document)
    project_id:   string   (FK to PostgreSQL projects.id)
```

**Operations:**
- **Upsert** — bulk insert during document ingestion
- **Search** — cosine similarity with optional payload filter (e.g., `project_id`)
- **Scroll** — paginated retrieval by filter (used by contradiction service)
- **Delete** — by document_id (on document deletion) or by project_id (on project deletion)

### 7.3 Dual-Store Relationship

PostgreSQL and Qdrant are complementary stores with **document_id as the join key**:

```
PostgreSQL                           Qdrant
┌─────────────┐                     ┌─────────────────────┐
│ documents   │                     │ canon_documents      │
│             │   document_id       │                     │
│ id ─────────┼─────────────────────┼─▶ payload.document_id│
│ title       │                     │   payload.text      │
│ status      │                     │   payload.title     │
│ chunk_count │                     │   vector[3072]      │
│ project_id ─┼─────────────────────┼─▶ payload.project_id│
└─────────────┘                     └─────────────────────┘
```

When a document is deleted, both stores are cleaned up: Qdrant vectors are deleted by `document_id` filter, then the PostgreSQL record is removed. When a project is deleted, Qdrant vectors are deleted by `project_id` filter, then the project and its documents cascade-delete in PostgreSQL.

---

## 8. Multi-Project Scoping

Projects provide isolated knowledge bases within a single deployment. Every document and query is scoped to a project.

### Backend Scoping

- **API routes** nest under `/projects/{project_id}/...` for documents and queries
- **Qdrant payloads** include `project_id`, enabling filtered vector search
- **PostgreSQL** enforces the relationship via foreign keys with cascade delete
- **Legacy data migration:** On startup, `backfill_qdrant_project_ids()` scans all Qdrant points and assigns the default project ID (`00000000-0000-0000-0000-000000000001`) to any points missing a `project_id`

### Frontend Scoping

- **ProjectContext** holds the active project, persisted to `localStorage`
- **ProjectSelector** in the sidebar lets the user switch projects
- **React Query keys** include `projectId` (e.g., `["documents", projectId]`), so switching projects automatically refetches data
- **Page guards** show a prompt to select a project when none is active
- **API client** passes `projectId` as a path parameter on all project-scoped calls

---

## 9. Runtime Settings

API keys and model names can be changed at runtime via the Settings page, without restarting the container.

### Flow

```
User updates settings in UI
  │
  ▼
PUT /api/v1/settings { anthropic_api_key: "sk-new-..." }
  │
  ├─ Ignore values containing "***" (masked values sent back unchanged)
  ├─ Update in-memory Settings object
  ├─ Call reset_llm_service() → clears the singleton
  ├─ Call get_llm_service() → creates new providers with updated config
  ├─ Run check_available() → verify new credentials work
  └─ Return new settings (masked) + health status
```

### Key Masking

API keys are masked in GET responses using the pattern `sk-an***awAA` (first 5 + last 4 characters). On PUT, any value containing `***` is treated as "unchanged" and ignored. This prevents the UI from accidentally overwriting a valid key with its masked representation.

### Important Limitation

Settings changes are **runtime-only** — they are stored in the in-memory `Settings` object and will be lost on container restart. The container will revert to the environment variables defined in `docker-compose.yml` or `.env`.

---

## 10. Build and Packaging

### Backend Dependencies

Managed by **UV** (fast Python package manager). Key dependencies:

| Package          | Purpose                                     |
|------------------|---------------------------------------------|
| `fastapi`        | Web framework                               |
| `uvicorn`        | ASGI server                                 |
| `sqlalchemy[asyncio]` | ORM with async support                 |
| `asyncpg`        | Async PostgreSQL driver                     |
| `alembic`        | Database migrations                         |
| `pydantic-settings` | Environment-based configuration          |
| `anthropic`      | Claude API client                           |
| `openai`         | OpenAI API client (embeddings)              |
| `qdrant-client`  | Qdrant vector DB client                     |
| `llama-index-core` | SentenceSplitter for text chunking        |
| `pypdf`          | PDF text extraction                         |
| `tiktoken`       | Token counting for context assembly         |
| `aiofiles`       | Async file I/O                              |
| `loguru`         | Structured logging                          |

### Frontend Dependencies

Managed by **npm**. Key dependencies:

| Package                  | Purpose                          |
|--------------------------|----------------------------------|
| `react` + `react-dom`   | UI framework (v19)               |
| `react-router-dom`      | Client-side routing (v7)         |
| `@tanstack/react-query`  | Server state management (v5)    |
| `tailwindcss`            | Utility-first CSS (v4)          |
| `sonner`                 | Toast notifications              |
| Various `@radix-ui/*`    | Headless UI primitives (shadcn) |

### Build Commands

```bash
# Full stack (Docker)
docker compose up -d --build

# Backend only
cd backend && uv sync --all-groups
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8080

# Frontend dev
cd frontend && npm install && npm run dev

# Tests
cd backend && uv run pytest tests/ -v
cd backend && uv run pytest tests/ -v -m "not integration"
```

---

## 11. API Reference

### Health Check

```
GET /health

Response 200:
{
  "status": "healthy" | "degraded",
  "services": {
    "generator": true,
    "embedder": true
  }
}
```

### Projects

```
POST /api/v1/projects
Body: { "name": "My World", "description": "Optional" }
Response 200: { "id", "name", "description", "created_at", "updated_at" }

GET /api/v1/projects
Response 200: [{ "id", "name", "description", "document_count", "created_at", "updated_at" }]

GET /api/v1/projects/{project_id}
Response 200: { "id", "name", "description", "document_count", "created_at", "updated_at" }

PUT /api/v1/projects/{project_id}
Body: { "name": "New Name", "description": "New desc" }
Response 200: { "id", "name", "description", "updated_at" }

DELETE /api/v1/projects/{project_id}
Response 200: { "status": "deleted" }
```

### Documents (project-scoped)

```
POST /api/v1/projects/{project_id}/documents/upload
Body: multipart/form-data with "file" field
Response 200: { "id", "title", "status", "chunk_count", "project_id" }

GET /api/v1/projects/{project_id}/documents?skip=0&limit=50
Response 200: [{ "id", "title", "status", "chunk_count", "created_at" }]

GET /api/v1/projects/{project_id}/documents/{doc_id}
Response 200: { "id", "title", "status", "chunk_count", "file_path", "created_at", "error_message" }

DELETE /api/v1/projects/{project_id}/documents/{doc_id}
Response 200: { "status": "deleted" }
```

### Query (project-scoped)

```
POST /api/v1/projects/{project_id}/query
Body: { "question": "Who rules the Northern Kingdom?", "top_k": 10 }
Response 200: {
  "answer": "Based on the sources...",
  "citations": [
    { "document_id": "...", "title": "...", "chunk_text": "...", "relevance_score": 0.89 }
  ],
  "processing_time_ms": 2340
}
```

### Settings

```
GET /api/v1/settings
Response 200: {
  "anthropic_api_key": "sk-an***awAA",
  "openai_api_key": "sk-pr***j4Qm",
  "anthropic_model": "claude-sonnet-4-20250514",
  "openai_embedding_model": "text-embedding-3-large"
}

PUT /api/v1/settings
Body: { "anthropic_api_key": "sk-new-key-here" }
Response 200: {
  "settings": { ... },
  "health": { "status": "healthy", "services": { ... } }
}
```

### OpenAI-Compatible (for OpenWebUI)

```
POST /v1/chat/completions
Body: {
  "model": "canon-builder",
  "messages": [{"role": "user", "content": "Tell me about..."}],
  "temperature": 0.3,
  "project_id": "optional-project-uuid"
}
Response 200: (standard OpenAI chat completion format)

GET /v1/models
Response 200: { "object": "list", "data": [{ "id": "canon-builder", ... }] }
```

---

## 12. Design Decisions

### Why a single container for frontend + backend?

The user prioritizes easy packaging and sharing. A single `docker compose up` brings up the entire system. Having the frontend as static files served by FastAPI means one fewer service to manage, one fewer port to expose, and a simpler mental model. The trade-off is that frontend changes require a full image rebuild, but this is acceptable for a personal tool.

### Why separate LLM providers for generation and embeddings?

Anthropic's Claude excels at generation but doesn't offer an embedding API. OpenAI's `text-embedding-3-large` is best-in-class for embeddings. The provider abstraction lets each model do what it's best at, and the composition pattern in `LLMService` makes it easy to swap either independently (e.g., adding Ollama for local generation).

### Why Qdrant instead of pgvector?

Qdrant provides purpose-built vector search with payload filtering, which is essential for project-scoped queries. It also scales independently from PostgreSQL, keeping the metadata database lean. The async client integrates naturally with the async-throughout architecture.

### Why token-aware context assembly?

Naively concatenating all retrieved chunks risks overflowing the LLM's context window or wasting tokens on low-relevance content. The `_assemble_context()` method counts tokens with tiktoken and packs chunks in relevance order up to a configurable budget (4000 tokens). This ensures the most relevant sources always make it into the prompt.

### Why runtime-only settings (not persisted to .env)?

Simplicity over persistence. Runtime settings let you quickly test different API keys or models without modifying files. The container restarts with known-good configuration from environment variables, providing a reliable fallback. For permanent changes, users update their `.env` file directly.

### Why no authentication?

This is a single-user personal tool. Auth adds complexity without value for the target use case. It's deferred to Phase 4 of the roadmap for when multi-user support is added.

### Why fire-and-forget contradiction scanning?

Contradiction detection is computationally expensive (it compares every new chunk against all existing project chunks via LLM calls). Running it synchronously would make document uploads unacceptably slow. Using `asyncio.create_task()` lets the upload return immediately while scanning continues in the background. The trade-off is that contradictions won't appear instantly after upload, but this is acceptable since contradiction review is not time-critical.

### Why SentenceSplitter (LlamaIndex) for chunking?

`SentenceSplitter` respects sentence boundaries when splitting text, producing more coherent chunks than fixed-character splitting. This improves both embedding quality and the readability of cited source passages. The 512-token chunk size with 50-token overlap balances granularity against context.
