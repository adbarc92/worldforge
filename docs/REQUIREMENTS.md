# AetherCanon Builder - Core Requirements
**Extracted from CoreDesignDoc v2.0**
**Generated:** January 6, 2026

---

## 1. Functional Requirements

### FR-1: Document Ingestion
**Priority:** P0 (Critical)
**Phase:** 1 (MVP)

#### FR-1.1 File Format Support
- **REQ:** System SHALL support document upload in the following formats:
  - PDF (.pdf)
  - Microsoft Word (.docx)
  - Markdown (.md, .markdown)
  - Plain text (.txt)
- **Acceptance:** All four formats successfully parsed and stored

#### FR-1.2 Document Processing
- **REQ:** System SHALL process uploaded documents through the following pipeline:
  1. Parse document using Unstructured.io → Extract structured text + metadata
  2. Chunk text using LlamaIndex (500 tokens per chunk, 50 token overlap)
  3. Generate embeddings using BGE-large-en-v1.5
  4. Store embeddings in vector database (Qdrant/ChromaDB)
  5. Extract entities and relationships using LLM
  6. Store knowledge graph in graph database (Neo4j/SQLite)
  7. Store original document with Git versioning
  8. Create metadata entry in PostgreSQL/SQLite
- **Acceptance:** End-to-end pipeline completes without data loss

#### FR-1.3 Entity Extraction
- **REQ:** System SHALL extract the following entity types:
  - Character (people, creatures, sentient beings)
  - Location (places, buildings, regions, worlds)
  - Event (significant happenings, battles, ceremonies)
  - Concept (ideas, magic systems, philosophies, organizations)
  - Item (important objects, artifacts, weapons)
- **REQ:** System SHALL achieve ≥70% precision on entity extraction (validated against test corpus)
- **Acceptance:** Automated test suite validates precision threshold

#### FR-1.4 Performance Requirements
- **REQ:** System SHALL process documents within the following time limits:
  - Up to 50 pages: <2 minutes on recommended hardware
  - Up to 100 pages: <5 minutes on recommended hardware
- **Acceptance:** Performance benchmarks pass in CI/CD

---

### FR-2: Semantic Query with Provenance
**Priority:** P0 (Critical)
**Phase:** 1 (MVP)

#### FR-2.1 Natural Language Query
- **REQ:** System SHALL accept natural language queries about the canon
- **REQ:** System SHALL return contextually relevant answers with source citations
- **Example:** Query: "What is the political structure of Keldoria?"
  - Response includes answer + inline citations `[^1]`, `[^2]`
- **Acceptance:** User can ask questions and receive answers

#### FR-2.2 Query Processing Pipeline
- **REQ:** System SHALL process queries using the following workflow:
  1. Generate query embedding
  2. Perform similarity search in Qdrant (top-k=10)
  3. Retrieve relevant chunks + Neo4j graph context
  4. Assemble context for LLM
  5. Generate answer with inline citations
  6. Render response with expandable source excerpts
- **Acceptance:** Pipeline executes successfully for test queries

#### FR-2.3 Source Attribution
- **REQ:** Every factual claim in query responses SHALL have ≥1 source citation
- **REQ:** Citations SHALL link to specific document + page/section number
- **REQ:** System SHALL display "I don't have information on that" when query is outside canon
- **Acceptance:** Manual review of 20 test queries validates citation coverage

#### FR-2.4 Query Performance
- **REQ:** Query latency SHALL be <5 seconds (p95) on recommended hardware
- **Acceptance:** Load testing validates latency requirement

---

### FR-3: Inconsistency Detection
**Priority:** P0 (Critical)
**Phase:** 1 (MVP)

