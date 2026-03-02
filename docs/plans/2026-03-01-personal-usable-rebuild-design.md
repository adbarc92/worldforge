# Canon Builder: Personal Usable State — Design Document

**Date**: 2026-03-01
**Goal**: Rebuild the API and service layer so a single user can upload text/md/PDF documents, query them with RAG-powered answers, and interact via OpenWebUI.

## Decisions

- **Cloud APIs**: Anthropic (Claude) for generation, OpenAI for embeddings
- **LLM abstraction**: Provider interface so Ollama swaps in later via config change
- **All async**: asyncpg, AsyncQdrantClient, httpx.AsyncClient — no sync blocking
- **No auth**: Single-user personal use, auth deferred to Phase 4
- **Trimmed infrastructure**: 4 Docker services (postgres, qdrant, canon_api, openwebui)
- **UV + pyproject.toml**: Replaces pip + requirements.txt
- **Alembic**: Replaces raw SQL migration mounted into postgres
- **No stubs**: Only endpoints that work. No 501 placeholders.
- **OpenWebUI**: Connected via OpenAI-compatible `/v1/chat/completions` endpoint

## 1. LLM Provider Abstraction

```
LLMProvider (abstract)
├── generate(prompt, system_prompt, temperature, max_tokens) → str
├── embed(texts: list[str]) → list[list[float]]
└── check_available() → bool

AnthropicProvider
├── Uses anthropic SDK
├── Model configurable (default: claude-sonnet-4-20250514)
└── Implements generate() and check_available()

OpenAIProvider
├── Uses openai SDK
├── Model configurable (default: text-embedding-3-large, 3072-dim)
└── Implements embed() and check_available()

OllamaProvider (future)
├── Implements all three methods
└── Drop-in replacement via config

LLMService (composition)
├── generator: LLMProvider  (Anthropic)
├── embedder: LLMProvider   (OpenAI)
└── Routes calls to the right provider
```

## 2. Data Layer

```
AsyncSessionLocal (SQLAlchemy async engine + asyncpg)
├── get_db() → async dependency, yields session per request

Repositories
├── DocumentRepository
│   ├── create(title, file_path, status) → Document
│   ├── get(id) → Document | None
│   ├── list(skip, limit) → list[Document]
│   ├── update_status(id, status, chunk_count) → Document
│   └── delete(id) → None
```

- Alembic async migrations, run on app startup
- Existing SQLAlchemy models retained, adapted for async sessions

## 3. Service Layer

```
IngestionService (async)
├── Dependencies: LLMService, QdrantService, DocumentRepository
├── process_document(file_path, title) → Document
│   1. Detect format (text/md/pdf)
│   2. Extract text (plain read or PyPDF)
│   3. Chunk via LlamaIndex SentenceSplitter
│   4. Embed all chunks in batches via LLMService.embed()
│   5. Store vectors in Qdrant with metadata
│   6. Update document record in PostgreSQL
│   7. On failure → rollback partial data
└── delete_document(id) → cleanup Qdrant + PostgreSQL

QdrantService (async)
├── AsyncQdrantClient
├── Embedding dim from config (not hardcoded)
├── search(), upsert(), delete_by_document()

RAGService (async)
├── Dependencies: LLMService, QdrantService
├── query(question, top_k=10) → QueryResponse
│   1. Embed question
│   2. Semantic search in Qdrant
│   3. Token-aware context assembly (tiktoken)
│   4. Generate answer via Claude with grounding prompt
│   5. Return answer + citations
```

Neo4j deferred entirely — not needed for upload + query.

## 4. API Routes

```
GET  /health                    → ping all services
POST /api/v1/documents/upload   → IngestionService.process_document()
GET  /api/v1/documents          → DocumentRepository.list()
GET  /api/v1/documents/{id}     → DocumentRepository.get()
DELETE /api/v1/documents/{id}   → IngestionService.delete_document()
POST /api/v1/query              → RAGService.query()
POST /v1/chat/completions       → OpenAI-compatible wrapper for OpenWebUI
```

Startup: initialize DB engine, run migrations, verify all services reachable. Fail fast.
Shutdown: close DB engine and HTTP clients.

## 5. Infrastructure

**Docker Compose** (4 services):
- postgres (16-alpine)
- qdrant
- canon_api (FastAPI)
- openwebui

Removed: ollama, neo4j, unstructured, prometheus, grafana.

**Dockerfile**:
- python:3.11-slim, non-root user, no --reload
- UV for dependency management
- Built-in health check

**Configuration** (Pydantic Settings):
- Required: ANTHROPIC_API_KEY, OPENAI_API_KEY, DATABASE_URL
- Optional with defaults: QDRANT_URL, models, chunk params, top_k

## 6. Testing

- Unit: LLM providers (mocked), ingestion pipeline, RAG context assembly
- Integration: upload → verify in Qdrant + Postgres, upload → query → answer, upload → delete → cleanup
- pytest + pytest-asyncio + httpx async test client

## 7. Roadmap

| Phase | Scope |
|-------|-------|
| **2: Knowledge Graph** | Neo4j async service, entity extraction, graph-enhanced RAG, Obsidian sync |
| **3: Proposals & Consistency** | AI canon extensions, review workflow, contradiction detection, audit logging |
| **4: Multi-User & Auth** | Registration, JWT, per-user isolation, rate limiting, secrets management |
| **5: Advanced** | Ollama support, Unstructured.io parsing, monitoring, export, collaboration |

## What Gets Rewritten

- All services (async-native, error handling, rollback)
- All routes (only working endpoints)
- Config (required vs optional, no hardcoded secrets)
- Dockerfile (production-ready)
- Docker Compose (4 services)
- Dependencies (UV + pyproject.toml)
- Migrations (Alembic)

## What Stays

- SQLAlchemy model definitions (adapted for async)
- Obsidian vault template
- Project documentation (README, SETUP, IMPLEMENTATION_SUMMARY)
