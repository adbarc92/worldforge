# WorldForge Demo Script & Storyboard

**Goal:** a silent, autoplay-friendly screen recording that sells WorldForge in under a minute. Contradiction detection is the hero. Everything else is supporting evidence.

**Deliverables:**
- **Primary cut:** 45 seconds. For README, Reddit, Discord, product page.
- **Short cut:** 25–30 seconds. For X/Twitter autoplay. Trim Beat 2 and shorten Beat 5.
- **Formats:** MP4 (X/Discord), GIF (README/Reddit), ~1080p cropped to browser.

**Style:**
- No voiceover. Captions and brief title cards only — must play muted.
- Use real-looking worldbuilding notes, not lorem ipsum. Authenticity sells.
- One hero moment: the contradiction reveal. Hold it long enough to read.

---

## Pre-Production Checklist

### Corpus prep (30 min)

Use the same "duke died of fever vs. murdered" contradiction that appears in `LAUNCH_TWEETS.md` and the README origin story. Consistency across assets reinforces the brand.

Create a folder `demo-corpus/` with ~6–8 files that look like real worldbuilding notes:

- `kingdom-history.md` — mentions "Duke Aldric died of fever in the spring of 847"
- `session-03.md` — session log describing the duke's murder in his chambers (the contradiction)
- `factions.md` — atmosphere, no contradiction
- `npcs-nobility.md` — atmosphere, references the duke neutrally
- `session-01.md`, `session-02.md` — atmosphere
- `world-bible.md` — atmosphere

The contradiction document (`session-03.md`) is uploaded separately in Beat 3, not with the bulk. Everything else goes in the bulk upload.

### Environment (15 min)