#### FR-3.1 Contradiction Detection Algorithm
- **REQ:** System SHALL detect contradictions using the following algorithm:
  1. For each new entity/relationship:
     - Perform embedding similarity search (threshold=0.85)
     - Find semantically similar existing content
  2. If similar content found:
     - Extract claims from both sources using LLM
     - Compare claims (contradictory/complementary/unrelated)
  3. If contradictory:
     - Assign severity: HIGH / MEDIUM / LOW
     - Create conflict record with evidence
- **Acceptance:** Algorithm implemented and tested

#### FR-3.2 Severity Classification
- **REQ:** System SHALL classify conflicts by severity:
  - **HIGH:** Direct factual contradiction (age, death, location)
  - **MEDIUM:** Inconsistent characterization or timeline
  - **LOW:** Ambiguous or minor detail mismatch
- **Acceptance:** Test cases validate classification logic

#### FR-3.3 Detection Accuracy
- **REQ:** System SHALL detect ≥85% of planted contradictions in test corpus
- **REQ:** False positive rate SHALL be <20%
- **Acceptance:** Validated against annotated test dataset

#### FR-3.4 Conflict Resolution
- **REQ:** System SHALL provide human-readable explanation for each conflict
- **REQ:** Users SHALL be able to mark conflicts as "not actually conflicting"
- **Acceptance:** UI allows conflict dismissal with feedback

---

### FR-4: Review Queue Interface
**Priority:** P0 (Critical)
**Phase:** 1 (MVP)

#### FR-4.1 Canonical vs Proposed Separation
- **REQ:** System SHALL maintain strict separation between:
  - **Canonical content:** User-approved entities/relationships
  - **Proposed content:** AI-generated suggestions pending review
- **REQ:** AI SHALL NEVER write directly to canonical store
- **Acceptance:** Database schema enforces separation

#### FR-4.2 Review Queue UI Components
- **REQ:** System SHALL provide the following UI views:
  - **Queue List:** Proposed items sorted by coherence score
  - **Detail View:**
    - Side-by-side: Proposed content | Related canonical content
    - Diff highlighting for edits
    - Conflict warnings (if any)
    - Actions: Approve / Edit & Approve / Reject / Defer
  - **Bulk Operations:** Approve all high-confidence (>0.9) items
- **Acceptance:** UI mockups approved, implementation functional

#### FR-4.3 Review Actions
- **REQ:** Users SHALL be able to perform the following actions:
  - **Approve:** Move proposed content to canonical store
  - **Edit & Approve:** Modify content, then move to canonical
  - **Reject:** Mark as rejected, remove from queue
  - **Defer:** Keep in pending state for later review
- **REQ:** System SHALL support undo for last 10 actions
- **Acceptance:** All actions functional with undo capability

#### FR-4.4 Queue Performance
- **REQ:** Queue SHALL load in <1 second for 100 items
- **Acceptance:** Performance testing validates requirement

---

### FR-5: Data Export
**Priority:** P1 (High)
**Phase:** 1 (MVP)

#### FR-5.1 Obsidian Export
- **REQ:** System SHALL export canonical content to Obsidian format:
  - One .md file per entity
  - YAML frontmatter with metadata
  - Wikilinks for relationships: `[[Entity Name]]`
  - graph.json file with nodes and edges
  - Directory structure by entity type
- **Acceptance:** Exported vault opens successfully in Obsidian

#### FR-5.2 Export Structure
- **REQ:** Export directory SHALL follow this structure:
  ```
  exports/
  ├── entities/
  │   ├── characters/
  │   ├── locations/
  │   ├── events/
  │   ├── concepts/
  │   └── items/
  ├── graph.json
  └── index.md
  ```
- **Acceptance:** Structure validation in automated tests

---

## 2. Non-Functional Requirements

### NFR-1: Performance
**Priority:** P0 (Critical)

#### NFR-1.1 Query Latency
- **REQ:** Query response time SHALL be <5 seconds (p95) on recommended hardware
- **Measured at:** End-to-end from user query to rendered response

