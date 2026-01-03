# Canon Builder - Final Unified Design Document

## Executive Summary

**Canon Builder** is an open-source, self-hosted tool for constructing and maintaining logically coherent knowledge systems. Positioned primarily for worldbuilding (fiction writers, game designers, TTRPG enthusiasts), it extends to research synthesis, policy analysis, and any domain requiring logical consistency across growing corpora.

**Core Innovation**: Explicit separation of "canonical" (user-verified) from "proposed" (AI-generated, pending review) content through a human-in-the-loop workflow. This creates a "living knowledge base" that grows coherently while maintaining strict consistency guarantees.

**Architecture**: RAG-based system combining vector search (Qdrant), knowledge graphs (Neo4j), and local LLMs (Ollama) with cloud fallback. Primary interface through Obsidian for familiar graph-based exploration; secondary web UI for upload/review workflows.

**Philosophy**: Privacy-first, open-source core, community-driven development with sustainable monetization through optional hosted services.

---

## 1. Project Vision & Goals

### Core Mission
Enable users to build complex, internally consistent knowledge systems that grow over time without accumulating contradictions, with AI assistance that enhances rather than replaces human judgment.

### Key Goals
1. **Logical Coherence**: Maintain strict internal consistency across unlimited document growth
2. **Human Oversight**: All canonization requires explicit user approval (no auto-acceptance)
3. **Flexibility**: Accept any document format (PDF, DOCX, images, markdown, OCR)
4. **Visual Exploration**: Graph-based interface for intuitive relationship discovery
5. **Collaboration**: Multi-user support with conflict resolution and audit trails
6. **Privacy**: Fully local/self-hosted by default, cloud optional
7. **Intelligence**: Proactive contradiction detection, gap identification, and pattern-based suggestions
8. **Accessibility**: One-click Docker deployment, minimal technical barriers

### Target Users

**Primary (Launch Focus)**
- Fiction writers building fantasy/sci-fi universes
- Game designers creating lore for TTRPGs and video games
- Game Masters managing evolving campaign worlds

**Secondary (6-12 months)**
- Academic researchers synthesizing literature
- Policy analysts building coherent frameworks
- Knowledge workers maintaining documentation consistency

**Tertiary (12-24+ months)**
- Philosophy/theory builders
- Enterprise knowledge management
- Collaborative worldview synthesis

---

## 2. Core Concept & Workflow

### The Canon/Proposed Dichotomy

**Canonical Content**:
- User-verified, authoritative knowledge
- Forms the ground truth for all queries and generations
- Versioned with full provenance tracking
- Immutable except through explicit user action

**Proposed Content**:
- AI-generated extensions, implications, or suggestions
- Clearly marked as pending review
- Includes coherence scores and supporting evidence
- Must be explicitly approved to become canonical

### User Workflow

#### 1. Initialize Canon
- Upload initial documents (any format)
- System parses, chunks, embeds (BGE-large-en-v1.5)
- Extract entities/relationships → knowledge graph (Neo4j)
- Store vectors (Qdrant), metadata (PostgreSQL)
- All content marked "canonical" by default for user uploads

#### 2. Query & Explore
- Natural language questions about canon: "What are the economic impacts of the magic system?"
- Hybrid retrieval: semantic (vectors) + keyword + graph traversal
- Answers strictly from canonical sources with citations
- Graph visualization shows entity relationships (Obsidian)
- Provenance: hover/click to see source documents

#### 3. Request Extension
- User prompts: "What happens if gunpowder is introduced?" or "Suggest implications of the recent war"
- System retrieves relevant canonical context
- LLM generates proposal grounded in canon
- Extension marked "Proposed" with:
  - Coherence score (0-100)
  - Supporting canonical sources
  - Potential contradictions flagged

#### 4. Review & Canonize
- Side-by-side interface: proposal vs. canonical sources
- Conflict highlighting with severity ratings
- User actions:
  - **Accept**: Proposal → canonical (versioned, re-indexed)
  - **Edit**: Inline modification before accepting
  - **Reject**: Discard with optional feedback
  - **Request Revision**: Provide guidance for alternative generation
- All decisions logged with attribution

#### 5. Consistency Monitoring
- **Proactive scanning**: Post-ingestion and during generation
- **Contradiction alerts**: "Character age: 35 (Doc A) vs. 42 (Doc B)"
- **Severity ratings**: Critical (logical impossibility) vs. Minor (ambiguity)
- **Resolution suggestions**: Reconcile via new canonical clarification

#### 6. Iterate & Collaborate
- Continuous canon growth with maintained consistency
- Multi-user sync (Git + Syncthing)
- Conflict resolution via voting/discussion
- Export options: PDF, markdown, JSON, static sites

---

## 3. Technical Architecture

