# Fantasy Worldbuilding Assistant – Core Design Document
(Version 1.0 – December 11, 2025)

## 1. Project Overview
### Project Name: AetherForge
AetherForge is an open-source, self-hosted fantasy worldbuilding tool powered by large language models (LLMs) and retrieval-augmented generation (RAG). It enables creative users—such as writers, game designers, and tabletop RPG enthusiasts—to build, maintain, and collaborate on immersive fantasy worlds. The system ingests diverse documents, maintains a persistent state, answers queries, detects inconsistencies, and optionally suggests expansions based on patterns in the lore.

### Key Goals
- **Persistence**: Create a "living world bible" with unlimited context growth over time.
- **Flexibility**: Accept any document format (e.g., PDFs, images, text files, mind maps).
- **Interactivity**: Provide an Obsidian-like graph interface for visual exploration.
- **Collaboration**: Support multi-user access with real-time or near-real-time syncing.
- **Intelligence**: Proactively identify lore inconsistencies and offer toggleable creative suggestions.
- **Privacy & Accessibility**: Fully local/self-hosted, with optional cloud fallbacks; easy to share with teams.

### Target Users
- Solo creators building personal worlds.
- Collaborative teams (2–30 users) for shared projects like novels, games, or campaigns.
- Focus on fantasy, but extensible to sci-fi, historical fiction, etc.

### Assumptions & Constraints
- Users have basic tech setup (e.g., Docker on a PC/server with 16–64 GB RAM and GPU for local LLMs).
- No internet required post-setup; all processing local.
- Budget: Free/open-source tools only; optional API costs for cloud LLMs (<$10/month).
- Scalability: Handles 100s of documents initially; scales to 1000s with proper hardware.

## 2. System Architecture
### High-Level Diagram
```
+-------------------+     +-------------------+     +-------------------+
|   User Interfaces |     |   Core Engine     |     |   Data Storage    |
+-------------------+     +-------------------+     +-------------------+
| - Obsidian (Graph)|<--->| - LlamaIndex      |<--->| - Qdrant (Vectors)|
| - Web UI (Custom) |     | - LangGraph       |     | - Neo4j (Graph)   |
|                   |     | - Agents (Checker,|     | - File System     |
|                   |     |   Suggester)      |     |   (Raw Docs)      |
+-------------------+     +-------------------+     +-------------------+
                                 ^
                                 |
                       +-------------------+
                       |   LLM Providers   |
                       +-------------------+
                       | - Local: Ollama   |
                       |   (Llama-3.1-70B) |
                       | - Fallback: API   |
                       |   (Claude/GPT)    |
                       +-------------------+
```

### Component Breakdown
| Component | Description | Tools/Technologies | Rationale |
|-----------|-------------|--------------------|-----------|
| **Ingestion Pipeline** | Parses and processes uploaded documents. | Unstructured.io (for multimodal: text, OCR, tables, images). | Handles diverse formats; extracts clean text/metadata for embedding. |
| **Embedding & Retrieval** | Converts chunks to vectors; hybrid search. | BGE-large-en-v1.5 embeddings; LlamaIndex for chunking. | Optimized for narrative text; fast retrieval with semantic + keyword search. |
| **Knowledge Graph** | Stores entities, relationships for reasoning. | Neo4j with GraphRAG extensions. | Enables contradiction detection via graph queries; visualizes connections. |
| **State Management** | Maintains persistent chat/context. | LangGraph for agent workflows; session tracking in LlamaIndex. | Ensures "memory" across sessions; toggle features like suggestions. |
| **LLM Core** | Powers queries, extractions, suggestions. | Local: Llama-3.1-70B or Nemotron-70B via Ollama (128k+ context).<br>Fallback: Claude 3.5 Sonnet / GPT-4o API. | Local for privacy/speed; long context for comprehensive answers. |
| **User Interfaces** | Interaction layers. | Primary: Obsidian (graph view, Markdown notes).<br>Secondary: OpenWebUI/Streamlit (web chat/upload). | Obsidian provides intuitive graph; web for accessibility. |
| **Collaboration** | Multi-user syncing. | Git (for Obsidian vaults) + Syncthing (real-time P2P). Optional: Self-hosted GitLab. | Simple, offline-capable; handles conflicts via merges. |
| **Agents** | Autonomous logic modules. | - Consistency Checker: Post-ingestion/query.<br>- Suggestion Engine: Pattern-based (toggleable).<br>- Extractor: Builds graph from docs. | Built with LangGraph; modular for easy extension. |

