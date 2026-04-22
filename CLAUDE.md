# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canon Builder is a RAG-powered worldbuilding knowledge system. It is a single-user personal tool that lets you upload documents (text, markdown, PDF), chunk and embed them, then query your knowledge base with AI-generated answers grounded in your canon. Uses Anthropic (Claude) for generation and OpenAI for embeddings.

## Tech Stack

- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS v4, shadcn/ui, React Router v7, TanStack React Query v5
- **Backend**: FastAPI, SQLAlchemy 2.0 (async with asyncpg), Pydantic v2, pydantic-settings
- **Vector DB**: Qdrant (async client)
- **LLM**: Anthropic SDK (generation), OpenAI SDK (embeddings)
- **Parsing**: LlamaIndex (SentenceSplitter), PyPDF
- **Database**: PostgreSQL (asyncpg), Alembic (async migrations)
- **Package Manager**: UV (backend), npm (frontend)
- **Infrastructure**: Docker Compose (4 services: API, PostgreSQL, Qdrant, OpenWebUI). Multi-stage Dockerfile builds frontend and backend into a single image.

## Build & Run Commands

```bash
# Install all dependencies (including dev/test)
cd backend && uv sync --all-groups
cd frontend && npm install

# Start all services (builds frontend + backend into single container)
docker compose up -d --build

# Run backend tests
cd backend && uv run pytest tests/ -v

# Skip integration tests
cd backend && uv run pytest tests/ -v -m "not integration"

# Run a single test
cd backend && uv run pytest tests/test_basic.py::test_health_check -v

# Frontend dev server (proxies API to backend on 8080)
cd frontend && npm run dev

# Frontend production build
cd frontend && npm run build

# Apply database migrations
cd backend && uv run alembic upgrade head
```

**Service ports**: API + Frontend 8080, OpenWebUI 3000, Qdrant 6333, PostgreSQL 5432
**Dev ports**: Vite dev server 5173 (proxies to backend 8080)

## Architecture

```
frontend/src/
├── components/
│   ├── layout/            Shell, Sidebar, HealthIndicator
│   ├── chat/              ChatView, MessageBubble, ChatInput
│   ├── documents/         UploadDropzone, DocumentCard
│   └── ui/                shadcn/ui components (button, card, input, etc.)
├── hooks/                 useChat, useDocuments, useHealth, useSettings
├── lib/
│   └── api.ts             Typed fetch wrapper for all backend endpoints
├── pages/                 ChatPage, DocumentsPage, SettingsPage
└── App.tsx                Router + QueryClient + Shell layout

backend/app/
├── api/v1/              Route handlers
│   ├── documents.py       Document CRUD (upload, list, get, delete)
│   ├── query.py           RAG query endpoint
│   ├── settings.py        Runtime config GET/PUT with key masking
│   └── openai_compat.py   OpenAI-compatible /v1/chat/completions for OpenWebUI
├── models/
│   ├── database.py        Async engine, session factory, get_db dependency
│   ├── schemas.py         Pydantic request/response models
│   └── repositories.py    SQLAlchemy document repository
├── services/
│   ├── llm/               LLM provider abstraction
│   │   ├── base.py          Abstract LLMProvider interface
│   │   ├── anthropic_provider.py  Claude implementation
│   │   ├── openai_provider.py     OpenAI implementation
│   │   └── service.py        LLMService (provider management)
│   ├── ingestion_service.py  Chunking + embedding + vector storage
│   ├── rag_service.py        Query + context assembly + generation
│   └── qdrant_service.py     Vector storage and similarity search
├── core/
│   └── config.py          Pydantic Settings (env-based configuration)
├── dependencies.py        Singleton services via FastAPI Depends
└── main.py                App factory with lifespan, SPA static serving
```

## Key Patterns

- **SPA served by FastAPI**: In production, Vite builds to `frontend/dist/`, the Dockerfile copies it to `frontend_dist/` inside the image, and FastAPI mounts it with a catch-all route for client-side routing. API routes are registered first so they take priority.
- **React Query for server state**: All API data (documents, health, settings) is managed via TanStack React Query hooks. Local state only for chat messages.
- **Runtime settings**: API keys and model names can be changed at runtime via `PUT /api/v1/settings`. This resets the LLM service singleton (`reset_llm_service()` in `dependencies.py`) so new providers are created with updated config.
- **LLM provider interface**: Swap between Anthropic/OpenAI/Ollama via config. All providers implement the same abstract base class (`LLMProvider`).
- **Dependency injection**: Services are singletons created at startup and injected into route handlers via `backend/app/dependencies.py` and FastAPI `Depends()`.
- **Token-aware RAG context**: Context assembly respects token limits when building prompts from retrieved chunks.
- **Rollback on ingestion failure**: If embedding or vector storage fails, database records are rolled back.
- **Async throughout**: All database, vector DB, and LLM calls are async.

## Configuration

Environment-based via pydantic-settings (`backend/app/core/config.py`).

**Required**:
- `ANTHROPIC_API_KEY` — for Claude generation
- `OPENAI_API_KEY` — for text-embedding-3-large embeddings

See `.env.example` for all options. Defaults work for Docker Compose deployment.

## Auth

No authentication — this is a single-user personal tool. Auth is deferred to roadmap Phase 4.

## Migrations

Alembic async migrations live in `backend/alembic/`. Run with `cd backend && uv run alembic upgrade head`.

## Launch Status

Pre-launch work (demo recording, launch posts, Reddit ramp) is tracked in [`docs/LAUNCH_TODOS.md`](docs/LAUNCH_TODOS.md). Check there first for what's outstanding before v1.0.0 ships.
