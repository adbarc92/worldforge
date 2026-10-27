# World-Consistency Checker — Test Data

Test documents for validating a world-consistency checking application, built from real worldbuilding content (Disruption RPG).

## Structure

### Canonical ("current") documents — represent ground truth
- `cosmology_current.md` — Realms, Eidolons, Ascension, Exousia, magic system
- `characters_current.md` — Party roster, backstories, key NPCs
- `factions_current.md` — The Collective, Vanarites, Elpidi, Glyphein, Union
- `locations_current.md` — Kyanos, Kuklos Anankes, the Unknown (layered zones)
- `story_current.md` — Premise, Disruption mechanics, endings, themes

### Older iteration ("v1") documents — contain contradictions
- `cosmology_v1_draft.md` — Early cosmology with structural differences
- `characters_v1_draft.md` — Early character concepts with changed backstories
- `factions_v1_draft.md` — Early faction design with different details
- `technology_v1_notes.md` — Early tech notes (no canonical counterpart)
- `story_v1_outline.md` — Early story outline with different plot points

### Answer key
- `ANSWER_KEY.md` — All 50 contradictions cataloged with severity and subtlety ratings

## Contradiction Types

The test set includes contradictions across several dimensions:

| Type | Example |
|------|---------|
| **Numerical** | 5 realms vs. 4; 7 Elders vs. 5; timelines shifted |
| **Naming** | Gandharva vs. Vanaheim; Runic Builder vs. Rune Smith |
| **Structural** | 3 Ascension conditions vs. 4; 4 magic forms vs. 3 |
| **Backstory** | Different family details, professions, appearances |
| **Thematic** | Different shadow aspects for Eidolons |
| **Temporal** | Different timelines for the same events |
| **Identity** | Elpidi as distinct race vs. Glyphein bloodline |
| **Attribution** | Who created ampoules; who forged Asura |
| **Cross-document** | Contradictions spanning multiple v1 files |

## Difficulty Distribution

- **14 obvious** contradictions (direct numerical/naming conflicts)
- **22 moderate** contradictions (require comparing parallel descriptions)
- **14 subtle** contradictions (buried in prose, single-word swaps, or require inference)

## Usage

Feed the documents to a consistency checker without the answer key. Compare detected contradictions against `ANSWER_KEY.md` to measure precision (are flagged items real contradictions?) and recall (how many of the 50 were found?).

For harder tests, feed only the v1 documents — the checker must find internal inconsistencies within the older iteration (items 49-50 in the answer key).
