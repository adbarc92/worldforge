# Canon Builder

**An open-source, self-hosted tool for constructing and maintaining logically coherent knowledge systems.**

Canon Builder helps you build complex, internally consistent knowledge bases that grow over time without accumulating contradictions. Primarily designed for worldbuilding (fiction writers, game designers, TTRPG enthusiasts), it also supports research synthesis, policy analysis, and any domain requiring logical consistency.

## Core Features

- **Human-in-the-Loop Canonization**: Explicit separation of "canonical" (user-verified) from "proposed" (AI-generated) content
- **Consistency Checking**: Automatic detection of contradictions across your knowledge base
- **Hybrid RAG System**: Semantic search (Qdrant) + Knowledge graph (Neo4j) + Local LLMs (Ollama)
- **Obsidian Integration**: Familiar graph-based exploration and markdown editing
- **Privacy-First**: Fully local/self-hosted by default, cloud optional
- **Version Control**: Git-backed versioning with full audit trails

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Obsidian (Primary) | Web UI (Secondary) | REST API             │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Backend | LlamaIndex RAG | LangGraph Agents            │
├─────────────────────────────────────────────────────────────────┤
│  Qdrant (Vectors) | Neo4j (Graph) | PostgreSQL (Metadata)       │
├─────────────────────────────────────────────────────────────────┤
│  Ollama (Local LLMs) | BGE-large-en-v1.5 (Embeddings)           │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (required)
- **64GB+ RAM recommended** (16GB minimum for CPU-only mode)
- **NVIDIA GPU** (optional but strongly recommended for good performance)
- **100GB+ free disk space**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/canon-builder.git
   cd canon-builder
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set secure secrets
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to initialize** (~30-60 seconds)

5. **Pull LLM models** (first time only, ~40GB download)
   ```bash
   # Pull the LLM (this will take a while)
   docker exec -it canon_ollama ollama pull llama3.1:70b

   # Pull the embedding model
   docker exec -it canon_ollama ollama pull bge-large-en-v1.5
   ```

6. **Access the interfaces**
   - **Web UI**: http://localhost:3000
   - **API Docs**: http://localhost:8080/docs
   - **Neo4j Browser**: http://localhost:7474 (user: `neo4j`, pass: `canon_builder_pass_2024`)

### Using Obsidian

1. **Copy the vault template**
   ```bash
   cp -r obsidian-vault-template my-canon-vault
   ```

2. **Open in Obsidian**
   - Launch Obsidian
   - Open folder as vault: `my-canon-vault`

3. **Start building your canon**
   - Use templates to create entities
   - Link entities with `[[wiki-style links]]`
   - View relationships in graph view

## Usage

### 1. Upload Documents

Upload your initial worldbuilding documents to establish the canon:

```bash
curl -X POST "http://localhost:8080/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@worldbuilding-notes.txt" \
  -F "title=Initial World Notes"
```

Or use the Web UI at http://localhost:3000

### 2. Query Your Canon

Ask questions about your canonical content:

```bash
curl -X POST "http://localhost:8080/api/v1/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main characteristics of the magic system?",
    "top_k": 10
  }'
```

### 3. Generate Extensions

Request AI-generated extensions to your canon:

```bash
curl -X POST "http://localhost:8080/api/v1/proposals/extend" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What would happen if gunpowder was introduced to this world?",
    "creativity_level": 0.7
  }'
```

### 4. Review & Canonize

Review proposals in the Web UI and choose to:
- **Accept**: Proposal becomes canonical
- **Edit**: Modify before accepting
- **Reject**: Discard the proposal
- **Revise**: Request a new generation with feedback

## Development

### Project Structure

```
canon-builder/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration, security
│   │   ├── models/      # Data models
│   │   ├── services/    # Business logic
│   │   └── utils/       # Utilities
│   ├── migrations/      # Database migrations
│   └── tests/           # Unit tests
├── docs/                # Documentation
├── obsidian-vault-template/  # Vault template
├── docker-compose.yml   # Service orchestration
└── README.md
```

### Running Locally (Development)

```bash
# Backend only
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Testing

```bash
cd backend
pytest tests/ -v --cov=app
```

## Hardware Requirements

| Tier | RAM | GPU | Storage | Use Case | Speed |
|------|-----|-----|---------|----------|-------|
| **Minimum** | 16 GB | None (CPU) | 100 GB | <50 docs, single user | ~5 tokens/sec |
| **Recommended** | 64 GB | RTX 3060 (12GB) | 500 GB | 50-500 docs, 2-5 users | ~40 tokens/sec |
| **Optimal** | 128 GB | RTX 4090 (24GB) | 1+ TB | 500+ docs, 10+ users | ~80 tokens/sec |

## Configuration

Key environment variables in `.env`:

- `JWT_SECRET`: Secret key for JWT tokens (change in production!)
- `OLLAMA_URL`: Ollama service URL (default: http://ollama:11434)
- `QDRANT_URL`: Qdrant vector DB URL (default: http://qdrant:6333)
- `NEO4J_URI`: Neo4j graph DB URI (default: bolt://neo4j:7687)
- `LLM_MODEL`: Model to use (default: llama3.1:70b)
- `EMBEDDING_MODEL`: Embedding model (default: bge-large-en-v1.5)

## API Documentation

Full API documentation available at http://localhost:8080/docs when running.

### Key Endpoints

- `POST /api/v1/auth/login` - Authenticate and get JWT token
- `POST /api/v1/documents/upload` - Upload documents
- `GET /api/v1/documents` - List all documents
- `POST /api/v1/query` - Query canonical knowledge
- `POST /api/v1/proposals/extend` - Generate extensions
- `GET /api/v1/graph/entities` - List knowledge graph entities
- `GET /api/v1/consistency/contradictions` - List detected contradictions

## Roadmap

### Phase 1: MVP (Current)
- [x] Document ingestion and indexing
- [x] Basic RAG with Q&A
- [x] Extension generation with review
- [x] Docker Compose deployment
- [ ] Entity extraction and graph building
- [ ] Basic contradiction detection
- [ ] Obsidian plugin (basic)

### Phase 2: Enhanced Coherence (Next)
- [ ] Advanced consistency checking
- [ ] Coherence scoring (0-100)
- [ ] Severity-rated alerts
- [ ] Multi-user collaboration
- [ ] Cloud API fallback

### Phase 3: Advanced Features
- [ ] Toggleable suggestion engine
- [ ] Gap identification
- [ ] Multiple canon branches
- [ ] Advanced export (PDF, static sites)
- [ ] Plugin ecosystem

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/canon-builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/canon-builder/discussions)

## Acknowledgments

Built with:
- [LlamaIndex](https://github.com/run-llama/llama_index) - RAG framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [Qdrant](https://github.com/qdrant/qdrant) - Vector search
- [Neo4j](https://neo4j.com/) - Knowledge graph
- [Ollama](https://github.com/ollama/ollama) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework

## Citation

If you use Canon Builder in your research or projects, please cite:

```bibtex
@software{canon_builder,
  title = {Canon Builder: A Tool for Constructing Coherent Knowledge Systems},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/canon-builder}
}
```

---

**Status**: Phase 1 MVP - Under Active Development

**Last Updated**: January 2025
