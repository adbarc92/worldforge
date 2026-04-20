# QA Checklist — PR #4 (qa-bugfixes)

Covers the four commits on `feature/qa-bugfixes`. App at `http://localhost:8080`.

## Pre-flight

```bash
curl -s http://localhost:8080/health
# expect: {"status":"healthy","services":{"generator":true,"embedder":true}}

curl -s http://localhost:8080/api/v1/projects | python -m json.tool
# expect: Test (4 docs) and Aegis Station (6 docs)
```

If Aegis Station is missing, see **Reseed demo** at the bottom.

---

## 1. Chat — basic query with citations

- Open `/`, pick **Aegis Station** from the sidebar.
- Ask: *"What is the Halion anomaly?"*
- **Expect:** grounded answer referencing the signal; citations badge under the reply showing `signal.txt`, `station.md`, possibly `tech_brief.pdf`, each with a % score.

## 2. Chat — resets on project switch *(fix: `46d5510`)*

- Still on Aegis Station, send a couple of messages.
- Switch the sidebar dropdown to **Test**.
- **Expect:** chat pane empties immediately. No Aegis messages linger.
- Ask Test a question; answer comes back scoped to Test's canon.

## 3. Chat — self-heal on deleted project *(fix: `d31ab05`)*

- Select a project, navigate to Chat.
- In a terminal, delete that project via API:
  ```bash
  curl -X DELETE http://localhost:8080/api/v1/projects/<id>
  ```
- Send one message.
- **Expect:** one error bubble: *"Error: Project not found"*. On the next render, chat falls back to *"Select a project to start chatting."* **No reload required.**

## 4. Documents — three formats ingest cleanly

- Navigate to **Documents** on Aegis Station.
- **Expect:** `station.md`, `crew.md`, `signal.txt`, `history.md`, `tech_brief.pdf`, `old_logs.md`. All status `completed`. Chunk counts non-zero.

## 5. Contradictions — auto-detected + grouped UI

- Navigate to **Contradictions** on Aegis Station.
- **Expect:** one open record grouped as `old_logs.md vs history.md` about the founding date (2384 vs 2387) and Vaskel vs Alvarado.

## 6. Contradictions — no duplicate for the same pair *(fix: `02fc817`)*

```bash
# Create a throwaway project and upload two contradicting docs concurrently
PID=$(curl -s -X POST http://localhost:8080/api/v1/projects \
  -H "Content-Type: application/json" -d '{"name":"Dup-Check"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s -X POST "http://localhost:8080/api/v1/projects/$PID/documents/upload" \
  -F "file=@docs/qa/fixtures/contradicting-pair/doc-a.md" &
curl -s -X POST "http://localhost:8080/api/v1/projects/$PID/documents/upload" \
  -F "file=@docs/qa/fixtures/contradicting-pair/doc-b.md" &
wait
sleep 30
curl -s "http://localhost:8080/api/v1/projects/$PID/contradictions?status=open" \
  | python -c "import sys,json;print('total:',json.load(sys.stdin)['total'])"
# expect: total: 1   (before the fix: total: 2)
curl -s -X DELETE "http://localhost:8080/api/v1/projects/$PID"
```

## 7. Contradictions — resolve with note

- On the Aegis Station contradictions page, click **Resolve** on the record.
- Enter a note: *"Canon: 2384 per archivist logs."*
- **Expect:** moves to the Resolved tab; note visible; `Reopen` button shown.

## 8. Synthesis — gate message links to contradictions *(fix: `3bc3775`)*

- First, **Reopen** the resolved contradiction so it's open again.
- Navigate to **Synthesis**.
- **Expect:** *"There is 1 open __contradiction__. Resolve or dismiss it before generating a synthesis."*
  - Grammar is singular.
  - The word **contradiction** is underlined.
  - Generate buttons disabled.
- Click **contradiction** → lands on `/contradictions` with the open record visible.

## 9. Synthesis — end-to-end generate

- Back on Contradictions, **Dismiss** (or resolve) the record.
- Navigate to Synthesis → click **Quick Generate**.
- **Expect:** outline generates in ~30–60s, then sections fill in. Final view shows the full primer, **Download** and **Regenerate** buttons.
- Click **Download** → `.md` file downloads.

## 10. Projects — stale-project reload clears gracefully *(fix: `5a684bc`)*

- Select any project, reload `/` with `?bust=1` appended.
- Now delete the selected project via API (step 3's curl).
- Reload again.
- **Expect:** sidebar dropdown shows *"Select a project..."*. Chat shows *"Select a project to start chatting."* Storage cleared automatically.

---

## Reseed demo

If you ever want to wipe and rebuild the Aegis project:

```bash
# (delete old Aegis if it exists)
curl -s http://localhost:8080/api/v1/projects \
  | python -c "import sys,json;[print(p['id']) for p in json.load(sys.stdin) if p['name']=='Aegis Station']" \
  | xargs -I {} curl -s -X DELETE http://localhost:8080/api/v1/projects/{}

# Recreate + upload
PID=$(curl -s -X POST http://localhost:8080/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Aegis Station","description":"Mystery in deep space"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
SRC="docs/qa/fixtures/aegis-demo"
for f in station.md crew.md signal.txt history.md tech_brief.pdf old_logs.md; do
  curl -s -X POST "http://localhost:8080/api/v1/projects/$PID/documents/upload" \
    -F "file=@$SRC/$f" > /dev/null
done
```