#### NFR-1.2 Ingestion Throughput
- **REQ:** System SHALL ingest 50-page documents in <2 minutes
- **REQ:** System SHALL handle documents up to 100 pages

#### NFR-1.3 Concurrent Users
- **REQ:** System SHALL support 10 concurrent users without degradation
- **Measured at:** Query latency remains <5s with 10 concurrent queries

#### NFR-1.4 Uptime
- **REQ:** System SHALL maintain >99% uptime in production
- **Exclusions:** Scheduled maintenance windows

---

### NFR-2: Scalability
**Priority:** P1 (High)

#### NFR-2.1 Document Capacity
- **Phase 1 (MVP):** Support 100-500 documents per user
- **Phase 2:** Support 1,000-5,000 documents per user
- **Phase 3:** Support 10,000+ documents per user

#### NFR-2.2 Knowledge Graph Size
- **Phase 1:** Support up to 1,000 entities
- **Phase 2:** Support up to 10,000 entities
- **Phase 3:** Support 100,000+ entities

---

### NFR-3: Usability
**Priority:** P0 (Critical)

#### NFR-3.1 Setup Time
- **REQ:** New users SHALL complete setup in <30 minutes
- **Includes:** Docker installation, service startup, first document upload

#### NFR-3.2 Learning Curve
- **REQ:** Users SHALL be able to perform core workflows without documentation
- **Core workflows:** Upload document, query canon, review entity

#### NFR-3.3 User Satisfaction
- **Phase 1 Target:** User satisfaction score ≥7/10
- **Phase 2 Target:** NPS ≥40

---

### NFR-4: Reliability
**Priority:** P0 (Critical)

#### NFR-4.1 Data Integrity
- **REQ:** System SHALL prevent data loss through:
  - Automated backups every 6 hours
  - Git-based document versioning
  - PostgreSQL/SQLite WAL archiving
  - Transaction rollback on errors

#### NFR-4.2 Error Handling
- **REQ:** System SHALL gracefully handle errors:
  - Invalid file formats → Clear error message
  - LLM failures → Retry with exponential backoff
  - Database connection loss → Queue operations for retry

#### NFR-4.3 Data Loss Tolerance
- **REQ:** Data loss incidents SHALL occur in <5% of operations
- **Phase 2 Target:** <1% data loss incidents

---

### NFR-5: Security
**Priority:** P1 (High)

#### NFR-5.1 Local-First Architecture
- **REQ:** System SHALL work offline after initial setup
- **REQ:** User data SHALL remain on local infrastructure

#### NFR-5.2 Authentication (Phase 2)
- **REQ:** Multi-user deployments SHALL require authentication
- **REQ:** Support role-based access control (owner/editor/viewer)

#### NFR-5.3 Data Privacy
- **REQ:** System SHALL NOT send user data to external services without explicit consent
- **Exception:** Optional cloud LLM APIs (Claude/GPT-4) when configured

---

### NFR-6: Maintainability
**Priority:** P1 (High)

#### NFR-6.1 Code Quality
- **REQ:** Unit test coverage SHALL be ≥70%
- **REQ:** Code SHALL pass linting (Ruff for Python)
- **REQ:** API SHALL have OpenAPI documentation

#### NFR-6.2 Modularity
- **REQ:** System components SHALL be replaceable:
  - Vector DB: Qdrant ↔ ChromaDB ↔ Milvus
  - Graph DB: Neo4j ↔ SQLite + NetworkX
  - LLM: Ollama ↔ Claude API ↔ OpenAI API

#### NFR-6.3 Logging
- **REQ:** System SHALL log all errors with stack traces
- **REQ:** System SHALL log performance metrics (query latency, ingestion time)

---

## 3. Technical Requirements

### TR-1: Hardware Requirements
**Priority:** P0 (Critical)

