# WorldForge

**Your worldbuilding has contradictions. This finds them.**

[![CI](https://github.com/adbarc92/worldforge/actions/workflows/ci.yml/badge.svg)](https://github.com/adbarc92/worldforge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<!-- Demo GIF: record per docs/superpowers/specs/2026-04-15-launch-strategy-design.md, save as docs/images/demo.gif, then uncomment the line below -->
<!-- ![WorldForge demo](docs/images/demo.gif) -->

Upload your lore documents — session notes, story bibles, wiki exports. WorldForge chunks and embeds them into a vector database, then lets you:

- **Detect contradictions** when new content conflicts with established canon
- **Query your world** in plain English with cited answers
- **Synthesize narratives** across documents into a cohesive world primer

Open source. Self-hosted. One `docker compose up`.

---

## Why WorldForge?

I ran a homebrew TTRPG campaign for two years. Session notes, faction docs, and NPC backstories were scattered across dozens of markdown files. One night I told the party the duke was murdered — and a player pulled up my own notes showing I'd written he died of fever six months earlier.

So I built WorldForge. You upload your worldbuilding docs and it becomes a queryable knowledge base. The feature I'm most proud of: it catches contradictions before your players do.

---

## Quick Start

```bash
git clone https://github.com/adbarc92/worldforge.git
cd worldforge
cp .env.example .env
# Add your ANTHROPIC_API_KEY and OPENAI_API_KEY to .env

docker compose up -d
```

- **App:** http://localhost:8080
- **OpenWebUI chat:** http://localhost:3000
- **API docs:** http://localhost:8080/docs

Create a project, upload documents, and start asking questions.

---

## Features

### Contradiction detection
After every upload, WorldForge compares new content against existing canon and flags conflicts. Each contradiction shows both source chunks with citations so you can resolve, dismiss, or revise.

### Semantic query with citations
Ask questions in plain English. Answers are grounded in your actual documents with inline citations and relevance scores — no hallucinated lore.

### World synthesis
Generate a cohesive narrative primer across your whole project. Review and edit the outline before generation. Resolution notes from contradictions feed into the prompt, so the synthesis respects your canonical decisions.

### Multi-project isolation
Keep separate worldbuilds (campaigns, novels, settings) isolated. No cross-project leakage.

### Bulk upload
Point a CLI script at a folder of `.md`, `.txt`, or `.pdf` files and it creates the project and loads everything.

```bash
cd scripts
uv run python bulk_upload.py ./my-worldbuilding-notes --project "Homebrew Campaign"
```

### OpenAI-compatible endpoint
Point any OpenAI client at WorldForge and chat with your canon through a familiar interface. OpenWebUI ships preconfigured in docker compose.

---

## Tech Stack

- **Backend:** FastAPI, PostgreSQL, Qdrant, SQLAlchemy 2.0 (async), Alembic
- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query
- **LLM:** Anthropic Claude (generation), OpenAI `text-embedding-3-large` (embeddings)
- **Parsing:** LlamaIndex SentenceSplitter, PyPDF

Local LLM support (Ollama, BGE embeddings) is on the [roadmap](docs/ROADMAP.md) — v1.0.0 requires cloud API keys.

---

## Development

```bash
# Backend
cd backend
uv sync --all-groups
uv run pytest tests/ -v
uv run alembic upgrade head

# Frontend
cd frontend
npm install
npm run dev          # Vite dev server on 5173, proxies API to 8080
npm run test
```

**Service ports:** API + frontend 8080, OpenWebUI 3000, Qdrant 6333, PostgreSQL 5432.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor guide, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a system overview, and [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for what v1.0.0 ships.

---

## API

OpenAPI docs at `/docs` when the server is running. Endpoint reference: [docs/REQUIREMENTS.md § TR-3](docs/REQUIREMENTS.md#tr-3-api-design).

---

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md). Upcoming: DOCX support, contradiction severity, entity extraction, knowledge graph, local LLM support, export formats.

---

## License

MIT — see [LICENSE](LICENSE).
