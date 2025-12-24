# Canon Builder - Unified Design Document

## Project Vision

**Canon Builder** (working name, alternative: AetherForge) is an open-source, self-hosted tool for constructing and maintaining logically coherent knowledge systems. Primarily branded as a worldbuilding tool for fiction writers and game designers, it enables users to build internally consistent universes by iteratively proposing, reviewing, and canonizing logical extensions to an established body of knowledge.

The system can also be applied to research synthesis, policy analysis, and framework building—any domain where maintaining logical consistency across a growing corpus of information is valuable.

**Design Philosophy**: Human-in-the-loop verification combined with AI-powered synthesis and consistency checking. Privacy-first with local deployment as the primary option.

---

## Core Concept

Users build a "canon" (a set of established, authoritative documents) and interact with it through two primary modes:

1. **Query Mode**: Ask questions and explore existing canonical knowledge
2. **Extension Mode**: Request logical extensions that the AI generates for review

**Key Innovation**: Explicit separation between "canonical" (user-verified truth within the system) and "proposed" (AI-generated, pending review) content. This workflow maintains human oversight while leveraging AI's synthesis capabilities to build a "living world bible" that grows coherently over time.

---

## User Workflow

### 1. Initialize Canon
- Upload documents in any format (PDF, DOCX, images via OCR, TXT, Markdown, etc.)
- System parses, chunks, embeds, and indexes documents
- Automatic metadata tagging (upload date, user, document type)
- Initial knowledge graph construction from entity extraction

### 2. Query & Explore
- Natural language questions about the canon (e.g., "What are the elf kingdoms' alliances?")
- System retrieves relevant information from canonical documents only
- Answers include citations and provenance
- Visual graph interface (Obsidian-style) for exploring entity relationships

### 3. Request Extension
- User prompts logical extensions: "What are the economic implications of the magic system?" or "How would gunpowder affect this society?"
- System generates coherent proposal grounded in canonical knowledge
- Extension clearly marked as "Proposed" with coherence scoring
- Shows which canonical sources informed the generation

### 4. Review & Canonize
- User reviews proposed extension with side-by-side canonical sources
- Conflict highlighting shows potential contradictions
- User options:
  - **Accept**: Proposal becomes canonical (versioned and indexed)
  - **Edit**: Modify inline before accepting
  - **Reject**: Discard proposal
  - **Request Revision**: Ask for alternative approach
- All changes logged with user attribution

### 5. Consistency Monitoring
- Proactive agent scans for contradictions post-ingestion and during generation
- Severity-rated alerts (e.g., "Elf lifespan: 800 years (Doc A) vs. 200 years (Doc B)")
- Resolution suggestions with provenance
- Optional toggleable "suggestion engine" analyzes patterns and proposes creative extensions

### 6. Iterate & Collaborate
- Continuous canon expansion with maintained consistency
- Multi-user sync via Git/Syncthing for collaborative worldbuilding
- Change logs and conflict resolution voting
- Export to multiple formats (PDF, Markdown, JSON, static site)

---

## Core Features

### Canon Management
- **Document versioning**: Track all changes with full history
- **Provenance tracking**: Every canonical statement traces to source and user acceptance
- **Hierarchical organization**: Tag and categorize documents (geography, magic system, history, etc.)
- **Multi-format ingestion**: PDFs, images (OCR), text, DOCX, mind maps
- **Export capability**: Generate consolidated worldbuilding bible/documentation

### Coherence Engine
- **Contradiction detection**: Automated alerts for conflicting statements with sources
- **Entailment checking**: Identify logical implications of canonical facts
- **Consistency scoring**: Rate how well proposals fit existing canon (0-100 scale)
- **Gap identification**: Suggest incomplete or ambiguous areas
- **Graph-based reasoning**: Leverage knowledge graph for logical validation

### Generation Capabilities
- **Q&A**: Answer questions strictly from canonical knowledge
- **Extensions**: Generate logical developments from existing canon
- **Implications**: Derive consequences of canonical facts
- **Connections**: Identify relationships between canonical elements
- **Summaries**: Synthesize canonical knowledge on topics
- **Suggestions** (toggleable): Pattern-based creative proposals for gaps or expansions

