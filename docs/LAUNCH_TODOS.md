# Launch TODOs

Tracks outstanding work to ship the WorldForge v1.0.0 launch. Source of truth for "what's next?" between sessions.

## Status snapshot

- **Code:** v1.0.0 code-complete (merged via PR #4). 87 backend + 175 frontend tests passing, CI green.
- **Docs:** REQUIREMENTS/ROADMAP rewrite, launch strategy spec, README rebrand, and demo assets open in PRs [#5](https://github.com/adbarc92/worldforge/pull/5) and [#6](https://github.com/adbarc92/worldforge/pull/6).
- **Launch gate:** blocked on demo video and Reddit karma ramp. Plan: see `docs/superpowers/specs/2026-04-15-launch-strategy-design.md`.

---

## Phase 1 — Demo recording (pre-production)

Everything needed before hitting record. Full storyboard: `docs/DEMO_SCRIPT.md`.

### Dry-run the corpus end-to-end

- [x] `docker compose up -d --build` brings the full stack up cleanly. (Note: a stale postgres volume from a prior checkout can leave alembic at a missing revision and cause the api container to exit; if so, dump and `docker compose down -v` to wipe.)
- [x] `cd backend && uv run python ../scripts/bulk_upload.py ../demo-corpus --project "Homebrew Campaign"` loads all 6 files. (Run from `backend/` so httpx is on the venv path.)
- [x] Uploading `demo-corpus-incoming/session-03.md` surfaces the hero contradiction at the top of the Contradictions list — `session-03.md` ("Duke Aldric was murdered in his chambers during the harvest festival") vs `kingdom-history.md` ("Duke Aldric succumbed to fever in the spring of 847, six months before the harvest festival"). Three contradictions total; the secondary `kingdom-history` ↔ `session-01` flag is fine atmosphere.
- [x] Querying *"What happened to Duke Aldric?"* returns a clean RAG answer that explicitly contrasts the official fever account with the murder, citing both documents.
- [ ] **UI flow check (visual, manual):** open the app at http://localhost:8080 and click through Beats 1–5 to confirm labels match DEMO_SCRIPT — Documents page drag-drop zone, Contradictions page card layout, Chat page citation rendering. Patch the script if any text/UI has drifted.

### Recording tools

- [ ] OBS Studio (or Win Game Bar / macOS QuickTime) installed and tested at 1080p60.
- [ ] Cursor highlighter (OS accessibility setting or third-party tool) enabled.
- [ ] Post-production tool ready: DaVinci Resolve or CapCut.
- [ ] GIF conversion path chosen: ezgif.com (web) or gifski (Mac).

### Environment prep

Per DEMO_SCRIPT § "Environment":

- [ ] Browser: clean Chrome/Edge window, 1920×1080, bookmarks bar hidden.
- [ ] Terminal: black bg, 18–20pt font, prompt stripped of personal paths (set a temporary `PS1` / equivalent).
- [ ] Notifications silenced (Slack, Discord, mail, Teams).
- [ ] Taskbar/dock autohidden.

### Title-card copy (drafted from script)

Dark bg (#0a0a0a), white text, Inter/Geist/system sans at ~48pt, ≤2 lines, 1.5–2s on screen with 150ms fades.

- Beat 1 (optional): *"Your worldbuilding is scattered across dozens of files."*
- Beat 2: *"Upload it all."*
- Beat 4: *"WorldForge catches the contradictions."*
- Beat 5: *"And it answers what you wrote."*
- End card (Beat 5, 0:43–0:45):

  > **WorldForge**
  > Open source · self-hosted
  > github.com/adbarc92/worldforge

---

## Phase 2 — Recording

- [ ] Primary cut takes (Beats 1–5, target 45s, acceptance 40–50s).
- [ ] Short cut variants (or plan trims in post from the primary master).
- [ ] Hero shot: Beat 4 held ~15 seconds with both quotes legible — do not rush.

---

## Phase 3 — Post-production

- [ ] Primary cut: 40–50s, title cards between beats, no music, no voiceover.
- [ ] Short cut for X: 25–30s, skip Beat 5, preserve the Beat 4 hold.
- [ ] Export to `docs/images/`:
  - `demo.gif` — primary cut, <5MB.
  - `demo.mp4` — primary cut, original quality.
  - `demo-short.mp4` — X cut.
- [ ] Uncomment the `![WorldForge demo]` line near the top of `README.md`.
- [ ] Spot-check: GIF renders cleanly on GitHub (README preview) and Reddit preview.

---

## Phase 4 — Launch Wave 1 (TTRPG communities)

Per launch strategy spec. Requires Phases 1–3 complete.

- [ ] Reddit karma ramp: ~2 weeks of authentic contributions in r/worldbuilding, r/DMAcademy, r/DnDBehindTheScreen before posting.
- [ ] Prepare Discord intros for TTRPG servers.
- [ ] Publish Wave 1 posts per launch strategy spec.
- [ ] Monitor response; capture user feedback as issues.

## Phase 5 — Launch Wave 2 (devs / self-hosters)

- [ ] Show HN post.
- [ ] r/selfhosted + r/LocalLLaMA posts.
- [ ] Dev.to blog post ("How I built a RAG tool that catches contradictions" or similar).

---

## References

- Demo storyboard: [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md)
- Launch plan: [`docs/superpowers/specs/2026-04-15-launch-strategy-design.md`](superpowers/specs/2026-04-15-launch-strategy-design.md)
- Requirements: [`docs/REQUIREMENTS.md`](REQUIREMENTS.md)
- Roadmap: [`docs/ROADMAP.md`](ROADMAP.md)
