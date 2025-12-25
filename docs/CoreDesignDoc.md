# AetherCanon Builder — Core Design Document
**Version 2.0 — December 24, 2025**

## 1. Executive Summary

**AetherCanon Builder** is an open-source, locally-hosted knowledge coherence system that helps users build and maintain logically consistent worldbuilding canons using AI assistance. The system ingests diverse documents, maintains a versioned "canon" of approved content, detects logical inconsistencies, and generates optional extensions—all while keeping humans firmly in control of what becomes canonical truth.

**Primary Innovation**: Separation of "canonical" (user-approved) from "proposed" (AI-generated) content with explicit review workflows, enabling confident use of unreliable LLMs for creative knowledge work.

**Target Users**: Technical worldbuilders (fiction writers, game designers, TTRPG creators who are comfortable with Docker/basic DevOps).

**Deployment Model**: Open-source (MIT license) with local-first architecture. No SaaS tier in v1.0—revenue from enterprise support and managed hosting.

---

## 2. Problem Statement & User Research

### 2.1 The Core Problem
Worldbuilders working on complex fictional universes face **consistency drift** as their canon grows. Existing solutions fall short:
- **Wikis/Notion**: No consistency checking, manual maintenance
- **WorldAnvil/Campfire**: Structured data input, but inflexible and no semantic understanding
- **ChatGPT/Claude**: Helpful but stateless, hallucinates, no persistence

### 2.2 Validation Plan (Phase 0 - Before Development)
**Week 1-2**: Conduct 15 problem validation interviews
- Target: Active worldbuilders with 50+ pages of content
- Key questions: Consistency challenges? Current tools? Would you self-host?

**Week 3-4**: Solution validation with mockups
- Test Obsidian-based interface concept
- Validate canon/proposed separation model
- Gauge Docker/self-hosting comfort level

**Week 5-6**: Technical prototype (NO full features)
- Single workflow: Upload PDF → Extract entities → Display graph
- Goal: Validate technical feasibility, not build product

**Success Criteria**: 10/15 users express strong interest, 5+ willing to beta test, 80%+ comfortable with self-hosting given Docker Compose setup.

---

## 3. System Architecture

### 3.1 Architecture Principles
1. **Human authority**: AI suggests, humans decide
2. **Local-first**: Works offline after setup, optional cloud APIs
3. **Modular**: Components replaceable (swap Qdrant for Milvus, etc.)
4. **Transparent**: Show provenance, confidence scores, reasoning

### 3.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Layer                          │
├─────────────────────────────────────────────────────────┤
│  • Obsidian (graph, notes)                             │
│  • Web UI (upload, review queue, chat)                 │
│  • API (REST for integrations)                         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  Application Layer                      │
├─────────────────────────────────────────────────────────┤
│  • FastAPI backend (Python 3.11)                       │
│  • LlamaIndex (RAG orchestration)                      │
│  • LangGraph (agent workflows)                         │
│    - Ingestion Agent: Parse → Chunk → Embed           │
│    - Consistency Agent: Detect contradictions          │
│    - Extraction Agent: Build knowledge graph           │
│    - Extension Agent (opt-in): Generate expansions     │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                   Data Layer                            │
├─────────────────────────────────────────────────────────┤
│  • PostgreSQL: Metadata, versions, review queue        │
│  • Qdrant: Vector embeddings (semantic search)         │
│  • Neo4j 5.26: Knowledge graph (entities/relations)    │
│  • Filesystem: Original documents + Git versioning     │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                   AI Layer                              │
├─────────────────────────────────────────────────────────┤
│  • Ollama (local LLM): Mistral-7B / Llama3.1-8B        │
│  • Embedding: BGE-large-en-v1.5 (local)                │
│  • Optional cloud fallback: Claude/GPT-4 API           │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Data Model

#### Canonical Store (PostgreSQL Schema)
```sql
-- Core tables
documents (
  id UUID PRIMARY KEY,
  title TEXT,
  content_path TEXT,  -- filesystem location
  upload_date TIMESTAMP,
  status ENUM('active', 'archived'),
  git_commit_hash TEXT
)

entities (
  id UUID PRIMARY KEY,
  name TEXT,
  type ENUM('character', 'location', 'event', 'concept', 'item'),
  first_mentioned_doc UUID REFERENCES documents(id),
  canonical_description TEXT
)

relationships (
  id UUID PRIMARY KEY,
  source_entity UUID REFERENCES entities(id),
  target_entity UUID REFERENCES entities(id),
  relation_type TEXT,  -- 'located_in', 'allied_with', 'created_by'
  evidence_doc UUID REFERENCES documents(id),
  evidence_excerpt TEXT
)
```