### System Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
├─────────────────────────────────────────────────────────────────┤
│  • Obsidian (Primary): Graph view, markdown editing             │
│  • Web UI (Secondary): Upload, review, chat (OpenWebUI)         │
│  • API: REST for integrations, webhooks                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Core Engine Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  • RAG Framework: LlamaIndex (indexing, retrieval)              │
│  • Agent Orchestration: LangGraph (workflows)                   │
│    - Consistency Checker Agent                                  │
│    - Entity Extraction Agent                                    │
│    - Suggestion Engine Agent (toggleable)                       │
│  • Canonization Pipeline: Review → Approve → Index → Graph      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       Data Storage Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  • Qdrant: Vector embeddings for semantic search                │
│  • Neo4j: Knowledge graph (entities, relationships, provenance) │
│  • PostgreSQL: Metadata, user management, audit logs            │
│  • Filesystem: Original documents + processed chunks            │
│  • Git: Version control for canonical content                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        LLM Providers                            │
├─────────────────────────────────────────────────────────────────┤
│  • Primary: Ollama (local) - Llama-3.1-70B, 128k context        │
│  • Fallback: Cloud APIs - Claude 3.5 Sonnet, GPT-4o             │
│  • Embeddings: BGE-large-en-v1.5 (local, 335M params)           │
└─────────────────────────────────────────────────────────────────┘
```

### Data Layer Structure
```
├── Canonical Documents Store
│   ├── originals/          # Raw uploads (PDFs, DOCX, images)
│   ├── processed/          # Cleaned, chunked text
│   ├── embeddings/         # Qdrant vectors (by doc ID)
│   ├── graph/              # Neo4j nodes/edges (entities, relations)
│   └── versions/           # Git history with user attribution
│
├── Proposed Content Store
│   ├── extensions/         # Pending AI generations
│   ├── metadata/           # Prompt, timestamp, model, coherence score
│   ├── status/             # Accepted, rejected, edited flags
│   └── annotations/        # User comments on proposals
│
├── Metadata Store (PostgreSQL)
│   ├── documents           # ID, title, upload_date, user, tags
│   ├── users               # ID, name, role, permissions
│   ├── audit_logs          # Action, timestamp, user, details
│   ├── tags                # Hierarchical categories
│   ├── coherence_scores    # Proposal ID, score, flags
│   └── session_state       # User preferences, feature toggles
│
└── Configuration
    ├── rag_config.yaml     # Chunking, embedding, retrieval params
    ├── agent_config.yaml   # LangGraph workflows, toggles
    └── user_prefs.yaml     # Per-user settings (suggestion level, etc.)
```

### Processing Pipeline

#### Ingestion Pipeline
```
Upload → Parse (Unstructured.io) → Chunk (LlamaIndex, 512 tokens, 50 overlap)
  → Embed (BGE-large-en-v1.5) → Store (Qdrant + Filesystem)
  → Extract Entities (LLM + structured output) → Build Graph (Neo4j)
  → Add Provenance (link nodes to source docs) → Mark Canonical
```

#### Query Pipeline
```
Question → Embed Query → Hybrid Search:
  - Semantic: Top-k vectors (Qdrant, k=10)
  - Keyword: BM25 fallback (Qdrant)
  - Graph: Traverse related entities (Neo4j, depth=2)
→ Assemble Context (500-2000 tokens) → LLM Generate Answer
→ Add Citations → Return to User
```

#### Extension Pipeline
```
Prompt → Retrieve Canonical Context (same as Query)
→ LLM Generate Proposal (with grounding instructions)
→ Consistency Check:
  - Graph Query: Find related entities, check for conflicts
  - LLM Analysis: "Does this contradict existing canon?"
  - Compute Coherence Score (0-100, hybrid: LLM + graph similarity)
→ Flag Contradictions (if any, with severity)
→ Present for Review (side-by-side with sources)
→ User Decision:
  - Accept → Canonize (re-index, update graph, version)
  - Edit → Modify → Canonize
  - Reject → Log and discard
  - Revise → Regenerate with feedback
```

#### Consistency Monitoring Pipeline
```
Trigger: Post-ingestion, nightly scan, or manual request
→ For Each Canonical Document Pair:
  - Graph Query: Find overlapping entities
  - LLM Compare: "Are these statements contradictory?"
→ Generate Alerts:
  - Critical: Logical impossibility (age, dates, mutually exclusive)
  - Major: Factual conflict (different values for same property)
  - Minor: Ambiguity or potential inconsistency
