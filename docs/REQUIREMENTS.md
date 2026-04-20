# WorldForge — Requirements (v1.0.0)

**Reflects the actual Phase 1 implementation as shipped.**
**Last updated:** 2026-04-15

---

## 1. Functional Requirements

### FR-1: Multi-Project Support
**Priority:** P0 (Critical)

#### FR-1.1 Project CRUD
- **REQ:** System SHALL support creating projects with a name and optional description.
- **REQ:** System SHALL support listing, updating, and deleting projects.
- **REQ:** Deleting a project SHALL cascade-delete all associated documents, contradictions, syntheses, and vector data.
- **Acceptance:** All CRUD operations functional via API and UI. Cascade delete verified.

#### FR-1.2 Project Isolation
- **REQ:** Documents, contradictions, syntheses, and vector search results SHALL be scoped to the active project.
- **REQ:** The frontend SHALL persist the active project selection in localStorage.
- **Acceptance:** Switching projects shows only that project's data. No cross-project data leakage.

---

### FR-2: Document Ingestion
**Priority:** P0 (Critical)

#### FR-2.1 File Format Support
- **REQ:** System SHALL support document upload in the following formats:
  - Plain text (.txt)
  - Markdown (.md)
  - PDF (.pdf)
- **Acceptance:** All three formats successfully parsed, chunked, embedded, and queryable.

#### FR-2.2 Document Processing Pipeline
- **REQ:** System SHALL process uploaded documents through the following pipeline:
  1. Extract text from file (plain read for txt/md, PyPDF for PDF)
  2. Chunk text using LlamaIndex SentenceSplitter (512 tokens per chunk, 50 token overlap)
  3. Generate embeddings using OpenAI text-embedding-3-large (3072 dimensions)
  4. Upsert embeddings into Qdrant with metadata (text, document_id, title, chunk_index, project_id)
  5. Update document record in PostgreSQL with status and chunk_count
- **REQ:** If embedding or vector storage fails, database records SHALL be rolled back and document status set to "failed" with an error message.
- **Acceptance:** End-to-end pipeline completes. Failed documents show error state, not partial data.

#### FR-2.3 Document Management
- **REQ:** System SHALL support listing documents (with pagination), viewing document details, and deleting documents.
- **REQ:** Deleting a document SHALL remove its vectors from Qdrant and its database record.
- **Acceptance:** CRUD operations functional. Deleted documents no longer appear in search results.

#### FR-2.4 Bulk Upload
- **REQ:** A CLI script (`scripts/bulk_upload.py`) SHALL support uploading a folder of .txt, .md, and .pdf files to a specified project.
- **REQ:** The script SHALL create the project if it does not exist.
- **Acceptance:** Script uploads all supported files in a directory and skips unsupported formats.

---

### FR-3: Semantic Query with Citations
**Priority:** P0 (Critical)

#### FR-3.1 Natural Language Query
- **REQ:** System SHALL accept natural language queries about the canon.
- **REQ:** System SHALL return contextually relevant answers with source citations.
- **REQ:** Citations SHALL include document title and relevance score.
- **Acceptance:** User can ask questions and receive grounded answers with citations.

#### FR-3.2 Query Processing Pipeline
- **REQ:** System SHALL process queries using the following workflow:
  1. Generate query embedding via OpenAI
  2. Perform similarity search in Qdrant (configurable top_k, default 10, max 50)
  3. Assemble context from retrieved chunks, respecting a token limit (default 4000 tokens)
  4. Generate answer via Anthropic Claude with inline citations
- **Acceptance:** Pipeline executes successfully. Answers reference source material.

#### FR-3.3 Token-Aware Context Assembly
- **REQ:** Context assembly SHALL respect the configured token limit and include as many relevant chunks as fit.
- **Acceptance:** Large retrieval sets are truncated to fit within the token budget without error.

---

### FR-4: Contradiction Detection
**Priority:** P0 (Critical)