#### Proposed Content Store
```sql
proposed_content (
  id UUID PRIMARY KEY,
  type ENUM('entity', 'relationship', 'document_extension'),
  content JSONB,  -- flexible structure
  generation_metadata JSONB,  -- model, prompt, timestamp
  coherence_score FLOAT,
  conflicts JSONB,  -- [{severity: 'high', with_entity: UUID, reason: ''}]
  review_status ENUM('pending', 'approved', 'rejected', 'edited'),
  reviewed_by TEXT,
  reviewed_at TIMESTAMP
)
```

#### Knowledge Graph (Neo4j Schema)
```cypher
// Node types
(:Character {id, name, first_appearance, traits})
(:Location {id, name, geography, climate})
(:Event {id, name, date, description})
(:Concept {id, name, definition})

// Relationship types with provenance
(:Character)-[:LOCATED_IN {since_date, source_doc_id}]->(:Location)
(:Character)-[:ALLIED_WITH {strength, source_doc_id}]->(:Character)
(:Event)-[:INVOLVES {role, source_doc_id}]->(:Character)

// Provenance tracking
(:Entity)-[:MENTIONED_IN {excerpt, page}]->(:Document)
```

---

## 4. Core Features (MVP Scope)

### 4.1 Document Ingestion
**User Story**: As a worldbuilder, I want to upload my existing lore documents so the system understands my canon.

**Technical Flow**:
1. User uploads PDF/DOCX/MD via web UI
2. Unstructured.io parses document → structured text + metadata
3. LlamaIndex chunks text (500 tokens, 50 overlap)
4. BGE-large-en-v1.5 generates embeddings → Qdrant
5. Entity Extraction Agent identifies entities/relationships → Neo4j
6. Original document stored in filesystem with Git commit
7. Entry created in PostgreSQL `documents` table

**Acceptance Criteria**:
- Supports PDF, DOCX, Markdown, TXT
- Handles documents up to 100 pages
- Extracts entities with ≥70% precision (validated against test corpus)
- Processing time <2 min per 50-page document on recommended hardware

### 4.2 Semantic Query with Provenance
**User Story**: As a worldbuilder, I want to ask questions about my canon and get answers with source citations.

**Technical Flow**:
1. User submits natural language query: "What is the political structure of Keldoria?"
2. Query embedding generated → Qdrant similarity search (top-k=10)
3. Retrieved chunks + Neo4j graph context assembled
4. LLM generates answer with inline citations: `[^1]`, `[^2]`
5. Response rendered with expandable source excerpts

**Acceptance Criteria**:
- Query latency <5s on recommended hardware
- Every factual claim has ≥1 source citation
- Citations link to specific document + page/section
- "I don't have information on that" when query outside canon

### 4.3 Inconsistency Detection
**User Story**: As a worldbuilder, I want to be alerted when new content contradicts existing canon.

**Algorithm Design**:
```
For each new entity/relationship:
1. Embedding similarity search in Qdrant (threshold=0.85)
   → Find semantically similar existing content
2. If similar content found:
   - Extract claims from both sources using LLM
   - Structured comparison prompt:
     "Compare these claims. Are they contradictory, complementary, or unrelated?"
3. If contradictory:
   - Severity scoring:
     * HIGH: Direct factual contradiction (age, death, location)
     * MEDIUM: Inconsistent characterization/timeline
     * LOW: Ambiguous or minor detail mismatch
4. Create conflict record with evidence from both sources
```

**Acceptance Criteria**:
- Detects ≥85% of planted contradictions in test corpus
- False positive rate <20%
- Provides human-readable explanation for each conflict
- Allows user to mark conflicts as "not actually conflicting"

### 4.4 Review Queue Interface
**User Story**: As a worldbuilder, I want to review AI-generated suggestions before they become canon.

**UI Components**:
- Queue list view: Proposed items sorted by coherence score
- Detail view:
  - Side-by-side: Proposed content | Related canon
  - Diff highlighting for edits
  - Conflict warnings (if any)
  - Actions: Approve / Edit & Approve / Reject / Defer
- Bulk operations: Approve all high-confidence (>0.9) items

**Acceptance Criteria**:
- Queue loads <1s for 100 items
- Clear visual distinction between proposed/canonical
- Undo functionality for last 10 actions

---

## 5. Technical Specifications

### 5.1 Hardware Requirements (Right-Sized)

| Tier | CPU | RAM | GPU | Storage | Model Support | Use Case |
|------|-----|-----|-----|---------|---------------|----------|
| **Minimal** | 4-core | 16 GB | None | 100 GB | Mistral-7B-Instruct (Q4) | 10-50 docs, slow queries |
| **Recommended** | 8-core | 32 GB | RTX 3060 (12GB) | 500 GB | Llama3.1-8B (Q5) | 100-500 docs, <5s queries |
| **Optimal** | 16-core | 64 GB | RTX 4090 (24GB) | 1 TB | Mixtral-8x7B / Llama3.1-70B (Q4) | 1000+ docs, multi-user |

