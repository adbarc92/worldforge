# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canon Builder is a self-hosted tool for constructing logically coherent knowledge systems, primarily for worldbuilding (fiction, games, TTRPGs). It uses a RAG pipeline with human-in-the-loop canonization — all AI-generated content requires explicit user approval before becoming canon.

**Phase**: MVP foundation. Core service scaffolding is in place; many service implementations have TODO markers for full pipeline integration.

## Tech Stack

- **Backend**: FastAPI (Python 3.11) with SQLAlchemy ORM, Pydantic schemas, JWT auth
- **AI/RAG**: LlamaIndex (chunking/indexing), LangGraph (agent orchestration), Ollama (local LLM: llama3.1:70b, embeddings: bge-large-en-v1.5)
- **Storage**: Qdrant (vectors, 1024-dim BGE, cosine), Neo4j (knowledge graph), PostgreSQL (metadata/audit)
- **Infrastructure**: Docker Compose orchestration, OpenWebUI for chat interface, optional Prometheus/Grafana monitoring

## Build & Run Commands

```bash
# Start all services
docker-compose up -d

# Pull required LLM models (after Ollama container is running)
docker exec -it canon_ollama ollama pull llama3.1:70b
docker exec -it canon_ollama ollama pull bge-large-en-v1.5

# Start with monitoring stack
docker-compose --profile monitoring up -d

# Run tests
cd backend && pytest tests/ -v --cov=app

# Run a single test
cd backend && pytest tests/test_basic.py::test_health_check -v

# Check API health
curl http://localhost:8080/health

# Get auth token (demo user)
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'
```

**Service ports**: API 8080, OpenWebUI 3000, Neo4j 7474/7687, Qdrant 6333, PostgreSQL 5432, Ollama 11434

## Architecture

```
User Interfaces (Obsidian vault, OpenWebUI, REST API)
        ↓
FastAPI Backend (backend/app/)
  ├── api/v1/         → Route handlers (auth, documents, query, proposals, graph, consistency)
  ├── core/           → Config (env-based settings), Security (JWT, bcrypt)
  ├── models/         → database.py (SQLAlchemy ORM), schemas.py (Pydantic)
  └── services/       → Business logic layer
        ├── ingestion_service.py   → Document parse → chunk → embed → store
        ├── rag_service.py         → Hybrid search (semantic + keyword + graph) → LLM answer
        ├── entity_service.py      → LLM-based entity/relationship extraction → Neo4j
        ├── ollama_service.py      → LLM generation and embedding via httpx
        ├── qdrant_service.py      → Vector storage/search (collection: "canon_documents")
        └── neo4j_service.py       → Knowledge graph CRUD
        ↓
Data Layer (Qdrant, Neo4j, PostgreSQL, Filesystem)
        ↓
Ollama (local LLM runtime, GPU optional)
```

## Key Design Patterns

- **Canon vs Proposed**: All content has a `CanonStatus` (canonical/proposed/rejected). AI output starts as "proposed" and requires human review via the proposals API.
- **Dependency injection**: Services are injected into route handlers via FastAPI `Depends()`.
- **Hybrid search**: RAG queries combine semantic (Qdrant vectors), keyword (BM25), and graph (Neo4j traversal) results.
- **Audit trail**: All canonization actions are logged to `audit_logs` table with JSONB details.

## Configuration

All config is environment-based via `backend/app/core/config.py` (Pydantic Settings). Key vars are in `.env.example`. RAG parameters: `CHUNK_SIZE=512`, `CHUNK_OVERLAP=50`, `TOP_K_RETRIEVAL=10`.

## Database

- Schema defined in `backend/migrations/001_initial_schema.sql` (auto-applied on postgres container start)
- Key tables: users, documents, proposals, contradictions, audit_logs, session_state
- Demo user seeded: username=demo, password=demo

## Obsidian Integration

`obsidian-vault-template/` provides the vault structure with `canonical/` and `proposed/` directories, YAML frontmatter conventions, and markdown templates for characters, locations, and events. Uses `[[wiki-links]]` for entity cross-referencing.

## Dependencies

Backend dependencies are in `backend/requirements.txt` (pip-based, not yet migrated to UV/pyproject.toml). The Dockerfile installs them directly.
