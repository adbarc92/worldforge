# World Synthesis — Design Spec

## Overview

Generate a comprehensive narrative primer document that summarizes a project's entire worldbuilding canon for newcomers. Gated behind all contradictions being resolved. Uses a multi-step LLM pipeline: analyze chunks to propose an outline, optionally let the user approve/edit the outline, then generate each section using relevant chunks and contradiction resolution notes.

## Data Model

New `syntheses` table:

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| project_id | UUID FK → projects | Cascade delete |
| title | String | e.g., "World Primer" |
| outline | JSON | List of {title, description} section entries |
| outline_approved | bool | False until user approves, or true immediately in auto-mode |
| content | Text | Final assembled markdown document, nullable until complete |
| status | enum | `outline_pending` / `outline_ready` / `generating` / `completed` / `failed` |
| error_message | Text | Nullable, set on failure |
| created_at | timestamp | |
| updated_at | timestamp | |

No separate sections table. The outline is JSON, the final content is a single assembled markdown Text field. Old syntheses are kept for history; regenerating creates a new row.

Alembic migration adds this table. FK to projects uses CASCADE on delete.

## Backend Service

### SynthesisService

New service at `backend/app/services/synthesis_service.py`.

### Generation Flow

**Step 1: Gate check**
Query `contradictions.count(project_id, status="open")`. If any open contradictions exist, reject with a clear error: "Resolve all contradictions before generating."

**Step 2: Outline generation** (runs as background asyncio task)
- Retrieve all chunks for the project from Qdrant via `search_by_filter(filters={"project_id": project_id})`.
- Batch chunk texts into groups that fit the context window (~50 chunks per batch, ~25K tokens).
- For each batch, ask the LLM: "Given these passages from a worldbuilding canon, list the major topics covered (e.g., cosmogony, factions, characters, events, locations)."
- Merge the topic lists from all batches, then ask the LLM to consolidate into a final ordered outline of ~8-15 sections, each with a title and one-line description.
- Store the outline as JSON, set status to `outline_ready`.
- In auto-mode: set `outline_approved = True` and immediately proceed to step 4.

**Step 3: User approval**
- User reviews the outline via the UI, can reorder, edit titles/descriptions, or remove sections.
- On approval (POST `/{id}/approve`), set `outline_approved = True` and proceed to step 4.

**Step 4: Section generation** (runs as background asyncio task)
- Set status to `generating`.
- For each section in the approved outline:
  - Embed the section title + description and query Qdrant for top-30 most relevant chunks.
  - Query resolved/dismissed contradictions for the project that have a non-null `resolution_note`. Include these notes in the prompt as "Canon resolution notes" so the LLM knows which version of disputed facts to prefer.
  - Call the LLM with a narrative synthesis prompt:
    > "Write a flowing narrative section about {title} for someone being introduced to this world. Use only the provided source material. Where sources were contradictory, resolution notes indicate which version is canon."
  - Temperature: 0.7 (more creative than classification, still grounded).
- On failure of any section, set status to `failed` with error message and stop.

**Step 5: Assembly**
- Concatenate all sections with markdown headers (`# {title}`) into the final document.
- Store in the `content` column, set status to `completed`.

### Background Execution

All long-running steps (outline generation, section generation) run as `asyncio.create_task()` — same pattern as contradiction scanning. The background task creates its own DB session via `async_session`. The API returns immediately with the synthesis ID; the frontend polls for status updates.

## API Endpoints

All scoped under `/api/v1/projects/{project_id}/synthesis`:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/` | Start a new synthesis. Query param: `auto=true` to skip outline approval. Returns 202 + synthesis ID. Rejects 400 if open contradictions exist. |
| GET | `/` | List syntheses for the project, most recent first. |
| GET | `/{id}` | Get synthesis details: status, outline, content, error_message. |
| PATCH | `/{id}/outline` | Update the outline (reorder/edit sections). Request body: `{"outline": [...]}`. Only valid when status is `outline_ready` and `outline_approved` is false. Returns 409 otherwise. |
| POST | `/{id}/approve` | Approve the outline and start section generation. Only valid when status is `outline_ready`. Returns 409 otherwise. |
| GET | `/{id}/download` | Returns the content as a downloadable `.md` file with `Content-Disposition: attachment` header. Only valid when status is `completed`. Returns 409 otherwise. |

The POST create endpoint checks `ContradictionRepository.count(project_id, status="open") == 0` before proceeding. Returns 400 with message "Resolve all open contradictions before generating a synthesis" if the check fails.

## Frontend

### New Page: `/synthesis`

Added to sidebar after Contradictions.

**Page states:**

1. **No synthesis / list view** — Shows list of past syntheses (if any) with status badges. "Generate World Primer" button at top. Button is disabled with a tooltip/message if open contradictions remain (use the contradiction count query). Secondary "Quick Generate" button for auto-mode (skips outline approval).

2. **Outline review** (status: `outline_ready`) — Shows the outline as an editable list of sections. Each section has title and description, user can reorder, edit, or remove. "Approve & Generate" button to proceed.

3. **Generating** (status: `outline_pending` or `generating`) — Shows the outline read-only with a progress indicator. Poll the synthesis status endpoint every 3-5 seconds.

4. **Completed** — Renders the markdown content in the page (readable, formatted). "Download" button exports as `.md`. "Regenerate" button starts a new synthesis.

5. **Failed** — Shows error message with a "Retry" button that creates a new synthesis.

### Hooks

- `useSyntheses(projectId)` — React Query list fetch.
- `useSynthesis(id)` — Single synthesis fetch. Polls every 5 seconds when status is `outline_pending` or `generating`.
- `useCreateSynthesis()` — POST mutation, accepts `{auto?: boolean}`.
- `useUpdateOutline()` — PATCH mutation for outline edits.
- `useApproveSynthesis()` — POST approve mutation.

### Contradiction Gate UI

The "Generate" button queries the open contradiction count. If > 0, the button is disabled and shows: "Resolve all N open contradictions first". Links to the contradictions page.

## Dependency Wiring

- `SynthesisService` depends on `QdrantService`, `LLMService`, `ContradictionRepository`, and a `SynthesisRepository`.
- Follows existing pattern: `get_synthesis_service()` in `dependencies.py`.
- Background tasks create their own DB session via `async_session`.

## Testing

- **Gate check test:** Verify synthesis is rejected when open contradictions exist, allowed when all are resolved/dismissed.
- **Outline generation test:** Mock LLM to return canned topic lists, verify outline is consolidated and stored as JSON.
- **Section generation test:** Mock LLM and Qdrant, verify each section prompt includes relevant chunks and resolution notes.
- **API tests:** Create (with gate check), get, outline update (valid and invalid states), approve (valid and invalid states), download.
- **Status transition tests:** Verify invalid transitions are rejected (e.g., approve when status is `generating`, edit outline after approval).

No live LLM integration tests — prompt tuning happens manually with real data.