→ Store Alerts (with sources, suggested resolutions)
→ Notify Users (UI dashboard, optional email)
```

### AI Components

| Component | Purpose | Implementation | Notes |
|-----------|---------|----------------|-------|
| **Embedding Model** | Semantic search | BGE-large-en-v1.5 (local, 335M) | Optimized for narrative text |
| **Generation Model** | Q&A, extensions, proposals | Llama-3.1-70B (Ollama, 128k ctx) | Cloud fallback: Claude/GPT-4o |
| **Entity Extractor** | Build knowledge graph | LLM with JSON schema output | ~90% accuracy, manual review |
| **Consistency Checker** | Contradiction detection | LangGraph agent (graph + LLM) | Target: 80-90% recall |
| **Coherence Scorer** | Rate proposal fit | Hybrid: LLM (0-100) + graph similarity | Weighted average |
| **Suggestion Engine** | Creative pattern proposals | LangGraph agent (toggleable) | Analyzes graph for gaps/themes |

### Technology Stack

**Core Infrastructure**
- Backend: Python 3.10+, FastAPI
- RAG Framework: LlamaIndex 0.10+
- Agent Framework: LangGraph 0.2+
- Vector DB: Qdrant (self-hosted)
- Graph DB: Neo4j 5.24+ (Community Edition)
- Document Storage: PostgreSQL 16 + local filesystem
- Parsing: Unstructured.io

**User Interfaces**
- Primary: Obsidian (desktop app) with plugins:
  - Smart Random Note
  - Dataview
  - Custom RAG plugin (TBD)
- Secondary: OpenWebUI (web-based chat/upload)
- API: FastAPI REST endpoints

**LLM Infrastructure**
- Local: Ollama 0.3+ (manages models)
  - Llama-3.1-70B or Nemotron-70B (generation)
  - BGE-large-en-v1.5 (embeddings)
- Cloud Fallback: Anthropic/OpenAI APIs (user-provided keys)

**Collaboration**
- Version Control: Git (canonical content)
- Sync: Syncthing (real-time P2P) or GitLab (self-hosted)
- Conflict Resolution: Git merge + UI voting

**Deployment**
- Containerization: Docker + Docker Compose
- Orchestration: Optional Kubernetes (enterprise)
- Monitoring: Prometheus + Grafana (metrics, alerts)
- Logging: Structured JSON logs (FastAPI → Elasticsearch)

### Hardware Requirements

| Tier | RAM | GPU | Storage | Use Case | Inference Speed |
|------|-----|-----|---------|----------|-----------------|
| **Minimum** | 16 GB | None (CPU) | 100 GB | <50 docs, single user | ~5 tokens/sec (slow) |
| **Recommended** | 64 GB | RTX 3060 (12GB) | 500 GB | 50-500 docs, 2-5 users | ~40 tokens/sec |
| **Optimal** | 128 GB | RTX 4090 (24GB) | 1+ TB | 500+ docs, 10+ users | ~80 tokens/sec |

**Note**: CPU-only viable with quantized models (Q4_K_M) but significantly slower. GPU strongly recommended for production use.

---

## 4. Features & Capabilities

### Core Features (MVP - Phase 1)

**Canon Management**
- Document upload (PDF, DOCX, TXT, Markdown, images via OCR)
- Automatic chunking and indexing
- Full version history (Git-backed)
- Hierarchical tagging (manual or AI-suggested)
- Provenance tracking (every fact → source document)
- Export: Markdown, JSON

**Query & Retrieval**
- Natural language Q&A over canonical documents
- Hybrid search (semantic + keyword + graph)
- Citation included in all answers
- Graph visualization of entity relationships

**Extension Generation**
- User-prompted logical extensions
- Grounded in canonical context
- Proposals clearly marked "Pending Review"
- Inline editing before canonization

**Consistency Checking**
- Basic contradiction detection (same entity, conflicting properties)
- Alerts with source citations
- Manual resolution workflow

**Review Interface**
- Side-by-side: proposal vs. canonical sources
- Accept/Edit/Reject actions
- Version control on approval

### Advanced Features (Phase 2-3)

**Enhanced Coherence Engine**
- Coherence scoring (0-100) for all proposals
- Severity-rated contradiction alerts (Critical, Major, Minor)
- Graph-based reasoning for complex contradictions
- Gap identification (incomplete or ambiguous areas)
- Entailment checking (automatic inference of implications)

**Suggestion Engine (Toggleable)**
- Pattern analysis: detect recurring themes/motifs
- Gap suggestions: "No information on economy of Region X"
- Creative prompts: "Betrayal theme recurs—suggest spy subplot?"
- Configurable creativity level (conservative ↔ experimental)
- YAML toggle: `suggestions.enabled: true/false`

**Collaboration Tools**
- Multi-user access (2-30 concurrent)
- User roles: Viewer (read-only), Editor (propose), Admin (canonize)
- Real-time sync via Syncthing or Git push/pull
- Conflict resolution: Side-by-side diffs with voting
- Change logs: Audit trail with user attribution
- Comments/annotations on proposals

**Advanced Export**
- PDF with formatting (worldbuilding bible)
- Static website generation (MkDocs or Hugo)
- JSON API for external tools
- Graph export (GraphML, Cypher)

**Integration & Extensibility**
- REST API for third-party tools
- Webhooks for automation (e.g., Discord notifications)
- Plugin system for custom agents/extractors
- Import from WorldAnvil, Campfire, etc.

### Security & Privacy

**Authentication**
- Built-in: Username/password (OpenWebUI)
- Optional: OAuth2 (Google, GitHub)
- Enterprise: SSO via SAML/OIDC

**Authorization**
- Role-based access control (RBAC)
- Document-level permissions (future)
- Audit logs for all actions

**Data Privacy**
- Local-first: No data sent externally by default
- Cloud fallback: Explicit user opt-in with API keys
- Encrypted Git sync (SSH keys or HTTPS)
- No telemetry without explicit consent
- Open-source auditability

**Ethical Safeguards**
- Prominent disclaimers: "Coherence ≠ Factual Truth"
- Non-fiction use cases: Require user verification
- Bias awareness: Transparency about model limitations
- Misuse monitoring: Community reporting for hosted version

---

## 5. Development Roadmap

### Phase 0: Validation (4-6 weeks) - Pre-Development

**Objectives**: Validate market demand, refine workflow, finalize technical choices

**Activities**:
1. **User Research** (2 weeks)
   - Interview 15-20 worldbuilders, game designers, GMs
   - Questions: Current tools, pain points, willingness to adopt, feature priorities
   - Show mockups of canonization workflow
   - Identify must-haves vs. nice-to-haves

2. **Competitive Analysis** (1 week)
   - Deep dive: WorldAnvil, Campfire, LegendKeeper, Notion AI
   - Evaluate: Custom RAG setups, Obsidian plugins
   - Pricing models and user feedback
   - Identify differentiation opportunities

3. **Technical Feasibility** (2 weeks)
   - Prototype: Minimal RAG (LlamaIndex + Ollama)
   - Test: Contradiction detection on sample docs (accuracy baseline)
   - Benchmark: Local LLM performance on target hardware
   - Cost estimate: Cloud infrastructure for hosted version

4. **Branding & Positioning** (1 week)
   - Name finalization: Canon Builder vs. alternatives
   - Messaging: "Build coherent worlds, not contradictory lore"
   - Landing page design
   - Community strategy (Discord, Reddit)

**Deliverables**: Validation report, go/no-go decision, refined requirements

---

### Phase 1: MVP (2-3 months)

**Goal**: Working prototype demonstrating core canonization workflow

**Features**:
- Document ingestion (PDF, TXT, Markdown)
- Basic RAG with Q&A
- Extension generation with review
- Accept/reject workflow with Git versioning
- Simple contradiction detection (keyword + LLM)
- Obsidian integration (vault structure, basic graph)
- Local LLM (Llama-3.1-70B via Ollama)

**Infrastructure**:
- Docker Compose: Qdrant, Neo4j, Ollama, OpenWebUI, PostgreSQL
- FastAPI backend with REST endpoints
- LlamaIndex for indexing/retrieval
- Basic Neo4j schema (entities, relationships)
- Git for version control

**Success Metrics**:
- Solo user can build 5-10 doc fictional world
- Extend coherently with 3+ proposals
- System catches 50%+ of introduced contradictions
- One-click setup works on recommended hardware

**Deliverables**: GitHub repo, Docker Compose file, README, demo video

---

### Phase 2: Enhanced Coherence & Collaboration (2-3 months)

**Goal**: Production-ready with robust consistency checking and multi-user support

**Features**:
- Advanced contradiction detection (graph-based)
- Coherence scoring (0-100) with explanations
- Severity-rated alerts (Critical, Major, Minor)
- Citation/provenance tracking in UI
- Tagging and categorization
- Improved review interface (side-by-side, conflict highlighting)
- Multi-user sync (Git + Syncthing)
- User roles and change logs
- Cloud API fallback (optional user keys)

**Infrastructure**:
- LangGraph agents (consistency checker, entity extractor)
- Enhanced Neo4j schema (provenance nodes, typed edges)
- PostgreSQL for metadata and users
- Custom web UI (React or Vue) for review workflow
- Authentication and audit logging
- Monitoring (Prometheus, Grafana)

**Success Metrics**:
- 80%+ contradiction detection recall
- <5% false positive rate
- Support 2-5 collaborative users
- Average canon size: 20+ documents
- User satisfaction: 8/10+ on usability survey

**Deliverables**: Beta release, user documentation, collaboration guide, community Discord

---

### Phase 3: Advanced Features (3-4 months)

**Goal**: Power user features and ecosystem growth

**Features**:
- Toggleable suggestion engine (pattern analysis)
- Gap identification and creative prompts
- Multiple canon branches/timelines
- Advanced export (PDF, static sites, API)
- Multi-format ingestion (images, OCR, mind maps)
- Integration API and webhooks
- Mobile-responsive web UI
- Performance optimization (1000+ docs)

**Infrastructure**:
- Suggestion engine agent (LangGraph)
- Branch management (Git branches + UI)
- Export pipeline (Jinja2 templates, Pandoc)
- Chunking optimization and caching
- API rate limiting and authentication
- Analytics dashboard

**Success Metrics**:
- Handle 100+ document canons reliably
- Suggestion engine adopted by 30%+ active users
- Support 10+ collaborative users per canon
- 5+ case studies (professional authors/designers)
- Community contributions: 10+ merged PRs

**Deliverables**: 1.0 release, API docs, integration examples, plugin SDK

---

### Phase 4: Scale & Enterprise (Ongoing)

**Goal**: Enterprise-ready, local model parity, sustainable ecosystem

**Features**:
- Fine-tuned models for specific domains
- Advanced graph reasoning (inference rules)
- Automated consistency testing
- Mobile apps (iOS/Android)
- Offline-first architecture
- Custom plugin marketplace
- Enterprise SSO and RBAC
- White-label option

**Infrastructure**:
- Model fine-tuning pipeline (LoRA, QLoRA)
- Kubernetes deployment option
- CDN for static assets
- Advanced caching (Redis)
- Telemetry and error tracking (opt-in)
- Distributed architecture for scale

**Success Metrics**:
- 90%+ coherence checking accuracy
- Local models match cloud API quality
- Support 30+ users per canon
- 5+ enterprise deals ($500+/month each)
- Self-sustaining community governance

**Deliverables**: Enterprise edition, white-label, premium support tiers

---

## 6. Business Model & Monetization

### Primary Strategy: Open-Source Core + Hosted Premium

**Free Tier (Open-Source)**
- Unlimited documents, queries, users
- Full feature set (except cloud-only)
- Self-hosted deployment
- Community support (Discord, GitHub)
- MIT License for maximum adoption

**Revenue Streams**:

1. **Hosted Cloud Version** ($10-30/month)
   - No Docker setup required
   - Managed infrastructure and backups
   - Automatic updates
   - Higher resource limits (more concurrent users)
   - Email support (48-hour response)
   - Cloud API credits included (fallback)

2. **Premium Features (Add-ons)**
   - Advanced suggestion engine: $5/month
   - Cloud API credits (beyond free tier): $10-20/month
   - Priority support (24-hour): $20/month
   - Custom fine-tuned models: $50+/month
   - White-label branding: $100/month

3. **Team/Enterprise Licensing** (Custom pricing)
   - Self-hosted with support contracts ($500-2000/month)
   - SLA guarantees (99.9% uptime)
   - SSO and advanced RBAC
   - Custom integrations and consulting
   - Training and onboarding
   - Dedicated Slack/Discord channel

4. **Professional Services**
   - Custom deployment and configuration: $2,000-10,000
   - Fine-tuning for domain-specific use: $5,000-20,000
   - Integration development: $5,000-50,000
   - Consulting (worldbuilding, research synthesis): $200/hour

### Alternative: Freemium SaaS (Pivot if needed)

If open-source adoption is slow (<500 stars in 6 months):

- **Free Tier**: 10 documents, 50 queries/month, cloud-only, community support
- **Pro Tier** ($15-30/month): Unlimited docs/queries, local deployment, advanced features, email support
- **Team Tier** ($50-100/month): Collaborative features, shared canons, priority support, admin controls

### Financial Projections (Optimistic Scenario)

**Year 1**:
- Open-source: 500+ stars, 100+ active deployments
- Hosted: 50 paying users @ $20/month avg = $1,000 MRR
- Services: 2-3 custom projects @ $5,000 avg = $10,000-15,000

**Year 2**:
- Open-source: 5,000+ stars, 1,000+ deployments
- Hosted: 200 users @ $25/month avg = $5,000 MRR
- Enterprise: 2-3 deals @ $1,000/month avg = $2,000-3,000 MRR
- Total MRR: ~$7,000-8,000 ($84,000-96,000 ARR)

**Year 3**:
- Open-source: 20,000+ stars, 5,000+ deployments
- Hosted: 500 users @ $25/month avg = $12,500 MRR
- Enterprise: 10 deals @ $1,500/month avg = $15,000 MRR
- Total MRR: ~$27,500 ($330,000 ARR)
- Path to profitability or Series A funding

---

## 7. Risk Analysis & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation Strategy | Status |
|------|--------|-------------|---------------------|--------|
| **LLM hallucinations** | High | High | Strict grounding prompts, graph validation, mandatory user review, confidence scores | Ongoing |
| **Coherence accuracy** | High | Medium | Hybrid approach (graph + LLM), iterative improvement via user feedback, conservative thresholds initially | Phase 1-2 |
| **Local model quality** | Medium | Low | Start with cloud fallback, transition only when local quality sufficient (already viable) | Phase 1 |
| **Scalability (large canons)** | Medium | Medium | Chunking optimization, caching, incremental indexing, test early with 500+ docs | Phase 2-3 |
| **Graph extraction accuracy** | Medium | Medium | Manual review for critical entities, ~90% auto-success rate, iterative improvement | Phase 1-2 |
| **Performance degradation** | Medium | Medium | Profiling and optimization, async processing, database indexing, query caching | Ongoing |

### Product Risks

| Risk | Impact | Probability | Mitigation Strategy | Status |
|------|--------|-------------|---------------------|--------|
| **Market fit** | High | Medium | Extensive user research (20+ interviews), iterate on feedback, validate workflow with mockups | Phase 0 |
| **User adoption (too complex)** | High | Medium | One-click setup, excellent docs/videos, Obsidian integration (familiar UX), active community support | Phase 1-2 |
| **Workflow friction** | Medium | Medium | Optional AI features (not mandatory), export flexibility, gradual feature introduction | Phase 1-3 |
| **Competition** | Medium | Low | Open-source defensibility, unique workflow (canonization), first-mover in niche, community lock-in | Ongoing |
| **Churn (paid users)** | Medium | Medium | Free tier always available (open-source), clear value prop for hosted, responsive support | Phase 2+ |

### Ethical & Reputational Risks

| Risk | Impact | Probability | Mitigation Strategy | Status |
|------|--------|-------------|---------------------|--------|
| **Misinformation** | High | Low | Clear disclaimers (coherence ≠ truth), avoid "truth" framing, focus on fiction/worldbuilding | Phase 0+ |
| **Harmful use cases** | High | Low | Community monitoring, ToS for hosted version, trust open-source transparency, no support for propaganda | Ongoing |
| **Bias amplification** | Medium | Medium | Transparency about limitations, diverse fine-tuning data, user awareness education | Phase 3+ |
| **Privacy concerns** | Medium | Low | Local-first design, encrypted sync, no telemetry without opt-in, open-source auditability | Phase 1+ |
| **Overreliance on AI** | Medium | Medium | Emphasize human-in-loop, mandatory review for canonization, education on AI limitations | Phase 1+ |

### Business & Sustainability Risks

| Risk | Impact | Probability | Mitigation Strategy | Status |
|------|--------|-------------|---------------------|--------|
| **Funding runway** | High | Low | Bootstrap-friendly (low infra costs), hosted revenue early, consulting services, optional grants/VC | Phase 1+ |
| **Open-source sustainability** | Medium | Medium | Dual licensing option (MIT + commercial), hosted services, enterprise support contracts | Phase 2+ |
| **Community fragmentation** | Low | Low | Clear governance model (benevolent dictator → committee), responsive maintainers, regular releases | Phase 1+ |

---

## 8. Success Criteria & KPIs

### Year 1: MVP → Beta

**Adoption Metrics**:
- 500+ GitHub stars
- 100+ active self-hosted deployments
- 50+ Discord members
- 10+ community contributions (issues, PRs)

**Engagement Metrics**:
- Average canon size: 15+ documents
- 30% monthly retention (users active 2+ times/month)
- 5+ queries per session avg
- 70%+ of proposals reviewed (not ignored)

**Quality Metrics**:
- 70%+ contradiction detection recall (validated via user reports)
- <10% false positive rate
- 8/10+ user satisfaction (survey)
- <5 critical bugs per month

**Revenue** (if hosted launched):
- $500-1,000 MRR from cloud tier
- 2-3 consulting/services projects

---

### Year 2: Beta → 1.0

**Adoption Metrics**:
- 5,000+ GitHub stars
- 1,000+ active deployments
- 100+ paying cloud subscribers
- 200+ Discord members

**Engagement Metrics**:
- Average canon size: 30+ documents
- 40% monthly retention
- 20% of users adopt suggestion engine
- 5+ case studies (professional use)

**Quality Metrics**:
- 85%+ contradiction detection recall
- <3% false positive rate
- 9/10+ user satisfaction
- Handle 100+ document canons reliably

**Revenue**:
- $5,000-10,000 MRR (cloud + premium + enterprise)
- Sustainable operating costs covered

---

### Year 3: Scale & Enterprise

**Adoption Metrics**:
- 20,000+ GitHub stars
- 5,000+ active deployments
- 500+ paying cloud subscribers
- 5+ enterprise customers

**Engagement Metrics**:
- Average canon size: 50+ documents
- 50% monthly retention
- Handle 500+ document canons
- 10+ integrations/plugins from community

**Quality Metrics**:
- 90%+ accuracy on coherence checking
- Local models achieve parity with cloud APIs
- NPS score: 50+

**Revenue & Sustainability**:
- $50,000+ MRR ($600,000+ ARR)
- Path to profitability or Series A funding
- Self-sustaining community governance

---

## 9. Open Questions & Future Research

### Technical

1. **Quantitative coherence metrics**: Beyond LLM scoring, can we use graph-theoretic measures (centrality, clustering coefficient) to quantify consistency? Symbolic logic layer for formal verification?

2. **Long-term consistency drift**: How do we prevent "canon drift" where late additions contradict early ones? Periodic full-canon validation passes? Hierarchical summarization? Incremental fine-tuning on canon?

3. **Multimodal canon sources**: How to handle images, maps, diagrams as authoritative sources? Vision-language models (GPT-4V, LLaVA)? Specialized extractors for maps/charts? OCR quality thresholds?

4. **Real-time collaboration**: Can we support Google Docs-style simultaneous editing without vector re-indexing delays? CRDT-based text editing? Incremental vector updates?

5. **Scalability ceiling**: At what point (1,000 docs? 10,000?) does the system break down? Graph database limitations? Vector search degradation? Mitigation strategies?

### Product

1. **Ambiguity handling**: Should system flag ambiguous/contradictory user *inputs* before canonization? Force resolution? Allow intentional ambiguity (e.g., mystery elements)?

2. **AI autonomy spectrum**: Should there be "auto-canonize" mode for low-risk extensions (e.g., minor implications)? Trust scoring for AI? Per-user preference learning?

3. **Canon branches/timelines**: How to manage "what-if" scenarios or alternate universes? Full fork (duplicate everything)? Lightweight branches (delta storage)? Merge strategies?

4. **Social/discovery features**: Public canon repositories (like GitHub for worlds)? Forking and remixing? Licensing implications? Community guidelines?

5. **Workflow customization**: Should power users be able to customize the canonization workflow? Skip review for trusted AI? Multi-stage approval? Domain-specific templates?

### Business

1. **Open-source sustainability**: Can hosted tier alone fund full-time development? Need VC/grants? Dual licensing (MIT + commercial)? Community governance model (foundation)?

2. **Enterprise market validation**: Real demand for internal knowledge consistency? Compliance requirements (SOC 2, HIPAA)? Integration needs (SharePoint, Confluence)?

3. **Localization priority**: Non-English markets? Which languages prioritize worldbuilding tools? Translation of UI vs. multilingual canon support?

4. **Competitive response**: How will WorldAnvil, Campfire, etc. react? Can they add AI features? Our defensibility beyond open-source?

---

## 10. Next Steps & Execution Plan

### Phase 0: Validation (Weeks 1-6)

#### Week 1-2: User Research
- Recruit 15-20 participants (r/worldbuilding, Discord servers, Twitter)
- Structured interviews (45-60 min each):
  - Current worldbuilding workflow and tools
  - Pain points with consistency tracking
  - Reaction to canonization workflow mockups
  - Willingness to adopt (self-host vs. cloud)
  - Feature prioritization (must-have vs. nice-to-have)
  - Pricing sensitivity (for hosted version)
- Synthesize findings into user personas and requirements

#### Week 3: Competitive Analysis
- Hands-on testing: WorldAnvil, Campfire, LegendKeeper, Notion AI
- Feature matrix and gap analysis
- Pricing comparison and value proposition
- User sentiment analysis (Reddit, reviews, forums)
- Identify differentiation opportunities and positioning

#### Week 4-5: Technical Feasibility
- Build minimal prototype:
  - LlamaIndex + Ollama (Llama-3.1-70B)
  - 10-doc test corpus (fantasy worldbuilding)
  - Basic contradiction detection
- Benchmark performance on target hardware
- Test accuracy of entity extraction and coherence checking
- Estimate infrastructure costs for hosted version
- Document technical risks and mitigation strategies

#### Week 6: Strategy & Go/No-Go
- Synthesize research into validation report
- Finalize product requirements and roadmap
- Brand positioning and messaging framework
- Landing page mockups and copy
- Community launch strategy (Discord, Reddit, Twitter)
- **Decision point**: Proceed to Phase 1 or pivot/abandon

**Deliverables**:
- Validation report (15-20 pages)
- User research synthesis (personas, journey maps)
- Technical feasibility assessment
- Brand guidelines (name, messaging, visuals)
- Go/no-go recommendation with rationale

---

### Phase 1: MVP Development (Weeks 7-18, ~3 months)

#### Week 7: Project Setup
- GitHub repository (MIT license, choose name)
- Project structure: `/backend`, `/frontend`, `/docker`, `/docs`
- CI/CD pipeline (GitHub Actions: lint, test, build)
- Development environment setup guide
- Issue templates and project board (GitHub Projects)
- Discord server for community

#### Week 8-9: Core Infrastructure
- Docker Compose configuration:
  - Qdrant (vector store)
  - Neo4j (knowledge graph)
  - PostgreSQL (metadata)
  - Ollama (local LLM runtime)
  - OpenWebUI (web interface)
- FastAPI backend skeleton:
  - Health check endpoints
  - Basic authentication (JWT)
  - Document upload endpoint (stub)
- Database schemas and migrations

#### Week 10-12: Document Ingestion Pipeline
- Unstructured.io integration for parsing
- LlamaIndex setup for chunking (512 tokens, 50 overlap)
- BGE-large-en-v1.5 embedding generation
- Qdrant indexing and storage
- File system management (originals + processed)
- Basic metadata extraction (title, upload date, user)
- Integration tests with sample documents

#### Week 13-14: Entity Extraction & Graph Construction
- LLM-based entity extraction (structured output via JSON schema)
- Entity types: Character, Location, Event, Concept, Object
- Relationship extraction (typed edges: contains, allied_with, etc.)
- Neo4j graph creation with provenance links
- Graph visualization queries (for Obsidian integration)
- Manual review interface for corrections

#### Week 15-16: Query & Retrieval
- Hybrid search implementation:
  - Semantic search (Qdrant top-k, k=10)
  - Keyword fallback (BM25)
  - Graph traversal (Neo4j, depth=2)
- Context assembly (500-2000 tokens)
- LLM query processing (Ollama)
- Citation generation and provenance tracking
- API endpoint: `/api/v1/query`

#### Week 17: Extension Generation & Review
- Extension generation endpoint: `/api/v1/extend`
- Grounding instructions for LLM (strict adherence to canon)
- Basic contradiction detection (keyword matching + LLM comparison)
- Proposal storage with metadata (prompt, timestamp, model)
- Review interface (accept/reject/edit)
- Canonization pipeline (re-index, update graph, version with Git)

#### Week 18: Integration & Testing
- Obsidian integration:
  - Vault structure for canonical documents
  - Custom plugin for query/extend (or manual workflow)
  - Graph view configuration
- End-to-end testing with sample worldbuilding project
- Performance benchmarking (query latency, generation speed)
- Bug fixes and polish
- Documentation: README, setup guide, usage examples

**Success Criteria**:
- One-click Docker setup works on recommended hardware
- User can upload 5-10 docs, query coherently, generate 3+ extensions
- System catches 50%+ of introduced contradictions
- Latency: <3 sec for queries, <30 sec for extensions

**Deliverables**:
- GitHub repo with working code
- Docker Compose file (one-click deploy)
- README with setup and usage instructions
- Demo video (5-10 min screencast)
- Blog post announcing MVP

---

### Phase 1 Kickoff Tasks (Week 7, Day 1)

**Morning**:
1. Create GitHub repo (canon-builder) with MIT license
2. Set up project structure and basic CI/CD
3. Create Discord server with channels: #general, #dev, #support
4. Draft initial README (vision, features, roadmap)

**Afternoon**:
5. Begin Docker Compose configuration (Qdrant, Neo4j, PostgreSQL)
6. Set up FastAPI project with health check endpoint
7. Test Ollama installation and model download (Llama-3.1-70B)
8. Document development environment setup

**Week 7 Goal**:
- Working Docker environment with all services running
- FastAPI "Hello World" endpoint
- Ollama responding to test prompts
- Team communication channels established

---

## 11. Appendix

### A. Docker Compose Configuration

```yaml
version: '3.8'