### Knowledge Graph
- **Entity extraction**: Automated identification of characters, places, concepts, events
- **Relationship mapping**: Connections between entities with typed edges
- **Visual exploration**: Interactive graph interface (Obsidian integration)
- **Graph queries**: Enable complex reasoning about consistency
- **Provenance nodes**: Track which documents support each entity/relationship

### Review Interface
- **Side-by-side comparison**: Proposed content next to relevant canonical sources
- **Conflict highlighting**: Visual indicators of contradictions with severity ratings
- **Citation view**: See which canonical documents informed generation
- **Inline editing**: Modify proposals before accepting with markdown support
- **Comment/annotation**: Add notes explaining acceptance/rejection decisions
- **Coherence metrics**: Display consistency score and confidence levels

### Collaboration Tools
- **Multi-user access**: Support for 2-30 users per canon
- **Real-time sync**: Git + Syncthing for near-real-time collaboration
- **User roles**: Viewer/editor permissions with audit trails
- **Change logs**: Track who modified what and when
- **Conflict resolution**: Voting system for disputed canonizations
- **Shared canons**: Team workspaces with merge workflows

---

## Technical Architecture

### High-Level System Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
├─────────────────────────────────────────────────────────────────┤
│  • Obsidian (Primary: Graph view, Markdown notes)               │
│  • Web UI (Custom: Upload, review, chat via OpenWebUI/Streamlit)│
│  • API (REST/GraphQL for integrations)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Core Engine Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  • RAG Framework (LlamaIndex)                                   │
│  • Agent Orchestration (LangGraph)                              │
│    - Consistency Checker Agent                                  │
│    - Suggestion Engine Agent (toggleable)                       │
│    - Entity Extraction Agent                                    │
│  • Workflow Manager (Canonization pipeline)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       Data Storage Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  • Vector Store (Qdrant): Embeddings for semantic search        │
│  • Knowledge Graph (Neo4j): Entities, relationships, provenance │
│  • Document Store (PostgreSQL + Filesystem):                    │
│    - Canonical documents (original + processed)                 │
│    - Proposed content (pending review)                          │
│    - Version history and metadata                               │
│  • Session/State Store: User context, feature toggles           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        LLM Providers                            │
├─────────────────────────────────────────────────────────────────┤
│  • Primary: Local (Ollama - Llama-3.1-70B/Nemotron-70B)        │
│  • Fallback: Cloud APIs (Claude 3.5 Sonnet, GPT-4o)            │
│  • Embedding: BGE-large-en-v1.5 (local)                         │
└─────────────────────────────────────────────────────────────────┘
```

### Data Layer Structure
```
├── Canonical Documents Store
│   ├── Original uploads (PDFs, text, markdown, images)
│   ├── Processed/chunked content (indexed)
│   ├── Embeddings database (Qdrant vectors)
│   ├── Knowledge graph nodes (Neo4j)
│   └── Version history (Git-backed)
│
├── Proposed Content Store
│   ├── Generated extensions (pending review)
│   ├── Generation metadata (prompt, timestamp, model, coherence score)
│   ├── Review status (accepted/rejected/edited)
│   └── User annotations and comments
│
└── Metadata Store
    ├── Document relationships and provenance
    ├── Tags and hierarchical categories
    ├── User annotations and resolution votes
    ├── Coherence scores and contradiction alerts
    └── Session state and feature toggles
