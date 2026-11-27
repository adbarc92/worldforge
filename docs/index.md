<!-- graph:index -->
# Index

One line per doc: link | keywords | one sentence. A link ending in "/" covers a whole folder.
Regenerate with `graph.mjs init`; check with `graph.mjs lint`.

- [WorldForge Architecture Guide](ARCHITECTURE.md) | architecture, backend, services, qdrant, postgres, api, llm provider, anthropic, embedder, document ingestion, rag query, chunking, embeddings, vector search | How WorldForge is built: services, data flow, LLM providers, ingestion and RAG query workflows.
- [Canon Builder - Final Unified Design Document](CoreDesignDoc.md) | vision, canon, proposed, review workflow, knowledge graph | Original vision doc, marked Pre-Development Validation Phase; open for product intent, not the shipped system.
- [Demo Runbook](DEMO_RUNBOOK.md) | demo, runbook, stack, corpus, contradiction, alembic, docker compose, container exit, stale volume, canon_api | How to run the demo stack and keep the corpus's hero contradiction intact; covers the stale alembic revision that makes the api container exit; open for demo gotchas.
- [WorldForge Demo Script & Storyboard](DEMO_SCRIPT.md) | demo, storyboard, recording, beats, video | Beat-by-beat storyboard for the 45s launch recording; open when recording or editing the demo.
- [Launch TODOs](LAUNCH_TODOS.md) | launch, checklist, demo recording, reddit, v1.0.0 | Source of truth for what is outstanding before the v1.0.0 launch; open to see what to do next.
- [Personal Usable State design](plans/2026-03-01-personal-usable-rebuild-design.md) | rebuild, rag, openwebui, anthropic, embeddings | March 2026 design for the single-user API and service rebuild; open for early architectural decisions.
- [Personal Usable State plan](plans/2026-03-01-personal-usable-rebuild-plan.md) | rebuild, implementation, fastapi, tasks, openwebui | Task-by-task implementation plan for the backend rebuild; open to see how the backend was first built.
- [Frontend Design](plans/2026-03-02-frontend-design.md) | frontend, react, vite, shadcn, pages | Design for the React SPA with Chat, Documents and Settings pages; open for frontend structure.
- [Frontend Implementation Plan](plans/2026-03-02-frontend-plan.md) | frontend, implementation, react, settings endpoints, spa | Task-by-task plan for building the React frontend served by FastAPI; open for how it was built.
- [Multi-Project Support Design](plans/2026-03-03-multi-project-design.md) | projects, multi-project, project_id, isolation, qdrant | Design for isolated worlds via a Project table and Qdrant payload filter; open for project scoping.
- [Multi-Project Support Plan](plans/2026-03-03-multi-project-plan.md) | projects, multi-project, migration, context, implementation | Task-by-task plan for multi-project support; open to see how project isolation was implemented.
- [Aegis demo fixtures](qa/fixtures/aegis-demo/) | aegis station, crew, history, logs, fixture | Six fictional sci-fi world files (md, txt, pdf) used as QA fixtures; look up by file name, not by topic.
- [Contradicting pair fixtures](qa/fixtures/contradicting-pair/) | valeria, kingdom, contradiction, fixture, doc-a | Two short Valeria files that disagree on every fact; fixtures for contradiction detection.
- [QA Fixtures](qa/fixtures/README.md) | fixtures, qa, contradicting-pair, aegis-demo, upload | Explains the QA fixture sets and what each tests; open before using them.
- [QA Checklist PR #4](qa/pr-4-checklist.md) | qa, checklist, pr 4, bugfixes, manual testing | Manual QA steps for the four qa-bugfixes commits; open to verify those fixes.
- [WorldForge Requirements v1.0.0](REQUIREMENTS.md) | requirements, functional, api, endpoints, v1.0.0 | Requirements as shipped in Phase 1 (updated 2026-04-15); open for what the product must do.
- [WorldForge Roadmap](ROADMAP.md) | roadmap, phases, knowledge graph, ollama, auth, docx, file formats, ingestion | Phase 1 complete; Phase 2 covers DOCX support and severity classification; phases 2 to 8 planned (DOCX, graph, review queue, export, local, auth); open for future work.
- [Contradiction Detection plan](superpowers/plans/2026-04-04-contradiction-detection.md) | contradiction, implementation, contradictions table, classify, tasks | Implementation plan for detecting and queueing contradictions; open for how the feature was built.
- [World Synthesis plan](superpowers/plans/2026-04-05-world-synthesis.md) | synthesis, primer, implementation, outline, syntheses table | Implementation plan for the narrative primer pipeline; open for how synthesis was built.
- [Open-Source Polish plan](superpowers/plans/2026-04-10-open-source-polish.md) | polish, ci, vitest, contributing, release | Plan for frontend tests, CI/CD, contributor files and the v1.0.0 merge; open for release prep history.
- [Contradiction Detection design](superpowers/specs/2026-04-04-contradiction-detection-design.md) | contradiction, similarity, data model, resolve, dismiss | Design spec for contradiction detection and its data model; open for how conflicts are found and resolved.
- [World Synthesis design](superpowers/specs/2026-04-05-world-synthesis-design.md) | synthesis, primer, outline, gated, narrative | Design spec for the world primer, gated on resolved contradictions; open for synthesis behaviour.
- [Open-Source Polish design](superpowers/specs/2026-04-10-open-source-polish-design.md) | polish, open-source, ci, approved, metadata | Approved spec for public-release polish: tests, CI, contributor infra; open for release scope.
- [WorldForge Launch Strategy](superpowers/specs/2026-04-15-launch-strategy-design.md) | launch, positioning, reddit, show hn, waves | Launch positioning and two-wave plan for TTRPG then dev communities; open when writing launch posts.
- [AetherCanon Builder Test Specifications](TEST_SPECIFICATIONS.md) | tests, test specifications, strategy, test cases, aethercanon | Test strategy and cases, status Active, v1.0 dated January 2026 against an earlier name; open for test design.