services:
  # Vector database for embeddings
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: canon_qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT_ALLOW_RECOVERY_MODE=true
    restart: unless-stopped

  # Knowledge graph database
  neo4j:
    image: neo4j:5.24-community
    container_name: canon_neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
    environment:
      - NEO4J_AUTH=neo4j/canon_builder_pass_2024
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=1G
    restart: unless-stopped

  # Document parsing service
  unstructured:
    image: downloads.unstructured.io/unstructured-io/unstructured-api:latest
    container_name: canon_unstructured
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
    environment:
      - UNSTRUCTURED_ALLOWED_MIMETYPES=application/pdf,image/png,image/jpeg,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document
    restart: unless-stopped

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
    restart: unless-stopped
    # Note: Run after startup to preload models:
    # docker exec -it canon_ollama ollama pull llama3.1:70b
    # docker exec -it canon_ollama ollama pull bge-large-en-v1.5

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
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY:-change_this_secret_key_in_production}
      - ENABLE_RAG=true
    depends_on:
      - ollama
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  # Backend API
  canon_api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: canon_api
    ports:
      - "8080:8080"
    volumes:
      - ./backend:/app
      - ./data:/data
      - ./documents:/documents
    environment:
      - QDRANT_URL=http://qdrant:6333
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=canon_builder_pass_2024
      - OLLAMA_URL=http://ollama:11434
      - UNSTRUCTURED_URL=http://unstructured:8000
      - POSTGRES_URL=postgresql://canon:canon_pass@postgres:5432/canon_metadata
      - JWT_SECRET=${JWT_SECRET:-your_jwt_secret_here}
      - ENVIRONMENT=development
    depends_on:
      - qdrant
      - neo4j
      - ollama
      - unstructured
      - postgres
    restart: unless-stopped

  # PostgreSQL for metadata
  postgres:
    image: postgres:16-alpine
    container_name: canon_postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d
    environment:
      - POSTGRES_USER=canon
      - POSTGRES_PASSWORD=canon_pass
      - POSTGRES_DB=canon_metadata
    restart: unless-stopped

  # Prometheus for metrics (optional, for monitoring)
  prometheus:
    image: prom/prometheus:latest
    container_name: canon_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped
    profiles:
      - monitoring

  # Grafana for visualization (optional, for monitoring)
  grafana:
    image: grafana/grafana:latest
    container_name: canon_grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    depends_on:
      - prometheus
    restart: unless-stopped
    profiles:
      - monitoring