```

### Processing Pipeline
1. **Document Ingestion**:
   - Unstructured.io parses multimodal input (text, OCR, tables)
   - Chunk into semantic units (LlamaIndex)
   - Generate embeddings (BGE-large-en-v1.5)
   - Store in Qdrant + filesystem

2. **Knowledge Graph Construction**:
   - LLM extracts entities and relationships
   - Create Neo4j nodes with provenance links
   - Build typed edges between entities
   - Index for graph-based queries

3. **Retrieval (Query/Extension)**:
   - Hybrid search: semantic (vectors) + keyword + graph traversal
   - Retrieve top-k relevant chunks and graph neighborhoods
   - Assemble context with provenance

4. **Generation**:
   - LLM (local or API) generates response/extension
   - Grounded in retrieved canonical context
   - Includes citations and confidence scores

5. **Validation**:
   - Consistency checker agent analyzes for contradictions
   - Graph queries validate logical coherence
   - Compute coherence score (0-100)
   - Flag conflicts with severity ratings

6. **Presentation**:
   - Format for review interface with side-by-side sources
   - Highlight conflicts and show supporting evidence
   - Enable inline editing

7. **Canonization**:
   - User approves → version and commit to canonical store
   - Update vector index and knowledge graph
   - Trigger incremental re-indexing
   - Log change with user attribution

### AI Components
| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **Embedding Model** | Semantic search | BGE-large-en-v1.5 (local, 335M params) |
| **Generation Model** | Proposals, Q&A, extensions | Primary: Llama-3.1-70B (Ollama, 128k+ context)<br>Fallback: Claude 3.5 Sonnet / GPT-4o |
| **Entity Extraction** | Build knowledge graph | LLM-based with structured output (JSON schema) |
| **Consistency Checker** | Contradiction detection | LangGraph agent with graph queries + LLM reasoning |
| **Suggestion Engine** | Creative pattern proposals | LangGraph agent (toggleable) analyzing graph patterns |
| **Coherence Scoring** | Rate proposal fit | Hybrid: LLM scoring + graph similarity metrics |

### Technology Stack

#### Core Infrastructure
- **Backend**: Python 3.10+ with FastAPI
- **RAG Framework**: LlamaIndex (indexing, retrieval, agents)
- **Agent Framework**: LangGraph (workflow orchestration)
- **Vector Database**: Qdrant (self-hosted)
- **Graph Database**: Neo4j 5.24+ (self-hosted)
- **Document Storage**: PostgreSQL + local filesystem
- **Document Parsing**: Unstructured.io (multimodal)

#### User Interfaces
- **Primary**: Obsidian with RAG plugins (graph view, markdown editing)
- **Secondary**: Custom web UI (OpenWebUI or Streamlit for upload/review/chat)
- **API**: REST/GraphQL for extensibility

#### LLM Infrastructure
- **Local Models**: Ollama (manages model downloads, inference)
  - Generation: Llama-3.1-70B or Nemotron-70B (128k context)
  - Embeddings: BGE-large-en-v1.5
- **Fallback APIs**: OpenAI/Anthropic for cloud option

#### Collaboration
- **Version Control**: Git (Obsidian vaults, config)
- **Real-time Sync**: Syncthing (P2P) or self-hosted GitLab
- **Conflict Resolution**: Git merge workflows + UI voting

#### Deployment
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Optional Kubernetes for scale
- **Authentication**: OpenWebUI built-in (username/password)
- **Monitoring**: Prometheus + Grafana

### Hardware Requirements

| Tier | RAM | GPU | Storage | Use Case |
|------|-----|-----|---------|----------|
| **Minimum** | 16 GB | None (CPU-only) | 100 GB | Small canons (<50 docs), slow inference |
| **Recommended** | 64 GB | NVIDIA RTX 3060+ (12GB VRAM) | 500 GB | Medium canons (50-500 docs), fast local LLM |
| **Optimal** | 128 GB | NVIDIA RTX 4090 (24GB VRAM) | 1+ TB | Large canons (500+ docs), multi-user |

---

## Key Differentiators

### vs. Standard RAG Tools (LlamaIndex, LangChain demos)
- **Explicit canonization workflow** with versioning and provenance
- **Proactive consistency checking** via knowledge graph reasoning
- **User-in-the-loop** for all knowledge additions (no auto-canonization)
- **Creative extension mode** beyond simple Q&A

### vs. AI Writing Assistants (Sudowrite, NovelAI)
- **Strict consistency enforcement** across growing corpus
- **Structured knowledge management** with graph visualization
- **Multi-document reasoning** rather than single-context generation
- **Designed for complex, interconnected systems** not linear narratives

### vs. Worldbuilding Tools (WorldAnvil, Campfire)
- **AI-powered synthesis** and extension generation
- **Automated consistency checking** and gap identification
- **Graph-based exploration** of entity relationships
- **Local/self-hosted** with complete privacy

### vs. Knowledge Management (Obsidian, Notion)
- **AI actively generates** implications and extensions
- **Automated coherence validation** catches contradictions
- **Semantic search** beyond keyword/tag matching
- **Designed for synthesis** not just organization

---

## Development Roadmap

### Phase 1: MVP (2-3 months)
**Goal**: Demonstrate core canon workflow with basic consistency checking

**Features**:
- Document upload and parsing (text, PDF, markdown)
- Basic RAG with Q&A over canonical documents
- Extension generation with manual review
- Accept/reject workflow with versioning
- Simple contradiction detection (string matching + LLM)
- Obsidian integration for graph view
- Local LLM via Ollama (Llama-3.1-70B)

**Infrastructure**:
- Docker Compose setup (Qdrant, Neo4j, Ollama, OpenWebUI)
- LlamaIndex for indexing and retrieval
- Basic Neo4j graph for entities
- FastAPI backend with REST endpoints

**Success Metric**: Solo user can build a 5-10 document fictional world, extend it coherently, and system catches at least 50% of introduced contradictions.

**Deliverables**: Working prototype, one-click Docker deployment, basic documentation

---

### Phase 2: Enhanced Coherence & Collaboration (2-3 months)
**Goal**: Production-ready consistency checking and multi-user support

**Features**:
- Advanced contradiction detection with graph-based reasoning
- Coherence scoring (0-100) for proposals
- Citation and provenance tracking in UI
- Tagging and hierarchical categorization
- Improved review interface with conflict highlighting
- Multi-user sync via Git + Syncthing
- User roles and change logs
- Cloud API fallback (Claude/GPT-4o)

**Infrastructure**:
- LangGraph agents for consistency checking
- Enhanced Neo4j schema with provenance nodes
- PostgreSQL for metadata and user management
- Custom web UI (React/Vue) for review workflow
- Authentication and audit logging

**Success Metric**: System flags 80%+ of actual contradictions. Support 2-5 collaborative users with conflict resolution. Average canon size: 20+ documents.

**Deliverables**: Beta release, user documentation, collaboration guide

---

### Phase 3: Advanced Features (3-4 months)
**Goal**: Power user features and suggestion engine

**Features**:
- Toggleable suggestion engine (creative pattern proposals)
- Gap identification and analysis
- Multiple canon branches/timelines
- Advanced export (PDF, static sites, JSON API)
- Integration with writing tools (API, webhooks)
- Multi-format ingestion (images, OCR, mind maps)
- Mobile-responsive web UI
- Performance optimization for large canons (1000+ docs)

**Infrastructure**:
- Suggestion agent with pattern analysis
- Branch management in version control
- Export pipeline with templating
- Chunking optimization and caching
- Monitoring and analytics

**Success Metric**: Power users manage 100+ document canons. Suggestion engine adopted by 30%+ of active users. Support 10+ collaborative users per canon.

**Deliverables**: 1.0 release, API documentation, integration examples

---

### Phase 4: Optimization & Scale (Ongoing)
**Goal**: Enterprise-ready with local model parity

**Features**:
- Fine-tuned models for specific domains (fantasy, sci-fi)
- Advanced graph reasoning (inference rules, transitive relations)
- Automated testing of consistency engine
- Mobile app (iOS/Android)
- Offline-first architecture
- Custom plugin system for extensions
- Enterprise SSO and RBAC

**Infrastructure**:
- Model fine-tuning pipeline
- Kubernetes deployment option
- CDN for static assets
- Advanced caching strategies
- Telemetry and error tracking

**Success Metric**: System runs effectively on consumer hardware with local models. Coherence checking accuracy: 90%+. Support 30+ users per canon. Enterprise adoption.

**Deliverables**: Enterprise edition, white-label option, premium support

---

## Target Users & Go-to-Market

### Primary Segment (Launch Focus)
**Fiction Writers & Game Designers**
- Building fantasy/sci-fi worlds for novels, series, or games
- Need to track complex lore across multiple documents
- Value internal consistency and logical coherence
- Willing to adopt new tools for better workflows

**Channels**:
- Reddit (r/worldbuilding, r/fantasywriters, r/RPGdesign)
- Discord communities (writing, game dev, TTRPG)
- NaNoWriMo and writing forums
- Game dev conferences (GDC, IndieCade)

**Pricing Strategy**: Free/open-source with optional hosted version ($10-20/month for cloud)

---

### Secondary Segment (6-12 months)
**TTRPG Game Masters**
- Managing campaign worlds with evolving lore
- Need collaborative tools for player-generated content
- Value consistency across sessions
- Moderate tech savvy

**Channels**:
- D&D Beyond, Roll20 communities
- Actual play podcast communities
- Gaming conventions
- Partnerships with VTT platforms

**Pricing**: Free for personal use, $5-10/month for advanced features

---

### Tertiary Segment (12-24 months)
**Academic Researchers & Analysts**
- Literature review synthesis
- Policy framework building
- Maintaining research notes with consistency
- High value on accuracy and provenance

**Channels**:
- Academic Twitter/Mastodon
- University partnerships
- Research software directories
- Conference presentations

**Pricing**: Free for academics, $30-50/month for institutional licenses

---

### Future Segments (24+ months)
**Enterprise Knowledge Workers**
- Internal documentation consistency
- Multi-team knowledge bases
- Compliance and audit requirements
- Custom deployment needs

**Channels**: Direct sales, enterprise partnerships

**Pricing**: Custom enterprise licenses ($500+/month)

---

## Business Model & Monetization

### Open-Source Core (Primary Strategy)
**Philosophy**: Core functionality free forever to build community and adoption

**Revenue Streams**:
1. **Hosted Cloud Version** ($10-30/month)
   - Managed infrastructure (no Docker setup required)
   - Automatic updates and backups
   - Higher usage limits
   - Email support

2. **Premium Features** (Optional add-ons)
   - Advanced suggestion engine ($5/month)
   - Cloud API credits for fallback models ($10-20/month)
   - Priority support ($20/month)
   - Custom fine-tuned models ($50+/month)

3. **Enterprise Licensing** (Custom pricing)
   - Self-hosted with support contracts
   - SSO and advanced RBAC
   - SLA guarantees
   - Custom integrations
   - Training and onboarding

4. **Professional Services**
   - Custom deployments
   - Integration development
   - Fine-tuning services
   - Consulting for large-scale implementations

### Alternative: Freemium SaaS
If open-source adoption is slow, pivot to:
- **Free Tier**: 10 documents, 50 queries/month, cloud-only
- **Pro Tier** ($15-30/month): Unlimited docs/queries, local deployment, advanced features
- **Team Tier** ($50-100/month): Collaborative features, shared canons, admin controls

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **LLM hallucinations** | High (incorrect canon extensions) | High | Strict grounding prompts, graph validation, user review mandatory |
| **Coherence checking accuracy** | High (missed contradictions) | Medium | Start conservative, improve with user feedback, hybrid approach (graph + LLM) |
| **Local model quality** | Medium (poor experience) | Medium | Start with cloud APIs, transition only when local models sufficient (already viable with Llama-3.1-70B) |
| **Scalability (large canons)** | Medium (slow queries) | Medium | Optimize chunking, caching, incremental indexing; test early with 500+ docs |
| **Graph extraction accuracy** | Medium (wrong entities/relations) | Medium | Manual review for graph, 90%+ auto success rate, iterative improvement |

### Product Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Market fit** | High (no adoption) | Medium | Start with worldbuilding, validate with 20+ user interviews, iterate on feedback |
| **User adoption** | High (too complex) | Medium | One-click Docker setup, excellent docs, video tutorials, active community support |
| **Competition** | Medium (overtaken) | Low | Open-source defensibility, focus on unique workflow (canonization), first-mover in niche |
| **Workflow friction** | Medium (users abandon) | Medium | Obsidian integration for familiar UX, optional AI suggestions (not mandatory), export flexibility |

### Ethical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Misinformation** | High (harmful if misused) | Low | Clear disclaimers that coherence ≠ factual accuracy, avoid "truth" framing, focus on fiction |
| **Harmful use cases** | High (propaganda/conspiracy) | Low | Monitor community, terms of service for hosted version, trust open-source transparency |
| **Bias amplification** | Medium (reinforces biases) | Medium | Transparency about limitations, diverse training data for fine-tuning, user awareness |
| **Privacy concerns** | Medium (data leaks) | Low | Local-first design, encrypted Git sync, no telemetry without opt-in, open-source auditability |

---

## Success Criteria & KPIs

### Year 1 (MVP → Beta)
- **Users**: 500+ GitHub stars, 100+ active self-hosted deployments
- **Engagement**: Average canon size 15+ documents, 30% monthly retention
- **Quality**: Coherence checking catches 70%+ of contradictions (validated via user reports)
- **Community**: Active Discord (100+ members), 10+ community contributions
- **Revenue** (if hosted): $500-1000 MRR from cloud tier

### Year 2 (Beta → 1.0)
- **Users**: 5,000+ stars, 1,000+ active deployments, 100+ cloud subscribers
- **Engagement**: Average canon size 30+ documents, 40% monthly retention, 20% use suggestion engine
- **Quality**: 85%+ contradiction detection accuracy, <3% false positive rate
- **Case Studies**: 5+ professional authors/game designers using in production
- **Revenue**: $5,000-10,000 MRR (cloud + premium features)

### Year 3 (Scale & Enterprise)
- **Users**: 20,000+ stars, 5,000+ deployments, 500+ cloud subscribers, 5+ enterprise deals
- **Engagement**: Average canon 50+ documents, 50% retention, handle 100+ doc canons reliably
- **Quality**: 90%+ accuracy, local models achieve parity with cloud APIs
- **Ecosystem**: 3rd-party integrations, plugin marketplace, community-driven features
- **Revenue**: $50,000+ MRR, path to profitability or VC funding for scale

---

## Open Questions & Future Research

### Technical
1. **Quantitative coherence metrics**: How do we measure coherence beyond LLM scoring? Graph-based metrics (centrality, density)? Symbolic logic layer?
2. **Long-term consistency**: How do we prevent "canon drift" across 1000+ documents? Periodic full-canon validation? Hierarchical summarization?
3. **Multimodal canon**: How to handle images, maps, diagrams as canonical sources? Vision-language models? Specialized extractors?
4. **Real-time collaboration**: Can we support Google Docs-style simultaneous editing without conflicts? CRDT-based text editing + vector re-indexing?

### Product
1. **Ambiguity handling**: Should system flag ambiguous/contradictory *inputs* before canonization? How to resolve user-introduced contradictions?
2. **AI autonomy balance**: Should there be "auto-canonize" for low-risk extensions? Trust scoring for AI proposals? User preference learning?
3. **Canon branches**: How to manage alternate timelines/what-if scenarios? Full fork or lightweight branches? Merge strategies?
4. **Social features**: Canon sharing/discovery? Public canon repositories (like GitHub for worlds)? Forking and remixing?

### Business
1. **Open-source sustainability**: Can we fund development through hosted tier alone? Or need VC/grants? Community governance model?
2. **Enterprise market**: Is there real demand for internal knowledge consistency tools? What compliance/security features are deal-breakers?
3. **Localization**: Should we support non-English languages? Which markets prioritize worldbuilding tools?

---

## Next Steps (Pre-Development)

### Phase 0: Validation (4-6 weeks)

1. **User Research** (2 weeks)
   - Interview 15-20 worldbuilders, game designers, GMs
   - Questions: Current workflow, pain points, willingness to adopt new tools, feature priorities
   - Validate canonization workflow concept with mockups
   - Identify must-have vs. nice-to-have features

2. **Competitive Analysis** (1 week)
   - Deep dive: WorldAnvil, Campfire, LegendKeeper, World Scribe
   - Evaluate: Notion AI, Obsidian + AI plugins, custom RAG setups
   - Identify gaps and differentiation opportunities
   - Pricing analysis

3. **Technical Feasibility** (2 weeks)
   - Prototype: Minimal RAG setup with LlamaIndex + Ollama
   - Test: Contradiction detection accuracy with sample worldbuilding docs
   - Benchmark: Local LLM performance on consumer hardware
   - Estimate: Infrastructure costs for cloud version

4. **Branding & Positioning** (1 week)
   - Name finalization (Canon Builder vs. AetherForge vs. alternatives)
   - Messaging framework for worldbuilding community
   - Website mockups and landing page copy
   - Community strategy (Discord, Reddit engagement plan)

**Deliverable**: Validation report with go/no-go recommendation

---

### Phase 1 Kickoff: MVP Development (Week 1)

1. **Repository Setup**
   - GitHub repo (MIT or Apache 2.0 license)
   - Project structure (backend, frontend, docs, docker)
   - CI/CD pipeline (GitHub Actions)
   - Issue tracking and project board

2. **Architecture Spike**
   - Docker Compose file with Qdrant, Neo4j, Ollama
   - LlamaIndex hello-world with local embeddings
   - FastAPI skeleton with health endpoints
   - Basic Obsidian vault structure

3. **Documentation**
   - Architecture Decision Records (ADRs)
   - Development setup guide
   - Contribution guidelines
   - Roadmap publication

4. **Community Launch**
   - Discord server setup
   - Reddit announcement posts (r/worldbuilding, r/LocalLLaMA)
   - GitHub Discussions for feedback
   - Early adopter signup (waitlist for cloud beta)

**Deliverable**: Working repository, initial community, week 2 sprint plan

---

## Appendix: Docker Compose Example

```yaml
version: '3.8'

