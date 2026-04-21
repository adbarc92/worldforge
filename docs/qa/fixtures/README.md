# QA Fixtures

Test data referenced by `docs/qa/pr-4-checklist.md`.

## `contradicting-pair/`
Two short markdown files that disagree on every fact about the fictional
kingdom of Valeria. Upload them together to a fresh project to exercise
automatic contradiction detection (including the dedup race fix — commit
`02fc817`).

## `aegis-demo/`
A six-document canon about **Aegis Station**, a deep-space research
outpost studying a recurring signal from a gas giant. Includes `.md`,
`.txt`, and `.pdf` formats and one intentional contradiction between
`history.md` and `old_logs.md`. Useful for end-to-end verification of
chat, documents, contradictions, and synthesis flows.