volumes:
  qdrant_data:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  ollama_data:
  openwebui_data:
  postgres_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: canon_network

# Usage:
# 1. Copy .env.example to .env and customize secrets
# 2. docker-compose up -d
# 3. Wait for services to start (~30 seconds)
# 4. Load models: docker exec -it canon_ollama ollama pull llama3.1:70b
# 5. Load embeddings: docker exec -it canon_ollama ollama pull bge-large-en-v1.5
# 6. Access web UI at http://localhost:3000
# 7. Access Neo4j browser at http://localhost:7474 (user: neo4j, pass: canon_builder_pass_2024)
# 8. Access API docs at http://localhost:8080/docs
#
# For monitoring (optional):
# docker-compose --profile monitoring up -d
# Access Grafana at http://localhost:3001 (user: admin, pass: from .env)
```

### B. Example .env File

```bash
# Canon Builder Environment Configuration

# Web UI Secret (change in production)
WEBUI_SECRET_KEY=your_very_secret_key_change_this_in_production

# JWT Secret for API authentication
JWT_SECRET=another_secret_key_for_jwt_tokens_change_this

# Grafana admin password (if using monitoring)
GRAFANA_PASSWORD=admin_change_this

# Optional: Cloud API fallback keys (leave empty to disable)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Optional: Sentry DSN for error tracking
SENTRY_DSN=