### Data Flow
1. **Upload**: User adds document → Unstructured parses → Chunks embedded → Stored in Qdrant.
2. **Graph Building**: LLM extracts entities/relations → Neo4j nodes/edges with provenance.
3. **Query**: User asks question → Retrieve vectors + graph subset → LLM synthesizes answer.
4. **Consistency Check**: Agent scans for conflicts → Alerts users with sources/resolutions.
5. **Suggestions**: If toggled, agent analyzes patterns (e.g., gaps in lore) → Proposes ideas.
6. **Collaboration Sync**: Changes push to Git/Syncthing → Triggers re-indexing.

## 3. Features in Detail
### Core Features
- **Document Ingestion**: Supports PDFs, DOCX, images (OCR), TXT, etc. Automatic metadata tagging (e.g., upload date, user).
- **Query Answering**: Natural language questions about the world (e.g., "What are the elf kingdoms' alliances?").
- **Inconsistency Detection**: Proactive; e.g., "Elf lifespan: 800 years (Doc A) vs. 200 years (Doc B)". Severity-rated alerts.
- **Graph Interface**: Obsidian-style: Nodes (entities), edges (relations); clickable for details/queries.

### Advanced Features
- **Toggleable Suggestions**: Analyzes graph for patterns (e.g., "Recurring 'betrayal' theme—suggest a spy subplot?"). Configurable creativity level.
  - Toggle: UI checkbox or YAML flag (`suggestions.enabled: false`).
- **Collaboration Tools**: User roles (viewer/editor); change logs; resolution voting for conflicts.
- **Export/Backup**: Full graph export to JSON/Markdown; static site generation for sharing.

### Security & Privacy
- All local: No data sent externally unless API fallback enabled.
- Authentication: Basic via OpenWebUI (usernames/passwords).
- Auditing: Log all changes with user attribution.

## 4. Technical Specifications
### Hardware Requirements
- Minimum: 16 GB RAM, CPU-only (slow for large models).
- Recommended: 64 GB RAM + NVIDIA GPU (RTX 3060+ for fast local LLM).
- Storage: 100 GB+ for docs/vectors/graph.

### Software Dependencies
- Docker for containerization.
- Python 3.10+ for scripts/agents.
- Models: Download via Ollama (e.g., `ollama run llama3.1:70b`).

### Deployment
- **One-Click Setup**: Docker Compose file (see Appendix).
- **Steps**:
  1. Clone repo.
  2. `docker-compose up`.
  3. Install Obsidian plugins (RAG, LiveSync).
  4. Seed with initial docs.

## 5. Development Roadmap
### Phase 1 (MVP – 1 Month)
- Ingestion + Basic RAG.
- Graph building + Obsidian integration.
- Query answering + Consistency checker.

### Phase 2 (Collaboration – 1 Month)
- Multi-user sync.
- Web UI.

### Phase 3 (Enhancements – Ongoing)
- Suggestion engine.
- Mobile access.
- Custom extensions (e.g., map generation).

### Risks & Mitigations
- LLM Hallucinations: Mitigate with strict prompting + graph grounding.
- Performance: Optimize chunk sizes; fallback to smaller models.
- Accuracy: Manual review for graph extractions (90%+ auto success rate).

## 6. Appendix: Docker Compose Example
```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  neo4j:
    image: neo4j:5.24
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
  unstructured:
    image: unstructured-io/unstructured-api:latest
    ports:
      - "8000:8000"
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "8080:8080"
    depends_on:
      - qdrant
    extra_hosts:
      - "host.docker.internal:host-gateway"
volumes:
  qdrant_data:
  neo4j_data:
```

## 7. References & Credits
- Based on open-source tools: LlamaIndex, Neo4j, Obsidian.
- Inspired by community projects (e.g., GraphRAG by Microsoft, r/LocalLLaMA discussions).
- Version Control: GitHub repo recommended for project tracking.

This document serves as the foundational blueprint. Update as needed for iterations.
