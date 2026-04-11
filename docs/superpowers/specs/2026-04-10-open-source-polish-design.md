---
name: Open-Source Polish Pass
description: Polish WorldForge for public open-source release — frontend test suite, CI/CD, contributor infrastructure, metadata cleanup, merge feat/multiple-projects to main
status: approved
date: 2026-04-10
---

# Open-Source Polish Pass

## Context

WorldForge (Canon Builder) is a working, personal RAG-powered worldbuilding tool with Phase 1 complete and a large feature branch (`feat/multiple-projects`, 39 commits ahead of main) adding multi-project support, contradiction detection, and synthesis. A prior audit found the repo is ~75–80% ready for public release: good architecture, comprehensive backend tests, MIT license, Docker setup, no secrets in git history.

This design covers the polish pass needed to take the project from "working personal tool" to "professional open-source release that invites contribution."

## Goals

1. Frontend test suite with comprehensive coverage (currently zero tests)
2. GitHub Actions CI/CD for backend, frontend, and Docker
3. Contributor infrastructure (`CONTRIBUTING.md`, issue/PR templates)
4. Metadata cleanup in `frontend/package.json` and `backend/pyproject.toml`
5. Commit valuable untracked docs; exclude internal artifacts
6. Merge `feat/multiple-projects` → `main` and tag `v1.0.0`

## Non-Goals

