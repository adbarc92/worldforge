# Contradiction Detection — Design Spec

## Overview

Automatically identify contradictions in a project's canon as documents are added, and queue them for manual resolution. Uses semantic similarity search to find candidate chunk pairs, then an LLM to classify whether they genuinely contradict each other.

## Data Model

New `contradictions` table:

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| project_id | UUID FK → projects | Scoped to project, cascade delete |
| chunk_a_id | UUID | Qdrant point ID |
| chunk_b_id | UUID | Qdrant point ID |
| document_a_id | UUID FK → documents | Source document for chunk A |
| document_b_id | UUID FK → documents | Source document for chunk B |
| chunk_a_text | text | Snapshot of chunk text at detection time |
| chunk_b_text | text | Snapshot of chunk text at detection time |
| explanation | text | LLM description of the contradiction |
| status | enum | `open` / `resolved` / `dismissed` |
| resolved_at | timestamp | Nullable, set on resolution |
| created_at | timestamp | |

Chunk texts are stored as snapshots — no need to look them up from Qdrant at display time. Document FKs provide source attribution ("Exousia_v0.md vs WDD_Exousia.md").

Alembic migration adds this table. FK to documents uses `SET NULL` on delete so contradictions survive document removal (text snapshots remain readable).

## Backend Service

### ContradictionService

New service at `backend/app/services/contradiction_service.py`.

### Detection Flow (per document)

1. Query Qdrant for all chunks belonging to the newly ingested document (filter by `document_id`).
2. For each chunk, query Qdrant for top-5 semantically similar chunks from *other documents* in the same project.
3. For each candidate pair, call the LLM with a classification prompt (see below).
4. If the LLM confirms a contradiction, insert a row into the `contradictions` table.
5. Deduplicate before inserting — check that the chunk pair (in either order) doesn't already exist.

### LLM Prompt

```
You are comparing passages from a worldbuilding canon. Do these two passages
contradict each other? A contradiction means they assert mutually exclusive facts
about the same subject. Different levels of detail, different topics, or evolving
ideas are NOT contradictions.

Passage A:
{chunk_a_text}

Passage B:
{chunk_b_text}

Respond with JSON only: {"is_contradiction": bool, "explanation": "string"}
```

- Temperature: 0 (deterministic classification)
- Max tokens: 256

### Trigger Points

**After ingestion (automatic):**
After `ingestion_service.process_document()` succeeds, fire `asyncio.create_task(contradiction_service.scan_document(doc_id, project_id))`. The upload response returns immediately — scanning runs in the background within the same process. The background task creates its own DB session (via `async_sessionmaker`) since the request-scoped session will be closed by the time the task runs.

**On-demand (manual):**
`POST /api/v1/projects/{project_id}/contradictions/scan` triggers a full project scan. Iterates all documents in the project and runs the per-document detection flow for each. Deduplication prevents re-flagging existing contradictions — only new pairs are inserted. Returns `202 Accepted` immediately. Also creates its own DB session for the background task.

### Cost Control

- Top-5 similar chunks per new chunk bounds LLM calls to ~5 per chunk.
- Skip pairs where both chunks belong to the same document.
- A 57-chunk document generates at most ~285 LLM calls, but same-document filtering reduces this significantly.
- Temperature 0 for deterministic results.

## API Endpoints

All scoped under `/api/v1/projects/{project_id}/contradictions`:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | List contradictions. Query params: `status` (open/resolved/dismissed), `skip`, `limit`. Default: open only. |
| POST | `/scan` | Trigger full project scan. Returns 202 Accepted. |
| PATCH | `/{id}/resolve` | Set status to `resolved`, set `resolved_at`. |
| PATCH | `/{id}/dismiss` | Set status to `dismissed`, set `resolved_at`. |

No create or delete endpoints — detection creates contradictions, users change their status.

## Frontend

### New Page: `/contradictions`

Added to sidebar between Documents and Settings.

**Layout:**
- Header with open contradiction count and "Scan Project" button.
- Filter tabs: Open / Resolved / Dismissed.
- List of contradiction cards, each showing:
  - Side-by-side chunk texts (Passage A | Passage B).
  - Source document titles for each side.
  - LLM explanation of the contradiction.
  - Action buttons: "Resolve" and "Dismiss".

### Hooks

- `useContradictions(projectId, status)` — React Query fetch for the contradiction list.
- `useScanContradictions(projectId)` — Mutation to trigger a scan.
- `useResolveContradiction()` — Mutation, invalidates list on success.
- `useDismissContradiction()` — Mutation, invalidates list on success.

### Scan Feedback

Triggering a scan shows a toast ("Scanning for contradictions..."). No websocket or polling — user refreshes or navigates back to see results.

## Dependency Wiring

- `ContradictionService` depends on `QdrantService`, `LLMService`, and `AsyncSession`.
- Follows existing pattern: `get_contradiction_service()` in `dependencies.py`, composed per-request.
- Ingestion service receives contradiction service via dependency injection to fire background scans.

## Testing

- **Unit tests for ContradictionService:** Mock LLM to return canned responses. Verify correct DB inserts, deduplication, and same-document skip logic.
- **Prompt parsing test:** Verify JSON parsing handles edge cases (markdown-wrapped JSON, missing fields).
- **API endpoint tests:** List (with status filter), scan (returns 202), resolve, dismiss.
- **Deduplication test:** Upload same document twice, verify no duplicate contradictions.

No live LLM integration tests — prompt tuning happens manually with real data.
