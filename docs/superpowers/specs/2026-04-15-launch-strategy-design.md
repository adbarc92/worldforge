# WorldForge Launch Strategy

## Positioning

**Lead message:** "Catches when your worldbuilding contradicts itself."

Do not lead with "RAG worldbuilding tool" — that's a technical description, not a hook. Every TTRPG GM and series writer has felt the pain of contradicting their own lore. Contradiction detection is the unique, emotionally resonant differentiator. Everything else (upload, query, citations) is supporting evidence.

**One-liner:** WorldForge is an open-source, self-hosted tool that turns your worldbuilding docs into a queryable knowledge base — and catches when your lore contradicts itself.

---

## Two-Wave Staged Launch

### Timeline Overview

| Phase | Timing | Audience | Goal |
|-------|--------|----------|------|
| Pre-launch prep | Now through Week 0 | — | Assets, accounts, Reddit karma |
| Wave 1 | Week 1-2 | TTRPG GMs, worldbuilders | Product feedback, testimonials |
| Bridge | Week 2-3 | — | Collect feedback, polish, write blog post |
| Wave 2 | Week 3-4 | Devs, self-hosters, HN | Stars, forks, contributors |

---

## Pre-Launch Prep (Start Immediately)

### 1. Create Accounts

- [ ] **Reddit** — create account (or use existing). You need ~2 weeks of genuine participation before posting links in most subs. Auto-mod removes new accounts.
  - Subscribe to: r/worldbuilding, r/DMAcademy, r/dnd, r/rpg, r/selfhosted, r/LocalLLaMA
  - Comment helpfully on 10-15 posts across these subs over the next 2 weeks. Don't mention WorldForge. Just be a community member.
