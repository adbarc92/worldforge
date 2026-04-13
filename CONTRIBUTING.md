# Contributing to WorldForge

Thanks for your interest in contributing to WorldForge! This is a RAG-powered worldbuilding knowledge system built as a single-user personal tool that grew into something worth sharing. Contributions of all kinds are welcome — bug reports, feature suggestions, documentation improvements, and code.

See [README.md](README.md) for a project overview and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design details.

## Code of conduct

Be kind. Assume good faith. Focus on the work. If someone is making WorldForge better — even if you disagree with how — remember there's a human on the other side. Personal attacks, harassment, or dismissive behavior are not welcome. Maintainers may moderate or remove contributions that violate this spirit.

## Development setup

### Prerequisites

- **Docker Desktop** (or Docker Engine + Compose v2)
- **[UV](https://docs.astral.sh/uv/)** for Python package management
- **Node.js 20+** and npm
- An Anthropic API key and an OpenAI API key (for Claude generation and embeddings)

### Clone and install

```bash
git clone https://github.com/adbarc92/worldforge.git
cd worldforge

# Backend dependencies
cd backend && uv sync --all-groups && cd ..

# Frontend dependencies
cd frontend && npm install && cd ..

# Environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and OPENAI_API_KEY
```

### Run with Docker (recommended)

```bash
docker compose up -d --build
```

- API + frontend: http://localhost:8080
- OpenWebUI: http://localhost:3000
- Qdrant: http://localhost:6333
- PostgreSQL: port 5432

### Run without Docker (development)

Two terminals:

```bash
# Terminal 1 — backend
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8080
```

```bash
# Terminal 2 — frontend with hot reload
cd frontend
npm run dev
# Vite proxies /api, /v1, /health to localhost:8080
```

Frontend dev server runs on http://localhost:5173.

### Apply database migrations

```bash
cd backend
uv run alembic upgrade head
```

### Seed test data

WorldForge includes a bulk-upload script for loading existing `.md`, `.txt`, or `.pdf` files into a project:

```bash
cd scripts
uv run python bulk_upload.py <path-to-folder> --project "My Project"
```

## Project structure

```
backend/          # FastAPI + SQLAlchemy async, Qdrant, Anthropic/OpenAI SDKs
  app/
    api/v1/       # Route handlers
    models/       # SQLAlchemy + Pydantic schemas
    services/     # Business logic (LLM, ingestion, RAG, synthesis)
    core/         # Config
  tests/          # pytest (unit + integration)

frontend/         # React 19 + Vite + TanStack Query + Tailwind v4 + shadcn/ui
  src/
    components/   # UI by feature (chat, documents, contradictions, synthesis, layout)
    hooks/        # React Query hooks (one per resource)
    lib/          # API client
    pages/        # Route-level components
    test/         # Vitest setup, MSW handlers, test utilities

docs/             # Architecture, roadmap, design specs
scripts/          # Utility scripts (bulk upload, etc.)
.github/workflows/# CI pipelines
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture walkthrough.

## Running tests

### Backend

```bash
cd backend
uv run pytest tests/ -v              # all tests
uv run pytest tests/ -v -m "not integration"  # skip integration
uv run pytest tests/test_basic.py -v  # single file
```

### Frontend

```bash
cd frontend
npm run test              # run once
npm run test:watch        # watch mode
npm run test:coverage     # with coverage report
npm run test:ui           # Vitest UI
```

## Code style

### Python (backend)

- **Ruff** for linting and formatting (`uv run ruff check backend/` / `uv run ruff format backend/`)
- Type hints everywhere (Pydantic models for API, SQLAlchemy 2.0 typing for DB)
- Async-first — database, vector DB, and LLM calls are `async def`

### TypeScript (frontend)

- **ESLint** (`npm run lint`)
- **tsc --noEmit** for type checking (`npm run typecheck`)
- Strict mode enabled
- Follow existing patterns: one hook per resource, colocated tests, shadcn/ui for primitives

### Commit messages

Use conventional prefixes:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — tests only
- `chore:` — tooling, deps, config
- `refactor:` — code change that's not a fix or feature
- `ci:` — CI/CD changes

Keep commits focused — one logical change per commit. We use squash merges on PRs, but clean individual commits make review easier.

## PR workflow

1. **Fork** the repository and clone your fork
2. **Create a branch**: `git checkout -b feat/your-feature` or `fix/bug-name`
3. **Make changes** — keep PRs focused on one thing
4. **Run the test suite** locally (`uv run pytest` + `npm run test`)
5. **Run lint and typecheck** (`uv run ruff check backend/` + `npm run lint` + `npm run typecheck`)
6. **Commit** with a clear message (see conventions above)
7. **Push** to your fork and **open a PR** against `main`
8. **Link the issue** the PR addresses (if any)
9. Wait for **CI** to pass — all checks must be green before review
10. Respond to review feedback — don't force-push; add new commits so reviewers can see what changed

### Branch protection (maintainer reference)

The `main` branch is protected:

- Requires the `ci` check to pass
- No direct pushes — merge via PR
- Squash merge is the default

## What we're looking for

**Great first contributions:**

- Bug fixes with reproduction steps and a failing test
- Documentation improvements (typos, clearer explanations, missing sections)
- Frontend tests for components that aren't yet covered
- Backend tests for edge cases

**High-value areas:**

- Better PDF parsing and extraction
- Additional LLM providers (local, Ollama, etc.)
- Alternative embedding models
- Performance improvements to ingestion/query

**Check the roadmap:** [docs/ROADMAP.md](docs/ROADMAP.md) — Phase 2 (knowledge graph) and Phase 3 (proposals & consistency) are where most feature work is happening.

## What not to work on without discussion

Please open an issue or discussion first if you're thinking about:

- **Authentication / multi-user support** — this is Phase 4 work with significant scope. We want to plan it carefully.
- **Major architectural changes** — replacing a core dependency (Qdrant, FastAPI, React Query), restructuring the service layer, etc.
- **New pages or top-level features** — talk through the shape first so the PR doesn't land in surprising territory.

## Questions?

- [GitHub Discussions](https://github.com/adbarc92/worldforge/discussions) — questions, ideas, show-and-tell
- [GitHub Issues](https://github.com/adbarc92/worldforge/issues) — bugs and concrete feature requests

Thanks for contributing!