#### TR-1.1 Minimal Configuration
- **CPU:** 4-core processor
- **RAM:** 16 GB
- **GPU:** None (CPU-only)
- **Storage:** 100 GB
- **Model Support:** Mistral-7B-Instruct (Q4)
- **Use Case:** 10-50 documents, slower queries

#### TR-1.2 Recommended Configuration
- **CPU:** 8-core processor
- **RAM:** 32 GB
- **GPU:** RTX 3060 (12GB) or equivalent
- **Storage:** 500 GB
- **Model Support:** Llama3.1-8B (Q5)
- **Use Case:** 100-500 documents, <5s queries

#### TR-1.3 Optimal Configuration
- **CPU:** 16-core processor
- **RAM:** 64 GB
- **GPU:** RTX 4090 (24GB) or equivalent
- **Storage:** 1 TB
- **Model Support:** Mixtral-8x7B / Llama3.1-70B (Q4)
- **Use Case:** 1,000+ documents, multi-user support

---

### TR-2: Software Stack
**Priority:** P0 (Critical)

#### TR-2.1 Backend Framework
- **Language:** Python 3.11+
- **Web Framework:** FastAPI 0.104+
- **RAG Framework:** LlamaIndex 0.9+
- **Agent Framework:** LangGraph 0.0.30+ (Phase 1: Optional, Phase 2: Required)

#### TR-2.2 Databases
- **Metadata:** PostgreSQL 16+ OR SQLite 3.35+
- **Vector Store:** Qdrant 1.7+ OR ChromaDB 0.4+
- **Graph Store:** Neo4j 5.26 OR SQLite + NetworkX 3.2+

#### TR-2.3 AI Components
- **LLM Runtime:** Ollama 0.1.17+ AND/OR Claude API
- **Embedding Model:** BGE-large-en-v1.5 (1024 dimensions)
- **Document Parser:** Unstructured.io 0.10+

#### TR-2.4 Frontend
- **Framework:** Streamlit 1.29+ (Phase 1) OR React (Phase 2+)
- **Visualization:** Plotly 5.18+, NetworkX 3.2+

---

### TR-3: Deployment
**Priority:** P0 (Critical)

#### TR-3.1 Containerization
- **REQ:** System SHALL deploy via Docker Compose
- **REQ:** One-command startup: `docker-compose up -d`
- **Services:** app, postgres/sqlite, qdrant/chromadb, neo4j (optional), ollama

#### TR-3.2 Environment Configuration
- **REQ:** System SHALL use environment variables for configuration
- **REQ:** Provide .env.example template
- **REQ:** Support development and production configs

---

### TR-4: APIs
**Priority:** P0 (Critical)

#### TR-4.1 REST API Endpoints
**Documents:**
- `POST /api/documents/upload` - Upload and process document
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

**Query:**
- `POST /api/query` - Submit semantic query
- `GET /api/query/history` - Get query history

**Review:**
- `GET /api/review/queue` - Get proposed content
- `POST /api/review/{id}/approve` - Approve item
- `POST /api/review/{id}/reject` - Reject item
- `PUT /api/review/{id}/edit` - Edit item

**Export:**
- `POST /api/export/obsidian` - Generate Obsidian export
- `GET /api/export/{id}/download` - Download export

**Health:**
- `GET /health` - Health check endpoint

#### TR-4.2 API Standards
- **REQ:** All APIs SHALL return standardized response format:
  ```json
  {
    "success": true,
    "data": {...},
    "metadata": {...},
    "errors": []
  }
  ```
- **REQ:** All APIs SHALL have OpenAPI 3.0 documentation
- **REQ:** All APIs SHALL use proper HTTP status codes

---

## 4. Data Requirements

### DR-1: Data Models
**Priority:** P0 (Critical)

#### DR-1.1 Document Schema
```sql
documents (
  id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  original_filename TEXT,
  file_path TEXT NOT NULL,
  file_type TEXT,  -- pdf, docx, md, txt
  upload_date TIMESTAMP,
  status TEXT DEFAULT 'active',  -- active, archived, processing
  git_commit_hash TEXT,
  metadata JSON,
  chunk_count INTEGER,
  entity_count INTEGER
)
```