**Model Size Reality Check**:
- 7B quantized (Q4): ~4GB RAM
- 8B quantized (Q5): ~6GB RAM
- 70B quantized (Q4): ~40GB RAM (requires GPU)

### 5.2 Software Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Backend | FastAPI | 0.104+ | Async, OpenAPI docs |
| RAG Framework | LlamaIndex | 0.9+ | Best hybrid search |
| Agent Framework | LangGraph | 0.0.30+ | Stateful workflows |
| Vector DB | Qdrant | 1.7+ | Fast, local-first |
| Graph DB | Neo4j | 5.26 | Mature, Cypher queries |
| Metadata DB | PostgreSQL | 16+ | JSONB support |
| LLM Runtime | Ollama | 0.1.17+ | Easy local serving |
| Embeddings | BGE-large-en-v1.5 | - | Top MTEB for narratives |
| Document Parsing | Unstructured.io | 0.10+ | Multi-format |
| Web UI | Streamlit | 1.29+ | Rapid prototyping |

### 5.3 Deployment (Docker Compose)

```yaml
version: '3.8'

services:
  app:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/aethercanon
      - QDRANT_URL=http://qdrant:6333
      - NEO4J_URI=bolt://neo4j:7687
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./data/documents:/app/documents
      - ./data/git:/app/git
    depends_on:
      - postgres
      - qdrant
      - neo4j
      - ollama

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: aethercanon
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  qdrant:
    image: qdrant/qdrant:v1.7.4
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  neo4j:
    image: neo4j:5.26
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["graph-data-science"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  webui:
    build: ./frontend
    ports:
      - "8501:8501"
    depends_on:
      - app

volumes:
  postgres_data:
  qdrant_data:
  neo4j_data:
  ollama_data:
```

**Setup Instructions**:
```bash
# 1. Clone repository
git clone https://github.com/aethercanon/builder && cd builder

# 2. Pull Ollama model
docker-compose up -d ollama
docker exec -it ollama ollama pull mistral:7b-instruct

# 3. Start all services
docker-compose up -d

# 4. Initialize database
docker-compose exec app python -m alembic upgrade head

# 5. Access at http://localhost:8501
```

---

## 6. Development Roadmap

### Phase 0: Validation (6 weeks) ✓ Required Before Phase 1
- [ ] Conduct 15 user interviews
- [ ] Create Figma mockups of core workflows
- [ ] Build technical proof-of-concept (1 workflow only)
- [ ] Validate self-hosting comfort level
- [ ] Write PRD based on findings

**Go/No-Go Decision Point**: Need 8/15 users willing to beta test

### Phase 1: MVP (3 months)
**Goal**: Single-user system with core workflows

**Deliverables**:
- [ ] Document ingestion pipeline (PDF/DOCX/MD)
- [ ] Semantic query with citations
- [ ] Basic inconsistency detection (embedding + LLM comparison)
- [ ] Review queue interface
- [ ] Obsidian export (Markdown + graph JSON)

**Success Metrics**:
- 5 beta users actively using system
- Average canon size: 20+ documents
- Inconsistency detection precision >80%
- User satisfaction score ≥7/10

### Phase 2: Collaboration (3 months)
**Goal**: Multi-user support with conflict resolution

**Deliverables**:
- [ ] Git-based versioning with web UI
- [ ] Role-based permissions (owner/editor/viewer)
- [ ] Comment system on proposed content
- [ ] Activity log and notifications
- [ ] Merge conflict resolution UI for graph changes

**Success Metrics**:
- 3 teams of 2-4 users collaborating
- <5% data loss incidents
- Merge conflicts resolved in <10 min average

### Phase 3: Polish (Ongoing)
- Advanced graph queries (shortest path, clustering)
- Export to WorldAnvil/Notion formats
- Mobile companion app (read-only)
- Custom entity type definitions
- Automated canon summarization

---

## 7. Risk Management