#### FR-4.1 Automatic Detection on Upload
- **REQ:** After a document is successfully ingested, the system SHALL automatically scan for contradictions in the background.
- **REQ:** For each chunk in the new document, the system SHALL retrieve the top-5 semantically similar chunks from other documents in the same project.
- **REQ:** For each candidate pair, the system SHALL call the LLM to classify whether they contradict each other.
- **REQ:** If the LLM confirms a contradiction, the system SHALL insert a record with both chunk texts (snapshots), source document references, and the LLM's explanation.
- **REQ:** The system SHALL deduplicate — the same chunk pair (in either order) SHALL NOT produce duplicate contradiction records.
- **REQ:** The system SHALL skip pairs where both chunks belong to the same document.
- **Acceptance:** Uploading a document with contradictory content produces contradiction records. No duplicates. No same-document false positives.

#### FR-4.2 Manual Full-Project Scan
- **REQ:** `POST /api/v1/projects/{project_id}/contradictions/scan` SHALL trigger a full-project scan.
- **REQ:** The endpoint SHALL return 202 Accepted immediately; scanning runs in the background.
- **Acceptance:** Endpoint returns 202. New contradictions appear after scan completes.

#### FR-4.3 Contradiction Management
- **REQ:** Users SHALL be able to resolve, dismiss, or reopen contradictions.
- **REQ:** Resolve and dismiss actions SHALL accept an optional resolution note.
- **REQ:** Bulk operations SHALL allow updating multiple contradictions at once.
- **REQ:** The UI SHALL group contradictions by document pair with collapsible sections.
- **REQ:** The UI SHALL provide filter tabs for open, resolved, and dismissed contradictions.
- **Acceptance:** All status transitions work. Notes are persisted. Bulk operations update multiple records. UI reflects current state.

---

### FR-5: World Synthesis
**Priority:** P1 (High)

#### FR-5.1 Contradiction Gate
- **REQ:** Synthesis generation SHALL be blocked if any open contradictions exist in the project.
- **REQ:** The UI SHALL show the count of open contradictions and link to the contradictions page when the gate blocks.
- **Acceptance:** Cannot start synthesis with open contradictions. Clear error message displayed.

#### FR-5.2 Outline Generation
- **REQ:** System SHALL generate an outline by batching all project chunks, extracting topics via LLM, and consolidating into 8-15 ordered sections.
- **REQ:** Each section SHALL have a title and one-line description.
- **REQ:** Outline generation SHALL run as a background task (API returns 202).
- **Acceptance:** Outline appears after background processing. Sections are relevant to project content.

#### FR-5.3 Outline Review
- **REQ:** Users SHALL be able to view, edit (reorder, add, remove, rename sections), and approve the outline before generation proceeds.
- **REQ:** A "Quick Generate" mode SHALL skip outline approval and proceed directly to section generation.
- **Acceptance:** Outline edits are persisted. Approval triggers section generation. Quick mode skips approval.

#### FR-5.4 Section Generation
- **REQ:** For each approved section, the system SHALL retrieve relevant chunks from Qdrant and generate a narrative section via LLM.
- **REQ:** Resolution notes from resolved/dismissed contradictions SHALL be included in the prompt so the LLM knows which version of disputed facts to prefer.
- **REQ:** All sections SHALL be assembled into a single markdown document.
- **Acceptance:** Completed synthesis contains all sections as formatted markdown.

#### FR-5.5 Synthesis Management
- **REQ:** Users SHALL be able to list past syntheses, view completed content, download as .md, and retry failed syntheses.
- **REQ:** The UI SHALL poll for status updates during generation (every 5 seconds).
- **Acceptance:** Status polling shows progress. Download produces valid markdown file. Retry resets to outline state.

---

### FR-6: OpenAI-Compatible API
**Priority:** P1 (High)

#### FR-6.1 Chat Completions Endpoint
- **REQ:** `POST /v1/chat/completions` SHALL accept OpenAI-format chat requests and return OpenAI-format responses.
- **REQ:** The endpoint SHALL support a `project_id` parameter to scope queries to a specific project.
- **Acceptance:** OpenWebUI or any OpenAI-compatible client can connect and query the canon.

#### FR-6.2 Models Endpoint
- **REQ:** `GET /v1/models` SHALL return a model list including "canon-builder".
- **Acceptance:** Endpoint returns valid OpenAI-format model list.

---

### FR-7: Settings Management
**Priority:** P1 (High)