#### DR-1.2 Entity Schema
```sql
entities (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,  -- character, location, event, concept, item
  canonical_description TEXT,
  first_mentioned_doc UUID REFERENCES documents(id),
  confidence_score REAL,
  created_at TIMESTAMP,
  metadata JSON
)
```

#### DR-1.3 Relationship Schema
```sql
relationships (
  id UUID PRIMARY KEY,
  source_entity UUID REFERENCES entities(id),
  target_entity UUID REFERENCES entities(id),
  relation_type TEXT,  -- located_in, allied_with, created_by, etc.
  evidence_doc UUID REFERENCES documents(id),
  evidence_excerpt TEXT,
  confidence_score REAL,
  created_at TIMESTAMP,
  metadata JSON
)
```

#### DR-1.4 Proposed Content Schema
```sql
proposed_content (
  id UUID PRIMARY KEY,
  type TEXT NOT NULL,  -- entity, relationship, document_extension
  content JSON NOT NULL,
  generation_metadata JSON,  -- {model, prompt, timestamp}
  coherence_score REAL,
  conflicts JSON,  -- [{severity, with_entity_id, reason}]
  review_status TEXT DEFAULT 'pending',  -- pending, approved, rejected
  reviewed_by TEXT,
  reviewed_at TIMESTAMP,
  created_at TIMESTAMP
)
```

#### DR-1.5 Conflict Schema
```sql
conflicts (
  id UUID PRIMARY KEY,
  entity_id_1 UUID REFERENCES entities(id),
  entity_id_2 UUID REFERENCES entities(id),
  conflict_type TEXT,  -- contradiction, inconsistent_characterization, timeline_mismatch
  severity TEXT,  -- high, medium, low
  description TEXT,
  evidence_1 TEXT,
  evidence_2 TEXT,
  source_doc_1_id UUID REFERENCES documents(id),
  source_doc_2_id UUID REFERENCES documents(id),
  status TEXT DEFAULT 'unresolved',  -- unresolved, not_a_conflict, resolved
  resolved_by TEXT,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP
)
```

---

## 5. Quality Requirements

### QR-1: Testing Requirements
**Priority:** P0 (Critical)

#### QR-1.1 Unit Tests
- **Coverage Target:** ≥70% code coverage
- **Focus Areas:**
  - Entity extraction precision/recall (annotated corpus)
  - Vector search accuracy (MTEB benchmarks)
  - Inconsistency detection (synthetic contradictions)

#### QR-1.2 Integration Tests
- **REQ:** Test end-to-end workflows:
  - Document ingestion pipeline
  - Query → retrieval → generation → citation
  - Review queue approval workflow

#### QR-1.3 Performance Tests
- **REQ:** Validate performance requirements:
  - Query latency under load (10 concurrent users)
  - Ingestion throughput (100 documents in <1 hour)
  - Graph query performance (10K nodes in Neo4j)

#### QR-1.4 User Acceptance Tests
- **REQ:** 5 beta users perform scripted tasks
- **Metrics:** Task completion rate, time-on-task, satisfaction score

---

## 6. Constraints

### CN-1: Technical Constraints
**Priority:** P0 (Critical)

#### CN-1.1 Local-First Architecture
- **CONSTRAINT:** System MUST work without internet after initial setup
- **Rationale:** Privacy, offline capability, user control

#### CN-1.2 Open Source
- **CONSTRAINT:** Community edition MUST be MIT licensed
- **CONSTRAINT:** No vendor lock-in (all components replaceable)

#### CN-1.3 Hardware Limitations
- **CONSTRAINT:** Minimal config MUST run on consumer hardware (16GB RAM)
- **CONSTRAINT:** No cloud dependencies for core functionality

---