services:
  # Vector database for embeddings
  qdrant:
    image: qdrant/qdrant:latest
    container_name: canon_qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT_ALLOW_RECOVERY_MODE=true

  # Graph database for knowledge graph
  neo4j:
    image: neo4j:5.24-community
    container_name: canon_neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    environment:
      - NEO4J_AUTH=neo4j/canon_builder_2024
      - NEO4J_PLUGINS=["graph-data-science", "apoc"]
      - NEO4J_dbms_memory_heap_max__size=2G

  # Document parsing service
  unstructured:
    image: unstructured-io/unstructured-api:latest
    container_name: canon_unstructured
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
    environment:
      - UNSTRUCTURED_ALLOWED_MIMETYPES=application/pdf,image/png,image/jpeg,text/plain

  # Local LLM runtime
  ollama:
    image: ollama/ollama:latest
    container_name: canon_ollama
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
    # Uncomment to preload model on startup:
    # command: serve && ollama pull llama3.1:70b

  # Web UI for chat and upload
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: canon_webui
    ports:
      - "3000:8080"
    volumes:
      - openwebui_data:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_SECRET_KEY=your_secret_key_change_this
    depends_on:
      - ollama
    extra_hosts:
      - "host.docker.internal:host-gateway"

  # Backend API
  canon_api:
    build: ./backend
    container_name: canon_api
    ports:
      - "8080:8080"
    volumes:
      - ./backend:/app
      - ./data:/data
    environment:
      - QDRANT_URL=http://qdrant:6333
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=canon_builder_2024
      - OLLAMA_URL=http://ollama:11434
      - UNSTRUCTURED_URL=http://unstructured:8000
    depends_on:
      - qdrant
      - neo4j
      - ollama
      - unstructured

  # PostgreSQL for metadata
  postgres:
    image: postgres:16-alpine
    container_name: canon_postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=canon
      - POSTGRES_PASSWORD=canon_pass
      - POSTGRES_DB=canon_metadata

volumes:
  qdrant_data:
  neo4j_data:
  neo4j_logs:
  ollama_data:
  openwebui_data:
  postgres_data:

# Usage:
# 1. docker-compose up -d
# 2. docker exec -it canon_ollama ollama pull llama3.1:70b
# 3. docker exec -it canon_ollama ollama pull bge-large-en-v1.5
# 4. Access web UI at http://localhost:3000
# 5. Access Neo4j browser at http://localhost:7474
```

---

## References & Credits

**Inspired by**:
- Microsoft GraphRAG (graph-based retrieval)
- LlamaIndex/LangChain communities
- r/LocalLLaMA and r/worldbuilding discussions
- Obsidian knowledge management philosophy

**Open-source foundations**:
- LlamaIndex (RAG framework)
- LangGraph (agent orchestration)
- Neo4j (graph database)
- Qdrant (vector search)
- Ollama (local LLM runtime)
- Unstructured.io (document parsing)

**License**: MIT (for maximum community adoption)

**Governance**: Benevolent dictator (initial), transition to community governance at 1000+ stars

---

*Document Version: 1.0 (Unified from Claude + Grok designs)*
*Last Updated: December 2025*
*Status: Pre-Development - Validation Phase*
*Next Review: Post-user research (January 2026)*
