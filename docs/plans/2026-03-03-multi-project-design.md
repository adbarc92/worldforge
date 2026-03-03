# Multi-Project Support Design

**Goal:** Add support for multiple isolated projects (worlds/settings), each with its own documents and RAG queries.

**Architecture:** Single Qdrant collection with `project_id` payload filtering. New Project table in PostgreSQL with foreign key from Document. Frontend uses React Context + localStorage for active project state.

**Tech Stack:** Same as existing — no new dependencies.

---

## Data Model

### New `Project` table
- `id` (UUID string, PK)
- `name` (string, unique)
- `description` (text, nullable)
- `created_at`, `updated_at` (timestamps)

### `Document` table change
- Add `project_id` (foreign key -> Project.id, NOT NULL)

### Qdrant payload change
- Add `project_id` to every point's payload
- All searches filter by `project_id`

### Migration
- Alembic creates Project table, adds `project_id` column
- Creates "Default" project, assigns all existing documents to it
- Startup task backfills `project_id` into existing Qdrant payloads (idempotent)

---

## API Changes

### New project endpoints (`/api/v1/projects`)
- `POST /` — create project (name, optional description)
- `GET /` — list all projects
- `GET /{project_id}` — get project details (includes document count)
- `PUT /{project_id}` — rename/update description
- `DELETE /{project_id}` — delete project + all documents + all Qdrant vectors

### Existing endpoints become project-scoped
- `POST /api/v1/projects/{project_id}/documents/upload`
- `GET /api/v1/projects/{project_id}/documents`
- `GET /api/v1/projects/{project_id}/documents/{doc_id}`
- `DELETE /api/v1/projects/{project_id}/documents/{doc_id}`
- `POST /api/v1/projects/{project_id}/query`

### OpenAI-compatible endpoint
- `/v1/chat/completions` gets optional `project_id` field in request body
- Falls back to most recently created project if not specified

### Unchanged
- `/health`, `/api/v1/settings`

---

## Frontend Changes

### Project selector in sidebar
- Dropdown below "Canon Builder" title
- Shows active project name, click to switch
- "Manage Projects" link at bottom goes to `/projects`

### Projects page (`/projects`)
- Project cards: name, description, document count, created date
- New Project button with name/description form
- Edit and delete per project (delete with confirmation)

### Existing pages become project-scoped
- Documents and Chat pages use active project only
- If no project selected, redirect to `/projects`

### Active project state
- React Context provides `activeProject` + `setActiveProject`
- Persisted to `localStorage` for page refresh survival
- API client includes `project_id` in all scoped requests

---

## Testing

### Backend
- Project repository CRUD tests
- Project-scoped document listing test
- Project-scoped Qdrant search filter test
- Regression: existing settings tests still pass

### Migration
- Alembic migration for schema changes
- Idempotent Qdrant payload backfill at startup

### Frontend
- Manual testing only (thin UI layer)