### CN-2: Business Constraints
**Priority:** P1 (High)

#### CN-2.1 Phase 0 Validation Required
- **CONSTRAINT:** Phase 1 development SHALL NOT begin until:
  - 15 user interviews completed
  - 8/15 users willing to beta test
  - Technical PoC validates feasibility

#### CN-2.2 No SaaS in v1.0
- **CONSTRAINT:** Version 1.0 SHALL be self-hosted only
- **Rationale:** Focus on product-market fit before scaling

---

### CN-3: Legal Constraints
**Priority:** P0 (Critical)

#### CN-3.1 Data Privacy
- **CONSTRAINT:** System SHALL NOT transmit user data without consent
- **CONSTRAINT:** System SHALL be GDPR compliant (data export, deletion)

#### CN-3.2 License Compliance
- **CONSTRAINT:** All dependencies MUST use permissive licenses (MIT, Apache, BSD)
- **CONSTRAINT:** No GPL dependencies in core system

---

## 7. Success Criteria

### Phase 1 (MVP) - 3 Months
- [ ] 5 beta users actively using system
- [ ] Average canon size: 20+ documents per user
- [ ] Inconsistency detection precision >80%
- [ ] User satisfaction score ≥7/10
- [ ] Query latency p95 <5s
- [ ] System uptime >99%

### Phase 2 (Collaboration) - 6 Months
- [ ] 100 active users
- [ ] 10 collaborative teams (2-4 users each)
- [ ] 60% monthly retention rate
- [ ] <5% data loss incidents
- [ ] NPS ≥40

### Phase 3 (Maturity) - 12 Months
- [ ] 1,000 active users
- [ ] 50,000 documents indexed across all users
- [ ] 10 open-source contributors
- [ ] 50+ GitHub stars
- [ ] Featured in 2+ worldbuilding podcasts/blogs

---

## 8. Dependencies & Assumptions

### Assumptions
1. Users are comfortable with Docker and basic command-line operations
2. Users have hardware meeting minimal requirements (16GB RAM minimum)
3. LLM quality (Mistral-7B, Llama3.1-8B) is sufficient for entity extraction
4. Embedding similarity search is effective for contradiction detection
5. Users prefer local-first architecture over cloud SaaS

### External Dependencies
1. Ollama project continues active development
2. LlamaIndex maintains backward compatibility
3. Qdrant/ChromaDB remain open-source
4. Neo4j community edition remains free
5. BGE-large-en-v1.5 model remains available

---

## 9. Risk Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM Hallucinations | High | High | Conservative prompting, always show sources, user review required |
| Poor Inconsistency Detection | High | Medium | Start with high-precision/low-recall, user feedback loop |
| User Setup Complexity | High | Medium | One-command Docker Compose, video tutorials |
| Data Loss | Critical | Low | Automated backups, Git versioning, WAL archiving |
| Low User Adoption | High | Medium | Phase 0 validation reduces risk by 80% |

---

## 10. Traceability Matrix

| Requirement ID | Phase | Priority | Test Coverage | Status |
|----------------|-------|----------|---------------|--------|
| FR-1 (Document Ingestion) | 1 | P0 | Unit + Integration | ✅ Implemented |
| FR-2 (Semantic Query) | 1 | P0 | Integration + Performance | 🚧 In Progress |
| FR-3 (Inconsistency Detection) | 1 | P0 | Unit + UAT | 📅 Planned |
| FR-4 (Review Queue) | 1 | P0 | Integration + UAT | 📅 Planned |
| FR-5 (Export) | 1 | P1 | Integration | 📅 Planned |

---

**Document Control:**
- **Version:** 1.0
- **Extracted From:** CoreDesignDoc v2.0
- **Author:** AetherCanon Builder Team
- **Last Updated:** January 6, 2026
- **Status:** Active - Phase 1 Development
- **Next Review:** End of Phase 1 (3 months)
