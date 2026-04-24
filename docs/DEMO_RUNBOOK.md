# Demo Runbook

Operational notes for running the WorldForge demo stack end-to-end. Paired with:

- [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) — the 45s storyboard (what the recording looks like, beat by beat)
- [`LAUNCH_TODOS.md`](LAUNCH_TODOS.md) — launch checklist (what's outstanding)

This doc covers *how to actually run the stack and produce the flow the script describes*, plus the design invariants of the corpus so future edits don't accidentally break the hero contradiction.

---

## Stack bring-up

Clean slate before recording:

```bash
docker compose down -v           # wipe postgres + qdrant volumes
docker compose up -d --build     # builds frontend + backend into one container
```

Ports: API + frontend 8080, OpenWebUI 3000, Qdrant 6333, PostgreSQL 5432.

### Health check

The health route is `/health`, **not** `/api/v1/health`. The SPA catch-all serves `index.html` for unknown paths, so a non-200 at `/api/v1/health` looks ambiguous — always use `/health`.

```bash
curl http://localhost:8080/health
# {"status":"healthy","services":{"generator":true,"embedder":true}}
```

### Known gotcha: stale alembic revision

If you've run the stack before on a different branch, the postgres volume may hold an alembic revision that no longer exists in code. Symptom: the `canon_api` container exits with code 3, and `docker compose logs canon_api` shows the alembic context lines but no traceback. Surface the error by running migrations in a one-shot container:

```bash
MSYS_NO_PATHCONV=1 docker compose run --rm -e PYTHONUNBUFFERED=1 canon_api uv run alembic upgrade head
# FAILED: Can't locate revision identified by 'xxxxxxxxxxxx'
```

Fix: dump existing data, then wipe volumes.

```bash
mkdir -p db-backups
docker compose exec -T postgres pg_dump -U canon_user canon_builder \
  > "db-backups/backup-$(date +%Y%m%d-%H%M%S).sql"
docker compose down -v
docker compose up -d --build
```

Rollback a dump with:

```bash
docker compose up -d postgres
docker compose exec -T postgres psql -U canon_user canon_builder \
  < db-backups/backup-YYYYMMDD-HHMMSS.sql
```

---

## Headless dry-run (for verifying the flow before recording)

### Bulk upload

The script depends on `httpx`, which lives in the backend venv, not a scripts venv. Run from `backend/`:

```bash
cd backend
uv run python ../scripts/bulk_upload.py ../demo-corpus --project "Homebrew Campaign"
```

Flags: `--project NAME` (required), `--description DESC` (optional), `--project-id UUID` (use existing project instead of creating).

### Drag-drop contradiction doc

Upload `session-03.md` separately (simulates Beat 3):

```bash
PROJECT_ID=<from bulk_upload output>
curl -X POST "http://localhost:8080/api/v1/projects/$PROJECT_ID/documents/upload" \
  -F "file=@../demo-corpus-incoming/session-03.md"
```

**Wait ~75 seconds** for the background contradiction scan (longer than a naïve single-pair LLM call because the scan embeds every chunk of the new doc, finds top-10 similar chunks project-wide, and classifies each cross-doc pair).

### Inspect results

```bash
curl "http://localhost:8080/api/v1/projects/$PROJECT_ID/contradictions" | python -m json.tool
curl -X POST "http://localhost:8080/api/v1/projects/$PROJECT_ID/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What happened to Duke Aldric?", "top_k": 5}'
```

---

## Expected results

### Contradictions page (Beat 4)

Three contradictions; hero at the top:

1. **session-03.md ↔ kingdom-history.md** — HERO
   - session-03 quote (verbatim): *"Duke Aldric was murdered in his chambers during the harvest festival"*
   - kingdom-history quote (verbatim): *"Duke Aldric succumbed to fever in the spring of 847, six months before the harvest festival"*
2. kingdom-history.md ↔ session-01.md — atmospheric (letter-delivery anachronism)
3. kingdom-history.md ↔ session-03.md — mirror of #1

### Query (Beat 5)

"What happened to Duke Aldric?" produces an answer that opens with **"Based on the provided sources, there are contradictory accounts of what happened to Duke Aldric"** and contrasts the official fever account with the murder, citing both `kingdom-history.md` and `session-03.md`.

---

## Corpus design invariants

The corpus is tuned to make the hero contradiction surface reliably. If you edit the corpus, preserve these invariants or the Beat 4 shot will regress.

### session-03.md is short and leads with the murder

The first draft was a full in-character session log with RPG metadata (Date played, party list, Stealth rolls, GM notes). It failed to trigger the hero contradiction — two reasons:

1. **Format embedding bias.** Session logs embed as a *genre*. When the scan embedded session-03's chunk, the top-5 similar chunks were all other session logs (session-01, session-02). Kingdom-history's fever chunk sat at rank 9–10, past the retrieval window. Shortening the chunk and front-loading the hero fact shifted the embedding's dominant signal from "session log format" to "Duke Aldric's death".
2. **LLM meta-framing.** The original doc contained a GM aside: *"The official record will eventually claim a different cause — the regent's office is going to bury this"*. That sentence primed the classifier to treat the two versions as expected narrative framing rather than mutually exclusive facts, so even when the pair reached the LLM it returned `is_contradiction: false`. Drop any meta-commentary that acknowledges multiple versions exist intentionally.

**Keep:**
- Verbatim first content sentence: "Duke Aldric was murdered in his chambers during the harvest festival."
- Doc length around 1200 chars (single chunk).

**Drop or avoid:**
- GM meta-notes that frame the murder as "the hidden truth vs. the official record."
- Long RPG scaffolding (combat blocks, session consequences lists) that shifts the embedding toward session-log genre.

### kingdom-history.md's succession rule stays vague

Earlier drafts specified primogeniture by male line, then by "eldest surviving child by birthright." Both contradicted Lady Elayne being named heir (she's younger than her half-brother Edric), which surfaced as a distracting secondary contradiction. Current wording — *"hereditary, with final confirmation of each new duke requiring the assent of the Council of Stewards"* — names no specific rule, so the only contradiction the LLM finds is the fever/murder pair.

### session-01.md and session-02.md avoid asserting Duke Aldric is alive

Both sessions happen in autumn 847, after the kingdom-history's "spring 847" fever claim. Any line asserting the duke is alive at that point (e.g. "deliver to Duke Aldric personally," "Audience with Duke Aldric requested") contradicts kingdom-history and fires extra noise. Rephrased to "the duke's seat" / "the ducal seat" to preserve narrative without the time-state assertion.

---

## Product-side tunings that unlock the demo

These aren't corpus fixes — they live in the backend.

### Contradiction scan top-k is 10

`backend/app/services/contradiction_service.py` defines `SIMILAR_CHUNKS_TOP_K = 10`. Was 5 originally. The bump matters because format-mismatched but topically-related chunks can sit at rank 6–10, beyond what a tight top-5 window reaches. The cost is roughly 2× LLM classification calls per scan, acceptable for single-user use. If you revisit: don't drop below 10 without re-running the dry-run.

---

## Teardown

Between takes or stopping for the day (keeps data for next session):

```bash
docker compose down
```

Clean slate for the next recording session:

```bash
docker compose down -v
docker compose up -d --build
```

After a clean bring-up, re-run the bulk upload and the session-03 drop before recording — contradictions don't persist across volume wipes.