# Optional: Email configuration (for hosted version)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@canon-builder.example.com
```

### C. Obsidian Vault Structure

```
canon-vault/
├── .obsidian/
│   ├── config
│   └── plugins/
│       └── canon-builder/     # Custom plugin (future)
├── canonical/
│   ├── characters/
│   │   ├── protagonist.md
│   │   └── antagonist.md
│   ├── locations/
│   │   ├── capital-city.md
│   │   └── forbidden-forest.md
│   ├── events/
│   │   └── great-war.md
│   ├── magic-system/
│   │   └── elemental-magic.md
│   └── history/
│       └── timeline.md
├── proposed/
│   └── pending-review/
│       ├── 2024-12-25-economic-implications.md
│       └── 2024-12-26-gunpowder-introduction.md
├── templates/
│   ├── character-template.md
│   ├── location-template.md
│   └── event-template.md
└── README.md

# Each canonical document includes YAML frontmatter:
---
id: char_001
type: character
tags: [protagonist, human, warrior]
canon_status: canonical
created: 2024-12-20
modified: 2024-12-25
provenance: user_upload
sources: [original_notes.pdf]
---

# Character Name

[Content here with [[wiki-style links]] to other entities]

## Relationships
- [[antagonist]] - Enemy
- [[capital-city]] - Hometown