- [ ] **Hacker News** — create account at news.ycombinator.com. No karma requirement for Show HN, but having a non-empty profile builds credibility.
- [ ] **Dev.to** — create account, fill out bio. This is where the technical blog post goes.
- [ ] **Discord** — join worldbuilding and TTRPG servers:
  - Worldbuilding (search "worldbuilding" on Discord server directories)
  - D&D / TTRPG community servers (many have #tools or #resources channels)
  - Foundry VTT Discord (has a #showcase channel)

### 2. Record the Demo

This is the single most important asset. A 30-60 second screen recording that shows contradiction detection in action.

**Script:**
1. (0-5s) Show a folder of markdown files — visibly real worldbuilding notes, not lorem ipsum
2. (5-15s) Bulk upload them into WorldForge. Show the ingestion completing.
3. (15-25s) Upload one more document that contains a contradiction with existing canon
4. (25-45s) Show the contradiction detection result: "Your new document says X, but Document Y says Z" with citations
5. (45-60s) Quick query: ask a question, get a cited answer. Show this is a full knowledge base, not just a linter.

**Recording tips:**
- Use a real corpus (your actual worldbuilding notes are ideal — authenticity reads)
- OBS Studio or Windows built-in screen recorder both work
- 1080p, crop to just the browser window
- No voiceover needed — captions/text overlays are better for autoplay in feeds
- Export as both MP4 (for X/Discord) and GIF (for README/Reddit)
- Keep it under 60 seconds. Under 30 is even better for X.

### 3. Update the README

The current README is functional but doesn't lead with the hook. Restructure:

```
# WorldForge

**Your worldbuilding has contradictions. This finds them.**

Upload your lore documents — session notes, story bibles, wiki exports. 
WorldForge chunks and embeds them into a vector database, then lets you:

- **Detect contradictions** when new content conflicts with existing canon
- **Query your world** in plain English with cited answers
- **Synthesize across documents** to connect dots you missed

Open source. Self-hosted. One `docker compose up`.

[Screenshot/GIF of contradiction detection here]
```

- Add the demo GIF right below the tagline
- Move the API table and technical details further down
- Add a "Why WorldForge?" section that tells the 3-sentence origin story

### 4. Prepare the Origin Story Blurb (Wave 1)

Short, relatable, first-person. Use this as the template for Reddit/Discord posts:

> I DM a homebrew campaign that's been running for two years. I've got session notes, faction docs, NPC backstories scattered across dozens of files. Last month I told my players the duke was murdered — then a player pulled up my own notes showing I'd written he died of fever six months ago.
>
> So I built WorldForge. You upload your worldbuilding docs and it turns them into a knowledge base you can query. But the feature I'm most proud of is contradiction detection — it catches when new content conflicts with what you've already established.
>
> It's open source and self-hosted. Runs with a single `docker compose up`.

Adapt this for each channel (Reddit post body, Discord message, etc.) but keep the core: **personal pain → solution → the key feature**.

### 5. Draft the Technical Blog Post (Wave 2)

Target: 1500-2000 words on Dev.to. This is what you link from Hacker News.

**Outline:**

1. **The problem** (200 words) — worldbuilding inconsistency, why existing tools don't solve it
2. **Why contradiction detection is hard** (300 words) — naive approaches (keyword matching) fail, you need semantic understanding across documents, challenges of chunked retrieval
3. **Architecture** (400 words) — tech stack diagram, why FastAPI + Qdrant + Claude, how the pipeline works (ingest → chunk → embed → detect)
4. **How contradiction detection works** (400 words) — the core algorithm, how you compare new chunks against existing canon, prompt engineering for contradiction identification, handling false positives
5. **What I learned** (200 words) — surprises, things that didn't work, what you'd do differently
6. **Try it yourself** (100 words) — link to repo, `docker compose up`, demo GIF

**Title options (pick one for HN):**
- "Show HN: WorldForge — catches contradictions in your worldbuilding lore"
- "Show HN: I built an open-source tool that detects when your fictional world contradicts itself"
- "Show HN: WorldForge — RAG-powered worldbuilding with contradiction detection"

Recommend option 2 — it's specific, intriguing, and doesn't require knowing what RAG means.

### 6. Update the X Thread Draft

The existing draft in `docs/LAUNCH_TWEETS.md` is solid but leads with the generic pitch. Restructure:

**New Tweet 1 (Hook):**
> I kept contradicting my own worldbuilding lore mid-session. So I built a tool that catches it.
>
> WorldForge scans your docs for contradictions against your existing canon. Open source, self-hosted.
>
> [demo GIF]

Move the existing tweets 2-7 after this. The contradiction angle should hit in the first 280 characters.

Prepare **two versions** of the thread:
- **Wave 1 version** — casual, GM-focused, leads with the pain ("I kept contradicting my own lore")
- **Wave 2 version** — technical, leads with the architecture/approach ("Here's how I built semantic contradiction detection on top of RAG")

---

## Wave 1: TTRPG Communities (Weeks 1-2)

### Channels & Posting Strategy

#### Reddit

| Subreddit | Angle | Post Type |
|-----------|-------|-----------|
| r/worldbuilding | "I built a tool that catches contradictions in your lore" | Text post with embedded GIF, origin story |
| r/DMAcademy | "Tool that checks your session notes for contradictions" | Text post framed as a DM resource |
| r/dnd | Same as DMAcademy, broader framing | Text post, shorter |
| r/rpg | System-agnostic framing ("TTRPG worldbuilding tool") | Text post |

**Reddit rules to follow:**
- Read each sub's self-promotion rules before posting. Most allow it if you're an active participant (hence the 2-week ramp).
- r/worldbuilding has a specific format for resource posts — check their sidebar.
- Post on Tuesday-Thursday, 10am-12pm EST for best engagement.
- Respond to every comment within the first 2 hours. This is where feedback comes from and engagement signals boost visibility.
- Do NOT cross-post the same text. Write a tailored version for each sub.

#### Discord

- Find servers with #tools, #resources, or #showcase channels
- Drop the demo GIF + 2-sentence description + GitHub link
- Be available to answer questions in real-time for the first hour
- Discord is low-stakes — good for early, informal feedback

#### X (Wave 1 version)

- Post the GM-focused thread
- Use hashtags: #ttrpg #dnd #worldbuilding #gamedev #indiedev
- Pin the thread to your profile
- Post the demo GIF as a standalone tweet a few days later (different content, same audience)

### What to Collect from Wave 1

Before Wave 2, you want:
- [ ] 3-5 quotes from real users ("this would have saved me from X")
- [ ] Bug reports and friction points from first-time setup
- [ ] Feature requests (don't build them yet — just note them)
- [ ] At least one user who successfully used it with their own corpus

These become social proof for the HN/dev launch.

---

## Bridge Period (Week 2-3)

- Fix any bugs or setup friction from Wave 1 feedback
- Finish and polish the technical blog post
- Add user quotes to the README if they give permission
- Prepare the HN submission

---

## Wave 2: Dev & Self-Hoster Audience (Weeks 3-4)

### Channels & Posting Strategy

#### Hacker News (Show HN)

- **Title:** "Show HN: I built an open-source tool that detects when your fictional world contradicts itself"
- **Link:** Dev.to blog post (not the GitHub repo directly — blog posts perform better on HN because they tell a story)
- **Post timing:** Tuesday-Thursday, 8-10am EST
- **First comment:** Post a comment immediately with: what it does, why you built it, tech stack, link to repo, link to demo
- **Engage:** HN comments are where the real conversation happens. Be responsive, technical, and honest about limitations. Don't be defensive.

**What HN cares about:**
- Novel technical approach (contradiction detection via RAG is interesting)
- Clean architecture and code quality
- Honest "what I learned" (vulnerability wins on HN)
- Easy to try (`docker compose up`)
- What they do NOT care about: worldbuilding specifically. Frame it as a technical problem (semantic contradiction detection) that happens to be applied to worldbuilding.

#### Reddit (Dev subs)

| Subreddit | Angle |
|-----------|-------|
| r/selfhosted | "Self-hosted RAG tool with contradiction detection — single docker compose" |
| r/LocalLLaMA | "Open-source RAG pipeline with contradiction detection" (note: you use cloud APIs, be upfront about this — they'll ask about local model support) |

#### Dev.to

- Publish the technical blog post
- Tag: #opensource #python #ai #rag
- Cross-post announcement in Dev.to's #discuss tag

#### X (Wave 2 version)

- Post the technical thread
- Tag relevant AI/dev accounts (but don't spam)
- If any TTRPG folks from Wave 1 posted about it, quote-tweet with the tech angle

---

## Content Checklist

### Must-have before Wave 1
- [ ] Demo recording (30-60s, GIF + MP4)
- [ ] Updated README with contradiction detection lead, demo GIF, origin story
- [ ] Reddit account with 2 weeks of genuine participation
- [ ] Origin story blurb (3-4 sentences)
- [ ] Tailored post drafts for each Wave 1 subreddit
- [ ] Updated X thread (GM-focused version)

### Must-have before Wave 2
- [ ] Technical blog post on Dev.to (1500-2000 words)
- [ ] HN Show HN post draft + first comment
- [ ] User quotes/testimonials from Wave 1 (added to README)
- [ ] Architecture diagram for blog post
- [ ] X thread (technical version)
- [ ] Tailored post drafts for r/selfhosted, r/LocalLLaMA

---

## Metrics to Track

You don't need analytics tooling — just check these manually:

- **GitHub:** stars, forks, issues opened, clones (GitHub traffic tab)
- **Reddit:** upvotes, comment count, any follow-up posts by users
- **HN:** points, comment count, position on front page
- **Docker:** if you publish to Docker Hub, pull count
- **Qualitative:** what questions are people asking? what's confusing? what excites them?

---

## Common Pitfalls to Avoid

1. **Don't astroturf.** One authentic post per community is plenty. If people like it, they'll share it.
2. **Don't lead with the tech stack.** GMs don't care that it's FastAPI + Qdrant. They care that it catches contradictions.
3. **Don't apologize for v1.** "It's early but..." undermines the pitch. Ship it confidently, acknowledge limitations honestly when asked.
4. **Don't vanish after posting.** The first 2 hours of engagement on Reddit/HN determine whether the post lives or dies. Block the time.
5. **Don't build features between waves.** Fix bugs and polish — don't add scope. Wave 2 should showcase the same product, better explained.
6. **Don't skip the r/LocalLLaMA disclaimer.** They will immediately ask about local model support. Be upfront: "Currently uses Claude + OpenAI APIs. Local model support is on the roadmap." Honesty is respected; discovering it after cloning is not.