- Close every app except the browser and terminal (no Slack/Discord notifications mid-take).
- Browser: Chrome/Edge in a clean window, 1920×1080, bookmarks bar hidden.
- Terminal: black background, large font (18–20pt), no personal paths visible in the prompt.
- System dock/taskbar autohidden.
- Mouse pointer highlighted via OS accessibility or a tool like [Cursor Highlighter](https://cursor-highlighter.com/) so viewers can follow clicks.

### Recording setup

- **OBS Studio** (free, best quality) or Windows Game Bar / macOS QuickTime.
- Record at 1080p60. Crop in post to the browser window only (usually ~1440×900 after crop).
- Mute audio input — no room noise needed.
- Do several takes. Don't narrate; just perform the clicks cleanly.

### Tools for post

- **DaVinci Resolve** (free) or **CapCut** for cuts, title cards, speed ramps.
- **ezgif.com** or **gifski** (Mac) for MP4 → GIF conversion. Target <5MB GIF for GitHub/Reddit.

---

## Storyboard (45-second primary cut)

Each shot lists: **time · what's on screen · optional title card · notes.**

### Beat 1 — The problem (0:00–0:03)

- **Screen:** File explorer / VS Code sidebar showing the `demo-corpus/` folder. ~8 markdown files visible with plausible names.
- **Title card (optional):** "Your worldbuilding is scattered across dozens of files."
- **Notes:** Hold 2 seconds on the folder so viewers register it's real notes. Cursor drifts across filenames but doesn't open any.

### Beat 2 — Ingest everything (0:03–0:10)

- **Screen:** Terminal. Type (or paste) the bulk upload command and hit enter:
  ```
  uv run python bulk_upload.py ./demo-corpus --project "Homebrew Campaign"
  ```
  Show the progress output as each file is embedded. Speed-ramp 2–3× in post if it takes longer than 7 seconds.
- **Title card:** "Upload it all."
- **Notes:** Keep the terminal on screen through the last "✓" line. The speed ramp should feel snappy but still legible.

### Beat 3 — Add the contradicting document (0:10–0:18)

- **Screen:** Switch to the WorldForge Documents page in the browser. Drag `session-03.md` onto the upload zone (or click-upload). Show the document transitioning from "processing" → "completed."
- **Title card:** *(none — let the action speak)*
- **Notes:** Slight pause after completion so viewers expect the reveal. Don't preemptively click to the Contradictions tab — let the UI surface it.

### Beat 4 — The hero moment: contradiction detected (0:18–0:35)

**This is the shot. Everything serves this.**

- **Screen:** Contradictions page. One card appears at the top of the list.
  - Highlighted text from `session-03.md`: *"Duke Aldric was murdered in his chambers during the harvest festival."*
  - Highlighted text from `kingdom-history.md`: *"Duke Aldric succumbed to fever in the spring of 847, six months before the harvest festival."*
  - LLM explanation visible below both quotes.
  - Both document citations visible.
- **Title card (start of beat):** "WorldForge catches the contradictions."
- **Notes:**
  - Hold this shot ~15 seconds so viewers can read both quotes.
  - Cursor can briefly underline each quote to guide the eye — don't overdo it.
  - No need to click "Resolve" — that's out of scope for the demo. Let the contradiction speak.

### Beat 5 — Query works too (0:35–0:45)

- **Screen:** Chat page. Type: *"What happened to Duke Aldric?"* Hit enter. Answer streams in with inline citations to both `kingdom-history.md` and `session-03.md`.
- **Title card:** "And it answers what you wrote." *(appears as the response finishes)*
- **End card (0:43–0:45):** Black screen with the logo (if you have one — text-only is fine), and:
  > **WorldForge**
  > Open source · self-hosted
  > github.com/adbarc92/worldforge

---

## Storyboard (25-second short cut for X)

Same corpus, same takes. Edit for autoplay feeds:

| Time | Beat | Change vs. primary |
|------|------|-------------------|
| 0:00–0:02 | Folder | Shorter hold |
| 0:02–0:05 | Bulk upload | Speed-ramped heavily, 3–4× |
| 0:05–0:10 | Drop contradicting doc | Same |
| 0:10–0:22 | **Contradiction reveal** | Full hold (hero beat, don't shorten) |
| 0:22–0:25 | End card | Skip the query beat entirely |

The query beat is the weakest in a feed context — cutting it is fine. The contradiction shot is load-bearing and must not be trimmed.

---

## Title Card Style

Keep cards minimal and consistent:

- Dark background (#0a0a0a or similar), white text.
- One sans-serif face (Inter, Geist, or system default).
- ~48pt, center-aligned, single line if possible, 2 lines max.
- Each card on screen 1.5–2 seconds, fade 150ms in/out.
- Do not overlap cards with UI — show them on black between shots, or letterboxed above the browser.

---

## What to Avoid

- **Don't narrate.** Autoplay feeds are muted. A voiceover excludes 80% of viewers.
- **Don't show settings, API keys, or the tech stack.** The viewer doesn't care yet.
- **Don't use a throwaway corpus.** "Foo/Bar/Baz" filenames kill credibility in one frame.
- **Don't rush the contradiction beat.** The whole video is built around it. 15 seconds of hold feels long while recording; it's right on playback.
- **Don't include the resolve/dismiss workflow.** Out of scope; adds friction to the pitch.
- **Don't add music.** Autoplay is muted, and music locks platform reach on some networks.

---

## Acceptance Criteria

- [ ] Runs 40–50s (primary) / 25–30s (short).
- [ ] Contradiction detection beat occupies ≥30% of total runtime.
- [ ] No voiceover required to understand what the tool does.
- [ ] Viewer seeing only the first 5 seconds can tell it's a tool for worldbuilding notes.
- [ ] Viewer seeing only the last 5 seconds knows the project name and where to find it.
- [ ] Recorded filenames look like real worldbuilding notes, not demo filler.
- [ ] GIF version is <5MB and plays cleanly in a Reddit/README preview.

---

## Delivery

Once recorded, save outputs under `docs/images/`:

- `docs/images/demo.gif` — primary cut, <5MB
- `docs/images/demo.mp4` — primary cut, original quality
- `docs/images/demo-short.mp4` — 25–30s X cut

Then uncomment the `![WorldForge demo]` line in `README.md` (currently on line near the top) and push.