- New features or refactoring unrelated to the polish pass
- Rotating API keys (user's responsibility)
- Pushing the release to the public or announcing it (user's decision)
- Authentication / multi-user (Phase 4 work)
- Monitoring/observability setup

## Scope Summary

| Workstream | Owner (agent) | Files |
|---|---|---|
| Frontend tests | Agent A | `frontend/vitest.config.ts`, `frontend/src/test/**`, `frontend/src/**/*.test.ts[x]`, `frontend/package.json` (test scripts only) |
| CI/CD | Agent B | `.github/workflows/**`, `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md` |
| Docs & metadata | Agent C | `CONTRIBUTING.md`, `README.md` updates, `frontend/package.json` (metadata only), `backend/pyproject.toml`, `config/config.dev.yaml`, `.gitignore`, git-add `docs/ARCHITECTURE.md`, `docs/superpowers/**`, `scripts/bulk_upload.py` |

The three workstreams run in parallel. `frontend/package.json` is touched by two agents — they edit disjoint sections (scripts vs top-level metadata), but the integration step will resolve any conflict manually.

---

## Section 1: Frontend Test Suite

### Stack

- **Vitest** — shares Vite config, zero duplication of TypeScript/path-alias setup
- **React Testing Library** — component and hook testing
- **`@testing-library/jest-dom`** — DOM matchers
- **MSW (Mock Service Worker)** — API mocking (closer to real behavior than `vi.fn()` stubs)

### Structure

- Colocate tests with source files: `Component.tsx` → `Component.test.tsx`
- Shared utilities under `frontend/src/test/`:
  - `setup.ts` — global test setup (jest-dom matchers, MSW server lifecycle)
  - `test-utils.tsx` — custom `render()` wrapping in `QueryClientProvider` + `MemoryRouter` with a fresh `QueryClient` per test
  - `mocks/handlers.ts` — MSW request handlers for all backend endpoints
  - `mocks/server.ts` — MSW server instance

### Coverage Targets

| Area | What gets tested |
|---|---|
| `lib/api.ts` | Every function: URL, method, headers, body, error handling, response parsing |
| `hooks/*` | `useChat`, `useDocuments`, `useHealth`, `useSettings`, `useProjects`, etc. — query keys, mutations, optimistic updates, error states |
| `components/chat/*` | `ChatView`, `MessageBubble`, `ChatInput` — user input, rendering, streaming |
| `components/documents/*` | `UploadDropzone` (drag/drop, file validation), `DocumentCard` (actions, delete confirmation) |
| `components/layout/*` | `Shell`, `Sidebar`, `HealthIndicator` |
| Contradictions/synthesis components | Grouped views, bulk actions, resolution flows |
| `pages/*` | `ChatPage`, `DocumentsPage`, `SettingsPage`, `ProjectsPage`, synthesis and contradiction pages — integration-style tests with mocked API |
| Router | Navigation, 404 handling |

### Scripts added to `frontend/package.json`

- `test` — `vitest run`
- `test:watch` — `vitest`
- `test:coverage` — `vitest run --coverage`
- `test:ui` — `vitest --ui`
- `typecheck` — `tsc --noEmit` (needed by CI, may not yet exist)

### Coverage Thresholds (enforced in CI)

- Lines: 70%
- Branches: 65%

Configured in `vitest.config.ts` via the coverage reporter. Low enough to not block on untestable glue code, high enough to be meaningful.

### Mocking Strategy

MSW handles all HTTP mocking. Real `QueryClient` per test (no mocking React Query internals). Per-test override of specific handlers using `server.use()` for error-state tests.

---

## Section 2: CI/CD — GitHub Actions

Four workflow files under `.github/workflows/`:

### `backend.yml`

- Triggers: PRs and pushes touching `backend/**`
- Steps:
  1. Checkout
  2. Setup Python (matrix: 3.11, 3.12)
  3. Install UV
  4. `uv sync --all-groups`
  5. `uv run pytest tests/ -v -m "not integration"`
  6. `uv run pytest tests/ --cov=app --cov-report=xml -m "not integration"`
  7. Upload coverage artifact
- Caching: UV cache keyed on `uv.lock`

### `frontend.yml`

- Triggers: PRs and pushes touching `frontend/**`
- Steps:
  1. Checkout
  2. Setup Node 20
  3. `npm ci`
  4. `npm run lint`
  5. `npm run typecheck`
  6. `npm run test:coverage`
  7. `npm run build`
- Caching: npm cache keyed on `package-lock.json`

### `docker.yml`

- Triggers: PRs touching `Dockerfile` / `docker-compose.yml`, push to `main`, tag push matching `v*`
- Steps:
  1. Checkout
  2. Setup Buildx
  3. Login to GHCR (only on push to main / tag)
  4. Build with layer cache
  5. Push tags on main: `ghcr.io/adbarc92/worldforge:latest` + commit SHA
  6. Push tags on tag push: `ghcr.io/adbarc92/worldforge:v1.0.0`
- Uses `docker/build-push-action@v5`
- PR builds verify build succeeds without pushing

### `ci.yml` (umbrella)

- Triggers: every PR to main
- Calls `backend.yml`, `frontend.yml`, `docker.yml` as reusable workflows via `workflow_call`
- Single required status check — simpler than requiring three individual checks in branch protection

### Branch Protection

Documented in `CONTRIBUTING.md` for the user to apply manually in GitHub UI:
- Require `ci` to pass before merging to main
- Require PR review (optional for solo maintainer)
- No direct pushes to main

---

## Section 3: Contributor Infrastructure

### `CONTRIBUTING.md`

Sections:

1. Welcome & project overview (2-3 sentences, link to README)
2. Code of conduct (short inline — be kind, assume good faith)
3. Development setup (prerequisites: Docker, UV, Node 20; clone/install; running locally with/without Docker; applying migrations; seeding test data via `scripts/bulk_upload.py`)
4. Project structure (mini tree, pointer to `docs/ARCHITECTURE.md`)
5. Running tests (backend `uv run pytest`, frontend `npm test`, integration tests)
6. Code style (Ruff, ESLint, commit message conventions: `feat:`, `fix:`, `docs:`, etc.)
7. PR workflow (fork, branch naming, keep PRs focused, link issues, CI must pass)
8. What we're looking for (good first issues, roadmap phases from `docs/ROADMAP.md`)
9. What not to work on without discussion (auth — Phase 4, major architectural changes)
10. Questions (GitHub Discussions or Issues)

### `.github/ISSUE_TEMPLATE/`

Three templates:

- `bug_report.yml` — description, reproduction steps, expected/actual, environment (OS, Docker version), logs
- `feature_request.yml` — problem, proposed solution, alternatives, roadmap phase (if known)
- `config.yml` — disables blank issues; links to Discussions for questions

### `.github/PULL_REQUEST_TEMPLATE.md`

Checklist: what changes, why, how tested, screenshots if UI, linked issue, CI passing confirmation.

---

## Section 4: Metadata Cleanup

### `frontend/package.json`

```json
{
  "name": "worldforge-frontend",
  "version": "1.0.0",
  "private": true,
  "description": "React frontend for WorldForge, a RAG-powered worldbuilding knowledge system",
  "repository": {
    "type": "git",
    "url": "https://github.com/adbarc92/worldforge.git",
    "directory": "frontend"
  },
  "license": "MIT",
  "author": "Alex Barclay"
}
```

`private: true` retained — not publishing to npm, prevents accidents.

### `backend/pyproject.toml`

```toml
authors = [{ name = "Alex Barclay" }]
license = { text = "MIT" }
readme = "../README.md"
keywords = ["rag", "worldbuilding", "llm", "fastapi", "qdrant"]

[project.urls]
Repository = "https://github.com/adbarc92/worldforge"
Issues = "https://github.com/adbarc92/worldforge/issues"
```

### `config/config.dev.yaml`

Replace stale `claude-3-5-sonnet-20241022` with the current Claude Sonnet model used elsewhere in the codebase. Agent C verifies the correct current model ID by grepping the rest of the codebase before making the change.

### `.gitignore`

- Add `docs/LAUNCH_TWEETS.md`
- Verify `.claude/` is excluded (add if missing)
- Keep the staged `test-docs*` addition

---

## Section 5: Documentation Commits

### To commit

- `docs/ARCHITECTURE.md`
- `docs/superpowers/plans/2026-04-04-contradiction-detection.md`
- `docs/superpowers/specs/2026-04-04-contradiction-detection-design.md`
- `docs/superpowers/plans/*` (any others in the directory)
- `docs/superpowers/specs/2026-04-05-world-synthesis-design.md`
- `scripts/bulk_upload.py`

(This design doc is already committed in its own commit prior to implementation.)

- `.gitignore` update

### NOT committed

- `.claude/`
- `docs/LAUNCH_TWEETS.md`
- Any `.env*` files except `.env.example`

### `README.md` updates

- Add a "Contributing" section pointing to `CONTRIBUTING.md`
- Add a "Bulk upload" section in the usage docs pointing to `scripts/bulk_upload.py`
- Add a CI status badge at the top

---

## Section 6: Integration & Merge Strategy

After all three parallel workstreams finish and commit to `feat/multiple-projects`:

### Local Verification

- `cd backend && uv run pytest tests/ -v -m "not integration"` — backend tests green
- `cd frontend && npm run test` — frontend tests green
- `cd frontend && npm run build` — production build succeeds
- `cd frontend && npm run typecheck` — no TS errors
- `cd frontend && npm run lint` — no lint errors
- `docker compose build` — image builds cleanly

If anything fails: fix on the feature branch before proceeding.

### Push & CI Verification

1. Push feature branch: `git push origin feat/multiple-projects` — triggers CI for the first time. Confirms workflows work in CI, not just locally. Iterate until green.
2. Open PR `feat/multiple-projects` → `main` via `gh pr create` with detailed description (39 feature commits + polish pass).
3. Wait for CI to pass.

### Merge

- **Squash merge** (per user preference).
- Commit message: `feat: multi-project support, contradiction detection, synthesis, open-source polish`
- Post-merge cleanup: `git checkout main && git pull && git branch -d feat/multiple-projects`. User decides whether to delete remote branch.

### Tag v1.0.0

- `git tag -a v1.0.0 -m "Initial open-source release"`
- `git push origin v1.0.0`
- `docker.yml` automatically builds and pushes `ghcr.io/adbarc92/worldforge:v1.0.0`

### Stop Point

Halt after tagging and report back. Creating a GitHub release (with release notes, binary artifacts) and announcing the launch are user decisions not taken without explicit confirmation.

---

## Section 7: Testing & Error Handling

### Verification Matrix

| Area | Verification |
|---|---|
| Frontend tests | `npm run test` passes locally and in CI, coverage ≥70% lines / 65% branches |
| CI/CD | All four workflows run green on first push of `feat/multiple-projects`. Path filters work. `ci` umbrella appears as single status on PR. |
| Contributor infra | `CONTRIBUTING.md` renders on GitHub, issue templates appear in "New Issue" dropdown, PR template auto-populates |
| Metadata | No JSON/TOML syntax errors; values match spec |
| Docs commits | Files appear in `git log`; excluded files remain untracked |
| Integration | All local verification passes, CI passes on feature-branch push, merge completes, tag pushes successfully |

### Error Recovery

- **Frontend test setup fails** (Vitest/Vite conflict, missing deps): halt that workstream, fix before other streams merge
- **Tests fail because existing code has bugs**: fix the code, not the tests. Deep issues → `.skip` with `TODO(issue-#N)` + open GitHub issue
- **CI fails on first push** (works locally, fails in CI): iterate on workflow file, push fixes. Common causes: missing env vars, secrets, wrong path filters
- **Docker build breaks**: likely a missing dependency. Fix Dockerfile, not workflow
- **Merge conflicts with main**: unlikely (main hasn't moved), but resolve on feature branch if they appear
- **Flaky CI blocks PR**: quarantine (skip + issue), re-run, merge

### Agent Coordination

Each subagent receives an explicit file ownership list in its prompt:

- **Agent A (frontend tests)**: `frontend/vitest.config.ts`, `frontend/src/test/**`, `frontend/src/**/*.test.ts[x]`, `frontend/package.json` (test scripts only)
- **Agent B (CI/CD)**: `.github/workflows/**`, `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md`
- **Agent C (docs & metadata)**: `CONTRIBUTING.md`, `README.md`, `frontend/package.json` (metadata fields only — NOT scripts), `backend/pyproject.toml`, `config/config.dev.yaml`, `.gitignore`; git-add `docs/ARCHITECTURE.md`, `docs/superpowers/**`, `scripts/bulk_upload.py`

**`frontend/package.json` overlap**: Agents A and C touch different sections (scripts vs top-level metadata). Each agent's prompt instructs it to preserve any concurrent edits. The integration step resolves conflicts manually if they occur.

---

## Open Questions / Assumptions

- **Author name**: "Alex Barclay" — assumed from `git config user.name`. Update if different is preferred.
- **Repository URL**: `https://github.com/adbarc92/worldforge` — confirmed from existing remote.
- **GHCR visibility**: Assumed the GHCR image should be public (matches the repo). User can make it private later.
- **Current Claude model**: Agent C verifies by grepping the codebase before updating `config/config.dev.yaml`.
- **No GitHub Discussions yet**: `CONTRIBUTING.md` links to Discussions. If not enabled, it becomes a dead link. Agent C checks and falls back to Issues link if Discussions isn't enabled.
