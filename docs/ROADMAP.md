# WorldForge Roadmap

## Phase 1: Core Platform (Complete)

- [x] Multi-project support with isolated knowledge bases
- [x] Document ingestion — text, markdown, PDF (chunking via LlamaIndex, embeddings via OpenAI)
- [x] RAG-powered query with cited answers
- [x] Contradiction detection with resolve/dismiss workflow
- [x] World synthesis — outline generation, section writing, downloadable primer
- [x] OpenAI-compatible chat endpoint (OpenWebUI integration)
- [x] Runtime settings management (API keys, model selection)
- [x] LLM provider abstraction (Anthropic generation + OpenAI embeddings)
- [x] Async throughout (database, vector DB, LLM calls)
- [x] Docker Compose single-command deployment
- [x] React frontend with chat, documents, contradictions, synthesis pages
- [x] CI/CD (GitHub Actions for backend, frontend, Docker)
- [x] Contributor infrastructure (CONTRIBUTING.md, issue/PR templates)
- [x] Frontend test suite with Vitest + React Testing Library

## Phase 2: Document & Query Improvements

Strengthen the core document pipeline and query experience.

- [ ] DOCX file format support
- [ ] Contradiction severity classification (HIGH / MEDIUM / LOW)
- [ ] "No information found" response when query is outside canon
- [ ] Expandable source excerpts in query responses (click citation to see full chunk)
- [ ] Query history (persist and browse past queries per project)
- [ ] Ingestion performance benchmarks (target: 50 pages < 2 min)
- [ ] Bulk document management (multi-select delete, re-index)

## Phase 3: Knowledge Graph

Add structured entity/relationship extraction on top of the existing RAG pipeline.

- [ ] Entity extraction via LLM (characters, locations, events, concepts, items)
- [ ] Entity and relationship storage (new database tables)
- [ ] Graph-enhanced hybrid RAG search (vector + graph context)
- [ ] Entity browser UI (view, edit, link entities)
- [ ] Graph visualization (interactive relationship map)

## Phase 4: Review Queue & Proposals

AI-generated canon extensions with a human-in-the-loop review workflow.

- [ ] Proposed content system (AI suggests new entities/relationships)
- [ ] Review queue UI (approve / edit & approve / reject / defer)
- [ ] Canonical vs. proposed content separation
- [ ] Coherence scoring for proposed content
- [ ] Bulk approval for high-confidence items
- [ ] Undo support for review actions

## Phase 5: Export & Interoperability

Get canon data out of WorldForge and into other tools.

- [ ] Obsidian vault export (one .md per entity, wikilinks, YAML frontmatter)
- [ ] PDF export of world primer / synthesis
- [ ] Static site generation from canon
- [ ] Import from Obsidian vaults (round-trip)
- [ ] Import from other worldbuilding tools (World Anvil, Notion)

## Phase 6: Local & Offline

Remove cloud API dependencies for users who want full local operation.

- [ ] Ollama local LLM support (generation)
- [ ] Local embedding models (BGE-large-en-v1.5 or similar)
- [ ] Offline mode after initial setup
- [ ] Configurable model selection per task (use local for embeddings, cloud for generation, etc.)

## Phase 7: Multi-User & Auth

- [ ] User registration and JWT authentication
- [ ] Per-user document and project isolation
- [ ] Role-based access control (owner / editor / viewer)
- [ ] Rate limiting
- [ ] Secrets management (encrypted API key storage)

## Phase 8: Operational Maturity

- [ ] Automated backups (database + vector store)
- [ ] Monitoring and observability (Prometheus / Grafana)
- [ ] Audit logging (who changed what, when)
- [ ] Performance load testing (10 concurrent users, p95 < 5s)
- [ ] Error retry with exponential backoff (LLM failures, DB connection loss)

---

**Versioning:** Phase 1 shipped as v1.0.0. Future phases will be tagged as minor/major versions as they complete.