| Risk | Impact | Probability | Mitigation Strategy | Owner |
|------|--------|-------------|---------------------|-------|
| **LLM Hallucinations** | High | High | • Conservative prompting with grounding<br>• Always show sources<br>• User review required<br>• Track accuracy metrics | Engineering |
| **Poor Inconsistency Detection** | High | Medium | • Start with high-precision, low-recall<br>• Let users train on false positives<br>• Target 85% precision (validated in testing)<br>• Provide "not a conflict" feedback loop | ML/Product |
| **User Setup Complexity** | High | Medium | • One-command Docker Compose<br>• Video tutorial series<br>• Pre-configured DigitalOcean droplet<br>• Active Discord support | DevRel |
| **Graph Merge Conflicts** | Medium | High | • Delay multi-user to Phase 2<br>• Implement operational transformation<br>• Provide conflict visualization<br>• Allow manual resolution | Engineering |
| **Ollama Model Availability** | Medium | Low | • Support multiple model backends<br>• Document cloud API fallback<br>• Mirror critical models | DevOps |
| **Low User Adoption** | High | Medium | • Phase 0 validation (reduce by 80%)<br>• Focus on single high-value workflow<br>• Active community building | Product/Growth |
| **Data Loss** | Critical | Low | • Automated backups every 6 hours<br>• Git-based document versioning<br>• PostgreSQL WAL archiving<br>• Restore testing in CI/CD | DevOps |

---

## 8. Success Metrics & KPIs

### Phase 1 (MVP)
- **Adoption**: 20 active beta users
- **Engagement**: 10+ documents per user, 5+ queries per week
- **Quality**: Inconsistency detection precision >80%, <15% false positives
- **Technical**: Query latency p95 <5s, uptime >99%

### Phase 2 (Collaboration)
- **Growth**: 100 active users, 10 collaborative teams
- **Retention**: 60% monthly retention
- **Satisfaction**: NPS ≥40

### Phase 3 (Maturity)
- **Scale**: 1,000 users, 50,000 documents indexed
- **Community**: 10 open-source contributors, 50 GitHub stars
- **Recognition**: Featured in 2 worldbuilding podcasts/blogs

---

## 9. Business Model & Sustainability

### Open-Core Strategy
**Community Edition** (MIT License):
- Full feature set for single-user
- Docker Compose deployment
- Community support via GitHub/Discord

**Enterprise Add-Ons** (Proprietary):
- Managed cloud hosting ($50-100/user/month)
- SSO/SAML integration
- Priority support SLA
- Custom model fine-tuning
- Professional services (migration, training)

### Revenue Projections (Conservative)
- **Year 1**: $0 revenue (focus on adoption)
- **Year 2**: $50K (10 enterprise pilots × $5K)
- **Year 3**: $200K (20 enterprise customers × $10K)

**Sustainability Path**: If enterprise adoption fails, pivot to Patreon/sponsorship model (target: $3K/month to fund 1 maintainer).

---

## 10. Open Questions & Future Research

### Technical
1. **How do we handle ambiguous canon?** (e.g., "maybe magic exists")
   - Proposed: Confidence levels per fact, fuzzy logic queries
2. **Can we detect *temporal* inconsistencies?** (timeline contradictions)
   - Research: Timeline extraction NLP models
3. **How do we scale to 10K+ documents?**
   - Test: Benchmark Qdrant/Neo4j at scale, evaluate sharding

### Product
1. **Do users want automated suggestions, or is it annoying?**
   - Validate in Phase 0 interviews
2. **What's the right granularity for version control?** (per-entity vs per-document)
   - Prototype both, user test
3. **How do we visualize large knowledge graphs?** (1000+ nodes)
   - Research: Graph clustering, hierarchical layouts

### Business
1. **Is there enterprise demand for worldbuilding tools?**
   - Interview: 5 game studios, 3 TTRPG publishers
2. **Would users pay for cloud hosting?**
   - Validate pricing with beta users

---

## 11. Appendix: Testing Strategy

### Unit Tests
- Vector search accuracy (MTEB benchmarks)
- Entity extraction precision/recall (annotated corpus)
- Inconsistency detection (synthetic contradictions)

### Integration Tests
- End-to-end ingestion pipeline
- Query → retrieval → generation → citation
- Review queue approval workflow

### Performance Tests
- Query latency under load (10 concurrent users)
- Ingestion throughput (100 documents in <1 hour)
- Graph query performance (10K nodes)

### User Acceptance Tests
- 5 beta users perform scripted tasks
- Measure: Task completion rate, time-on-task, satisfaction

---

## 12. References

### Technical Resources
- LlamaIndex documentation: https://docs.llamaindex.ai
- Neo4j GraphRAG guide: https://neo4j.com/labs/genai-ecosystem/
- Qdrant hybrid search: https://qdrant.tech/documentation/tutorials/hybrid-search/

### Comparable Systems
- WorldAnvil (structured worldbuilding, no AI)
- Notion AI (AI assistance, no coherence checking)
- Obsidian + Smart Connections plugin (local knowledge graph)

### Research Papers
- Lewis et al. (2020) - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- GraphRAG: Unlocking LLM discovery on narrative private data (Microsoft Research, 2024)

---

**Document Owner**: [Your Name]
**Last Updated**: December 24, 2025
**Status**: Draft v2.0 - Awaiting Phase 0 Validation
**Feedback**: Open GitHub issue or email team@aethercanon.dev
