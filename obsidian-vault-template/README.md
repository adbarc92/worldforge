# Canon Builder - Obsidian Vault Template

This is a template vault structure for Canon Builder. Copy this directory to create your own canon vault.

## Structure

```
canonical/           # User-verified canonical content
├── characters/      # Character profiles
├── locations/       # Places, regions, worlds
├── events/          # Historical events, battles, meetings
├── concepts/        # Abstract ideas, systems, philosophies
├── magic-system/    # Magic/technology systems
└── history/         # Timelines and chronologies

proposed/            # AI-generated proposals pending review
└── pending-review/  # Proposals awaiting user decision

templates/           # Markdown templates for consistency
```

## Using This Vault

1. Copy this template to a new location
2. Open it in Obsidian
3. Use the templates for creating new canonical entries
4. AI-generated proposals will appear in `proposed/pending-review/`
5. After review, move accepted proposals to appropriate canonical folders

## Frontmatter Format

Each canonical document should include YAML frontmatter:

```yaml
---
id: unique_id
type: character|location|event|concept
tags: [tag1, tag2]
canon_status: canonical|proposed
created: YYYY-MM-DD
modified: YYYY-MM-DD
provenance: user_upload|ai_generated
sources: [document_references]
---
```

## Graph View

Use Obsidian's graph view to visualize relationships between entities. Link entities using `[[wiki-style links]]`.
