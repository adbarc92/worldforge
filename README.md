# AetherCanon Builder

**An open-source, locally-hosted knowledge coherence system for worldbuilders**

Build and maintain logically consistent fictional universes using AI assistance. Perfect for fiction writers, game designers, and TTRPG creators.

## Features (Phase 1 MVP)

- 📄 **Document Ingestion** - Upload PDF, DOCX, and Markdown files with automatic entity extraction
- 🔍 **Semantic Query** - Ask questions about your world with AI-powered answers and citations
- ⚠️ **Inconsistency Detection** - Automatically detect contradictions in your worldbuilding lore
- ✅ **Review Queue** - Review and approve AI-generated content before it becomes canonical
- 📤 **Obsidian Export** - Export your knowledge graph to Obsidian format

## Core Innovation

AetherCanon Builder separates "canonical" (user-approved) content from "proposed" (AI-generated) content with explicit review workflows. This enables confident use of unreliable LLMs for creative knowledge work.

## Tech Stack

**Simplified MVP Architecture:**
- **Backend:** FastAPI with Python 3.11
- **Databases:** SQLite (metadata), ChromaDB (vector embeddings)
- **RAG:** LlamaIndex for semantic search
- **LLM:** Hybrid support for Claude API and Ollama (local)
- **Frontend:** Streamlit web UI
- **Deployment:** Docker Compose

## Quick Start

### Prerequisites

- Docker Desktop with Docker Compose
- 16GB RAM minimum (32GB recommended)
- (Optional) NVIDIA GPU for faster local inference with Ollama
- (Optional) Claude API key for cloud-based LLM

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/worldforge.git
   cd worldforge
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your preferred LLM provider:

   **For Claude API (recommended for faster development):**
   ```env
   LLM_PROVIDER=claude
   CLAUDE_API_KEY=your-api-key-here
   ```

   **For Ollama (local, no API costs):**
   ```env
   LLM_PROVIDER=ollama
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **(Ollama users only) Pull the model:**
   ```bash
   docker exec -it worldforge-ollama-1 ollama pull mistral:7b-instruct
   ```

5. **Access the application:**
   - **Web UI:** http://localhost:8501
   - **API Docs:** http://localhost:8000/docs

### Stopping the Services

```bash
docker-compose down
```

To remove all data (reset):
```bash
docker-compose down -v
rm -rf data/
```

## Project Structure

```
worldforge/
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── config.py     # Configuration management
│   │   ├── main.py       # FastAPI entry point
│   │   ├── database/     # SQLAlchemy models & connection
│   │   ├── ingestion/    # Document parsing & entity extraction
│   │   ├── retrieval/    # Semantic search & RAG
│   │   ├── consistency/  # Inconsistency detection
│   │   ├── llm/          # LLM provider abstraction
│   │   ├── review/       # Review queue logic
│   │   ├── export/       # Obsidian export
│   │   └── api/          # REST API routes
│   └── requirements.txt
├── frontend/             # Streamlit web UI
│   ├── app.py           # Main page
│   └── pages/           # Feature pages
├── config/              # YAML configuration files
├── data/                # Persistent data (git-ignored)
├── docs/                # Documentation
│   └── CoreDesignDoc.md
├── docker-compose.yml   # Container orchestration
├── Dockerfile           # Application container
└── README.md
```

## Development Setup

For development with hot reload:

```bash
# Copy development config
cp config/config.example.yaml config/config.dev.yaml

# Edit config.dev.yaml with your settings
# Set DEBUG=true in .env

# Run with development overrides
docker-compose up --build
```

### Running Tests

```bash
# Run all tests
docker exec -it worldforge-app-1 pytest

# Run with coverage
docker exec -it worldforge-app-1 pytest --cov=app tests/
```

### Database Migrations

```bash
# Create a new migration
docker exec -it worldforge-app-1 alembic -c backend/alembic.ini revision --autogenerate -m "description"