## Inconsistencies
[Auto-generated by system, user can review/resolve]
```

### D. Sample API Endpoints

```python
# FastAPI Backend - Sample Endpoints

# Document Management
POST   /api/v1/documents/upload          # Upload document
GET    /api/v1/documents                 # List all documents
GET    /api/v1/documents/{id}            # Get document details
PATCH  /api/v1/documents/{id}            # Update metadata/tags
DELETE /api/v1/documents/{id}            # Delete document

# Query & Retrieval
POST   /api/v1/query                     # Natural language query
POST   /api/v1/search                    # Hybrid search (semantic + keyword)
GET    /api/v1/entities/{id}/related     # Get related entities from graph

# Extension & Proposals
POST   /api/v1/extend                    # Generate extension proposal
GET    /api/v1/proposals                 # List pending proposals
GET    /api/v1/proposals/{id}            # Get proposal details
POST   /api/v1/proposals/{id}/accept     # Accept and canonize
POST   /api/v1/proposals/{id}/reject     # Reject proposal
PATCH  /api/v1/proposals/{id}            # Edit proposal before accepting
POST   /api/v1/proposals/{id}/revise     # Request revision with feedback

# Consistency & Validation
GET    /api/v1/contradictions            # List detected contradictions
GET    /api/v1/contradictions/{id}       # Get contradiction details
POST   /api/v1/contradictions/{id}/resolve # Mark as resolved
POST   /api/v1/validate                  # Run full consistency check