#### FR-7.1 Runtime Configuration
- **REQ:** Users SHALL be able to view and update API keys and model names at runtime via `GET/PUT /api/v1/settings`.
- **REQ:** API keys SHALL be masked in GET responses (showing only last 4 characters).
- **REQ:** Updating settings SHALL reset the LLM service singleton so new providers are created with updated config.
- **REQ:** The settings UI SHALL display service health status (generator and embedder) after saving.
- **Acceptance:** Settings save successfully. Masked keys displayed. Service health reflects actual provider status.

---

## 2. Non-Functional Requirements

### NFR-1: Performance

#### NFR-1.1 Query Latency
- **REQ:** Query response time SHOULD be < 10 seconds under normal conditions (single user, typical corpus).
- **Note:** Actual latency depends on LLM provider response time, which is outside system control.

#### NFR-1.2 Ingestion Throughput
- **REQ:** System SHALL handle documents of at least 100 pages.
- **Note:** Ingestion time depends on embedding API throughput. No hard latency target for v1.

---

### NFR-2: Reliability

#### NFR-2.1 Data Integrity
- **REQ:** Failed ingestion SHALL roll back database records (document status set to "failed").
- **REQ:** Contradiction records SHALL use text snapshots so they remain readable even if source documents are deleted (FK set to NULL on delete).

#### NFR-2.2 Error Handling
- **REQ:** Invalid file formats SHALL produce clear error messages.
- **REQ:** LLM or embedding API failures during ingestion SHALL result in "failed" document status with error details.
- **REQ:** Background tasks (contradiction scan, synthesis generation) SHALL handle errors gracefully and record failure state.

#### NFR-2.3 Background Task Isolation
- **REQ:** Background tasks SHALL create their own database sessions (not rely on request-scoped sessions).
- **REQ:** Background task failures SHALL NOT crash the application or affect other requests.

---

### NFR-3: Usability

#### NFR-3.1 Setup
- **REQ:** System SHALL start with a single `docker compose up -d` command.
- **REQ:** System SHALL provide a `.env.example` template with all configuration options.

#### NFR-3.2 Frontend
- **REQ:** Frontend SHALL provide clear loading states, error messages, and toast notifications.
- **REQ:** Frontend SHALL persist active project selection across page reloads.
- **REQ:** Chat input SHALL support Enter to send and Shift+Enter for newline.

---

### NFR-4: Security

#### NFR-4.1 Data Privacy
- **REQ:** All user data SHALL remain on the user's own infrastructure.
- **REQ:** External API calls (Anthropic, OpenAI) are limited to LLM generation and embedding — no bulk data export.
- **REQ:** API keys SHALL be masked in API responses and the UI.

#### NFR-4.2 Authentication
- **Status:** Deferred to Phase 7. No auth in v1 — this is a single-user, self-hosted tool.

---

### NFR-5: Maintainability

#### NFR-5.1 Code Quality
- **REQ:** Backend SHALL have a test suite runnable via `uv run pytest tests/ -v`.
- **REQ:** Frontend SHALL have a test suite runnable via `npm run test`.
- **REQ:** API SHALL have OpenAPI documentation (auto-generated by FastAPI at `/docs`).

#### NFR-5.2 CI/CD
- **REQ:** GitHub Actions SHALL run backend tests, frontend tests (lint + typecheck + unit), and Docker build on PRs.
- **REQ:** Docker images SHALL be pushed to GHCR on push to main and on version tags.

#### NFR-5.3 Modularity
- **REQ:** LLM providers SHALL be swappable via configuration (Anthropic for generation, OpenAI for embeddings). All providers implement the same abstract interface.
- **REQ:** Services SHALL be injected via FastAPI dependency injection, not hardcoded.

---

## 3. Technical Requirements

### TR-1: Software Stack

| Component | Technology |
|-----------|-----------|
| Backend language | Python 3.11+ |
| Web framework | FastAPI |
| Frontend | React 19, Vite, TypeScript, Tailwind CSS v4, shadcn/ui |
| Database | PostgreSQL (async via asyncpg + SQLAlchemy 2.0) |
| Migrations | Alembic (async) |
| Vector DB | Qdrant (async client) |
| LLM generation | Anthropic Claude (claude-sonnet-4-20250514 default) |
| Embeddings | OpenAI text-embedding-3-large (3072 dimensions) |
| Document parsing | PyPDF (PDF), plain read (txt/md) |
| Chunking | LlamaIndex SentenceSplitter |
| State management | TanStack React Query v5 |
| Routing | React Router v7 |
| Package managers | UV (backend), npm (frontend) |
| Containerization | Docker Compose (4 services: API, PostgreSQL, Qdrant, OpenWebUI) |

