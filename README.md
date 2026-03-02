# Canon Builder

A RAG-powered worldbuilding knowledge system. Upload your documents, ask questions, get AI-generated answers grounded in your canon.

Single-user, self-hosted. Uses Claude for generation and OpenAI for embeddings. Chat via OpenWebUI.

## Quick Start

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY and OPENAI_API_KEY to .env

docker-compose up -d
```

Visit http://localhost:3000 (OpenWebUI) to start chatting with your canon.

API docs at http://localhost:8080/docs.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload a document (text, md, pdf) |
| GET | `/api/v1/documents` | List all documents |
| GET | `/api/v1/documents/{id}` | Get document details |
| DELETE | `/api/v1/documents/{id}` | Delete a document and its chunks |
| POST | `/api/v1/query` | RAG query with citations |
| POST | `/v1/chat/completions` | OpenAI-compatible endpoint (for OpenWebUI) |

## OpenWebUI Integration

OpenWebUI is included in docker-compose and auto-configured to use Canon Builder's API as its backend. Visit http://localhost:3000 after `docker-compose up -d`.

## Development

```bash
cd backend
uv sync --all-groups          # install dependencies
uv run pytest tests/ -v       # run tests
uv run alembic upgrade head   # apply migrations
```

**Service ports**: API 8080, OpenWebUI 3000, Qdrant 6333, PostgreSQL 5432

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for future plans.

## License

MIT License - see [LICENSE](LICENSE) for details.