# Knowledge Graph
GET    /api/v1/graph/entities            # List all entities
GET    /api/v1/graph/entities/{id}       # Get entity details
GET    /api/v1/graph/relationships       # List relationships
POST   /api/v1/graph/query               # Cypher query (advanced users)

# Export & Backup
POST   /api/v1/export/markdown           # Export canon as markdown
POST   /api/v1/export/json               # Export canon as JSON
POST   /api/v1/export/pdf                # Generate PDF worldbuilding bible
GET    /api/v1/backup                    # Download full backup

# User & Authentication
POST   /api/v1/auth/register             # Register new user
POST   /api/v1/auth/login                # Login (returns JWT)
POST   /api/v1/auth/refresh              # Refresh token
GET    /api/v1/users/me                  # Get current user
PATCH  /api/v1/users/me                  # Update user preferences

# Settings & Configuration
GET    /api/v1/settings                  # Get system settings
PATCH  /api/v1/settings                  # Update settings (admin only)
GET    /api/v1/settings/features         # Get feature toggles
PATCH  /api/v1/settings/features         # Update feature toggles
```

### E. References & Credits

**Inspired by**:
- Microsoft GraphRAG (graph-enhanced retrieval)
- LlamaIndex documentation and examples
- r/LocalLLaMA community discussions
- r/worldbuilding community needs and pain points
- Obsidian knowledge management philosophy

**Open-Source Foundations**:
- LlamaIndex (RAG framework) - MIT License
- LangGraph (agent orchestration) - MIT License
- Neo4j (graph database) - GPL/Commercial
- Qdrant (vector search) - Apache 2.0
- Ollama (local LLM runtime) - MIT License
- Unstructured.io (document parsing) - Apache 2.0
- FastAPI (backend framework) - MIT License
- OpenWebUI (web interface) - MIT License

**Competitive Analysis References**:
- WorldAnvil (worldbuilding platform)
- Campfire (writing tool)
- LegendKeeper (TTRPG tool)
- Notion AI (knowledge management)
- Custom RAG implementations (various)

**License**: MIT (for maximum community adoption and transparency)

**Governance Model**:
- Phase 1-2: Benevolent dictator (core team)
- Phase 3+: Transition to community governance at 1,000+ GitHub stars
- Consider: Technical Steering Committee, open RFC process

**Code of Conduct**: Contributor Covenant 2.1

**Contributing**: See CONTRIBUTING.md (standard open-source guidelines)

---

## 12. Conclusion & Vision

Canon Builder addresses a fundamental challenge in creative and analytical work: maintaining logical consistency across growing bodies of knowledge. By combining human judgment with AI assistance through an explicit canonization workflow, we create a tool that enhances rather than replaces human creativity.

**What makes this different**:
- Human-in-the-loop ensures quality and user trust
- Open-source core ensures transparency and community ownership
- Local-first design respects privacy and gives users control
- Graph-based architecture enables sophisticated consistency checking
- Worldbuilding focus provides clear initial market with expansion potential

**Long-term vision** (5+ years):
- Industry standard tool for worldbuilding across media (books, games, film/TV)
- Expanded to research synthesis, policy analysis, collaborative knowledge work
- Thriving plugin ecosystem for domain-specific extensions
- Self-sustaining community with distributed governance
- Local model quality exceeds cloud APIs for consistency checking
- Integration with major creative tools (Scrivener, Final Draft, Unity, etc.)

**Success looks like**:
- 50,000+ active users building coherent worlds
- 10+ professional authors/studios using in production
- Academic citations for research synthesis applications
- Community-driven feature development and maintenance
- Sustainable business supporting full-time core team
- Recognition as the "Git for knowledge consistency"

This document serves as the foundational blueprint. It will evolve through user feedback, technical discoveries, and market validation. The journey from concept to mature product will require iteration, but the core vision—empowering humans to build coherent knowledge systems with AI assistance—remains constant.

---

*Document Version: 2.0 (Final Unified from Claude + Grok iterations)*
*Last Updated: December 2025*
*Status: Pre-Development - Validation Phase*
*Next Review: Post-Phase 0 validation (6 weeks from start)*
*Maintainers: [Core team to be established]*
*Community: Discord invite TBD, GitHub Discussions TBD*