### TR-2: Deployment

#### TR-2.1 Docker Compose
- **REQ:** System SHALL deploy via `docker compose up -d`.
- **REQ:** Multi-stage Dockerfile SHALL build frontend and backend into a single image.
- **REQ:** FastAPI SHALL serve the built frontend as a SPA with catch-all routing (API routes registered first for priority).

#### TR-2.2 Service Ports
| Service | Port |
|---------|------|
| API + Frontend | 8080 |
| OpenWebUI | 3000 |
| Qdrant | 6333 |
| PostgreSQL | 5432 |
| Vite dev server | 5173 (dev only, proxies to 8080) |

#### TR-2.3 Environment Configuration
- **REQ:** System SHALL use environment variables for configuration via pydantic-settings.
- **REQ:** `.env.example` SHALL document all configuration options with defaults.

### TR-3: API Design

#### TR-3.1 REST Endpoints

**Projects:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/projects/{id}` | Get project |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project + cascade |

**Documents** (project-scoped):
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/projects/{pid}/documents/upload` | Upload document |
| GET | `/api/v1/projects/{pid}/documents` | List documents |
| GET | `/api/v1/projects/{pid}/documents/{id}` | Get document |
| DELETE | `/api/v1/projects/{pid}/documents/{id}` | Delete document |

**Query** (project-scoped):
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/projects/{pid}/query` | RAG query with citations |

**Contradictions** (project-scoped):
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/projects/{pid}/contradictions` | List (filter by status) |
| POST | `/api/v1/projects/{pid}/contradictions/scan` | Trigger full scan (202) |
| PATCH | `/api/v1/projects/{pid}/contradictions/{id}/resolve` | Resolve |
| PATCH | `/api/v1/projects/{pid}/contradictions/{id}/dismiss` | Dismiss |
| PATCH | `/api/v1/projects/{pid}/contradictions/{id}/reopen` | Reopen |
| POST | `/api/v1/projects/{pid}/contradictions/bulk` | Bulk update |

**Synthesis** (project-scoped):
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/projects/{pid}/synthesis` | Create (auto=true for quick) |
| GET | `/api/v1/projects/{pid}/synthesis` | List syntheses |
| GET | `/api/v1/projects/{pid}/synthesis/{id}` | Get synthesis |
| PATCH | `/api/v1/projects/{pid}/synthesis/{id}/outline` | Edit outline |
| POST | `/api/v1/projects/{pid}/synthesis/{id}/approve` | Approve outline |
| GET | `/api/v1/projects/{pid}/synthesis/{id}/download` | Download .md |
| POST | `/api/v1/projects/{pid}/synthesis/{id}/retry` | Retry failed |

**Settings:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/settings` | Get settings (masked keys) |
| PUT | `/api/v1/settings` | Update settings |