# Apply migrations
docker exec -it worldforge-app-1 alembic -c backend/alembic.ini upgrade head
```

## Usage Guide

### 1. Upload Documents

1. Navigate to the Upload page in the web UI
2. Upload PDF, DOCX, or Markdown files
3. Wait for processing (chunking, embedding, entity extraction)
4. View extracted entities in the Review Queue

### 2. Review AI-Generated Content

1. Go to the Review Queue page
2. View proposed entities and relationships
3. Approve, reject, or edit each item
4. Approved items become part of your canonical knowledge

### 3. Query Your World

1. Navigate to the Query page
2. Ask questions about your world (e.g., "Who is Aragorn?")
3. Get AI-generated answers with citations to source documents
4. Citations are linked to original documents and page numbers

### 4. Detect Inconsistencies

1. Conflicts are automatically detected when documents are uploaded
2. View detected conflicts in the Conflicts page
3. See side-by-side evidence from different sources
4. Mark conflicts as resolved or "not a conflict"

### 5. Export to Obsidian

1. Go to the Export page
2. Select entities and formats
3. Download the generated Obsidian vault
4. Open in Obsidian to view your knowledge graph

## Configuration

### LLM Provider Selection

**Claude API (Recommended for development):**
- Faster, more accurate
- Requires API key and costs per token
- Best for initial development and testing

**Ollama (For production/privacy):**
- Runs locally, no API costs
- Requires more RAM and compute
- Supports various models (Mistral, Llama, etc.)

### Customizing Prompts

Edit `backend/app/llm/prompts.py` to customize:
- Entity extraction templates
- Contradiction detection logic
- Query response formatting

### Adjusting Thresholds

In `.env`:
```env
SIMILARITY_THRESHOLD=0.85          # Conflict detection sensitivity
HIGH_CONFIDENCE_THRESHOLD=0.90     # Auto-approve threshold
CHUNK_SIZE=500                     # Text chunk size in tokens
CHUNK_OVERLAP=50                   # Overlap between chunks
```

## Roadmap

### ✅ Phase 0: Foundation (Current)
- [x] Project structure
- [x] Docker deployment
- [x] Database models
- [x] LLM provider abstraction
- [x] Basic FastAPI app

### 🚧 Phase 1: MVP Features (In Progress)
- [ ] Document ingestion pipeline
- [ ] Semantic query with citations
- [ ] Inconsistency detection
- [ ] Review queue interface
- [ ] Obsidian export

### 📅 Phase 2: Collaboration (Future)
- [ ] Git-based versioning
- [ ] Multi-user permissions
- [ ] Comment system
- [ ] Activity log
- [ ] Merge conflict resolution

### 📅 Phase 3: Advanced Features
- [ ] Neo4j integration for advanced graph queries
- [ ] Web-based graph visualization
- [ ] API webhooks
- [ ] Plugin system

## Troubleshooting

### Ollama model not found
```bash
docker exec -it worldforge-ollama-1 ollama pull mistral:7b-instruct
```

### Port already in use
Change ports in `docker-compose.yml` or `.env`:
```env
API_PORT=8001
STREAMLIT_PORT=8502
```

### Out of memory
Reduce chunk size or increase Docker memory limit in Docker Desktop settings.

### ChromaDB errors
Delete and recreate:
```bash
docker-compose down
rm -rf data/chromadb
docker-compose up -d
```

## Contributing

This is currently a solo project in active development. Contributions welcome after Phase 1 MVP is complete.

## License

MIT License - See LICENSE file

## Support

- **Issues:** https://github.com/yourusername/worldforge/issues
- **Documentation:** See `docs/CoreDesignDoc.md`

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [LlamaIndex](https://www.llamaindex.ai/)
- [ChromaDB](https://www.trychroma.com/)
- [Streamlit](https://streamlit.io/)
- [Anthropic Claude](https://www.anthropic.com/)
- [Ollama](https://ollama.ai/)

---

**Status:** Phase 1 MVP in development

**Last Updated:** January 2026