**OpenAI-compatible:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat/completions` | Chat completions |
| GET | `/v1/models` | List models |

**Health:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |

#### TR-3.2 API Standards
- **REQ:** All APIs SHALL have OpenAPI 3.0 documentation (auto-generated at `/docs`).
- **REQ:** All APIs SHALL use proper HTTP status codes (200, 201, 202, 400, 404, 409, 500).

### TR-4: Data Model

#### TR-4.1 Database Tables

**projects:**
| Column | Type | Notes |
|--------|------|-------|
| id | String(36) | PK, UUID |
| name | String(200) | Unique |
| description | Text | Nullable |
| created_at | DateTime | |
| updated_at | DateTime | |

**documents:**
| Column | Type | Notes |
|--------|------|-------|
| id | String(36) | PK, UUID |
| title | String(500) | |
| file_path | String(1000) | |
| status | String(50) | pending / processing / completed / failed |
| chunk_count | Integer | |
| error_message | Text | Nullable |
| project_id | String(36) | FK → projects, cascade delete |
| created_at | DateTime | |
| updated_at | DateTime | |

**contradictions:**
| Column | Type | Notes |
|--------|------|-------|
| id | String(36) | PK, UUID |
| project_id | String(36) | FK → projects, cascade delete, indexed |
| chunk_a_id | String(36) | Qdrant point ID |
| chunk_b_id | String(36) | Qdrant point ID |
| document_a_id | String(36) | FK → documents, SET NULL on delete, nullable |
| document_b_id | String(36) | FK → documents, SET NULL on delete, nullable |
| document_a_title | String(500) | Snapshot |
| document_b_title | String(500) | Snapshot |
| chunk_a_text | Text | Snapshot |
| chunk_b_text | Text | Snapshot |
| explanation | Text | LLM explanation |
| status | String(50) | open / resolved / dismissed |
| resolution_note | Text | Nullable |
| resolved_at | DateTime | Nullable |
| created_at | DateTime | |
| updated_at | DateTime | |

**syntheses:**
| Column | Type | Notes |
|--------|------|-------|
| id | String(36) | PK, UUID |
| project_id | String(36) | FK → projects, cascade delete, indexed |
| title | String(500) | Default: "World Primer" |
| outline | JSON | Nullable, list of {title, description} |
| outline_approved | Boolean | Default false |
| content | Text | Nullable, final markdown |
| status | String(50) | outline_pending / outline_ready / outline_approved / generating / completed / failed |
| error_message | Text | Nullable |
| created_at | DateTime | |
| updated_at | DateTime | |

#### TR-4.2 Vector Storage
- **Collection:** "canon_documents"
- **Dimensions:** 3072
- **Distance metric:** Cosine
- **Payload fields:** text, document_id, title, chunk_index, project_id

---

## 4. Frontend Requirements

### FE-1: Pages

| Page | Route | Purpose |
|------|-------|---------|
| Chat | `/` | Query canon, view answers with citations |
| Documents | `/documents` | Upload, list, delete documents |
| Contradictions | `/contradictions` | View, resolve, dismiss contradictions |
| Synthesis | `/synthesis` | Generate, review, download world primers |
| Projects | `/projects` | Create, manage, switch projects |
| Settings | `/settings` | Configure API keys, models, view health |

### FE-2: Key Interactions

- **Document upload:** Drag-and-drop or click-to-upload. Multi-file support. Progress/status feedback.
- **Chat:** Enter to send, Shift+Enter for newline. Messages show citations with document titles and relevance scores.
- **Contradictions:** Grouped by document pair. Collapsible groups. Bulk resolve/dismiss. Individual resolve/dismiss with optional notes. Reopen. Filter tabs (open/resolved/dismissed).
- **Synthesis:** Gate check against open contradictions. Two modes (full with outline review, quick auto). Outline editor with reorder/add/remove. Status polling during generation. Markdown viewer. Download.
- **Project switching:** Dropdown selector in sidebar. Persists across reloads.
- **Health indicator:** Colored dot in sidebar (green/yellow/red) with polling every 30 seconds.

---

## 5. Deferred Requirements

The following requirements from the original design doc are **not implemented in v1.0.0** and have been moved to the [Roadmap](ROADMAP.md):

| Original Requirement | Roadmap Phase |
|---------------------|---------------|
| DOCX file format support | Phase 2 |
| Contradiction severity (HIGH/MEDIUM/LOW) | Phase 2 |
| "No information" response for out-of-canon queries | Phase 2 |
| Query history | Phase 2 |
| Entity extraction | Phase 3 |
| Knowledge graph (Neo4j) | Phase 3 |
| Graph-enhanced hybrid search | Phase 3 |
| Review queue (approve/reject proposals) | Phase 4 |
| AI-generated canon proposals | Phase 4 |
| Obsidian export | Phase 5 |
| PDF export | Phase 5 |
| Ollama local LLM support | Phase 6 |
| Local embedding models (BGE) | Phase 6 |
| Offline capability | Phase 6 |
| Authentication & multi-user | Phase 7 |
| Automated backups | Phase 8 |
| Monitoring (Prometheus/Grafana) | Phase 8 |
| Load testing / concurrent user support | Phase 8 |

---

**Document Control:**
- **Version:** 2.0
- **Reflects:** v1.0.0 as shipped
- **Author:** Alex Barclay
- **Last Updated:** 2026-04-15
