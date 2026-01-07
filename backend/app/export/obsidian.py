"""
Obsidian format export for entities and relationships.
Generates Markdown files with wikilinks and YAML frontmatter.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database.models import Entity, Relationship, Document
from backend.app.config import settings


class ObsidianExporter:
    """
    Export worldbuilding content to Obsidian vault format.

    Generates:
    - One .md file per entity
    - YAML frontmatter with metadata
    - Wikilinks [[Entity Name]] for relationships
    - Graph JSON for visualization
    - Index file
    """

    def __init__(self, export_path: str = "/data/exports"):
        """
        Initialize Obsidian exporter.

        Args:
            export_path: Base path for exports
        """
        self.export_path = Path(export_path)
        self.export_path.mkdir(parents=True, exist_ok=True)

    async def export_full_canon(
        self,
        db: AsyncSession,
        export_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export all canonical entities and relationships to Obsidian format.

        Args:
            db: Database session
            export_name: Optional name for this export

        Returns:
            Export summary with file paths
        """
        # Create export directory
        if not export_name:
            export_name = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        export_dir = self.export_path / export_name
        export_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories by entity type
        entity_types = ["characters", "locations", "events", "concepts", "items"]
        type_dirs = {}
        for entity_type in entity_types:
            type_dir = export_dir / "entities" / entity_type
            type_dir.mkdir(parents=True, exist_ok=True)
            type_dirs[entity_type] = type_dir

        # Fetch all entities
        result = await db.execute(select(Entity))
        entities = result.scalars().all()

        # Fetch all relationships
        rel_result = await db.execute(select(Relationship))
        relationships = rel_result.scalars().all()

        # Create entity lookup for relationships
        entity_lookup = {entity.id: entity for entity in entities}

        # Group relationships by entity
        entity_relationships = {}
        for rel in relationships:
            # Add to source entity
            if rel.source_entity_id not in entity_relationships:
                entity_relationships[rel.source_entity_id] = {"outgoing": [], "incoming": []}
            entity_relationships[rel.source_entity_id]["outgoing"].append(rel)

            # Add to target entity
            if rel.target_entity_id not in entity_relationships:
                entity_relationships[rel.target_entity_id] = {"outgoing": [], "incoming": []}
            entity_relationships[rel.target_entity_id]["incoming"].append(rel)

        # Export each entity
        exported_files = []
        for entity in entities:
            file_path = await self._export_entity(
                entity=entity,
                relationships=entity_relationships.get(entity.id, {"outgoing": [], "incoming": []}),
                entity_lookup=entity_lookup,
                type_dirs=type_dirs
            )
            if file_path:
                exported_files.append(file_path)

        # Create index file
        index_path = await self._create_index(entities, export_dir)
        exported_files.append(index_path)

        # Create README
        readme_path = await self._create_readme(export_dir, len(entities), len(relationships))
        exported_files.append(readme_path)

        return {
            "export_id": str(uuid.uuid4()),
            "export_name": export_name,
            "export_path": str(export_dir),
            "entities_exported": len(entities),
            "relationships_exported": len(relationships),
            "files_created": len(exported_files),
            "created_at": datetime.utcnow().isoformat()
        }

    async def _export_entity(
        self,
        entity: Entity,
        relationships: Dict[str, List[Relationship]],
        entity_lookup: Dict[str, Entity],
        type_dirs: Dict[str, Path]
    ) -> Optional[Path]:
        """
        Export a single entity to Markdown file.

        Args:
            entity: Entity to export
            relationships: Entity relationships (outgoing/incoming)
            entity_lookup: Lookup dict for entity IDs
            type_dirs: Directory paths for each entity type

        Returns:
            Path to created file
        """
        # Determine directory
        entity_type_plural = self._get_type_plural(entity.type)
        if entity_type_plural not in type_dirs:
            entity_type_plural = "items"  # Default fallback

        # Sanitize filename
        safe_name = self._sanitize_filename(entity.name)
        file_path = type_dirs[entity_type_plural] / f"{safe_name}.md"

        # Generate YAML frontmatter
        frontmatter = self._generate_frontmatter(entity)

        # Generate content
        content_parts = [frontmatter]

        # Title
        content_parts.append(f"# {entity.name}\n")

        # Entity type badge
        content_parts.append(f"**Type:** {entity.type.capitalize()}\n")

        # Confidence score
        if entity.confidence_score:
            content_parts.append(f"**Confidence:** {entity.confidence_score:.2f}\n")

        # Description
        content_parts.append("\n## Description\n")
        content_parts.append(entity.canonical_description or "No description available.")
        content_parts.append("\n")

        # Relationships
        if relationships["outgoing"] or relationships["incoming"]:
            content_parts.append("\n## Relationships\n")

            # Outgoing relationships
            if relationships["outgoing"]:
                content_parts.append("\n### Related To\n")
                for rel in relationships["outgoing"]:
                    target_entity = entity_lookup.get(rel.target_entity_id)
                    if target_entity:
                        relation_type = rel.relation_type.replace("_", " ").capitalize()
                        content_parts.append(f"- **{relation_type}:** [[{target_entity.name}]]\n")

            # Incoming relationships
            if relationships["incoming"]:
                content_parts.append("\n### Referenced By\n")
                for rel in relationships["incoming"]:
                    source_entity = entity_lookup.get(rel.source_entity_id)
                    if source_entity:
                        relation_type = rel.relation_type.replace("_", " ").capitalize()
                        content_parts.append(f"- [[{source_entity.name}]] ({relation_type})\n")

        # Metadata
        if entity.metadata:
            content_parts.append("\n## Metadata\n")
            content_parts.append("```json\n")
            import json
            content_parts.append(json.dumps(entity.metadata, indent=2))
            content_parts.append("\n```\n")

        # Write file
        full_content = "\n".join(content_parts)
        file_path.write_text(full_content, encoding="utf-8")

        return file_path

    def _generate_frontmatter(self, entity: Entity) -> str:
        """
        Generate YAML frontmatter for entity.

        Args:
            entity: Entity object

        Returns:
            YAML frontmatter string
        """
        frontmatter = ["---"]
        frontmatter.append(f"id: {entity.id}")
        frontmatter.append(f"name: {entity.name}")
        frontmatter.append(f"type: {entity.type}")

        if entity.confidence_score:
            frontmatter.append(f"confidence: {entity.confidence_score}")

        frontmatter.append(f"created_at: {entity.created_at.isoformat()}")
        frontmatter.append("tags:")
        frontmatter.append(f"  - {entity.type}")
        frontmatter.append("  - worldbuilding")

        frontmatter.append("---\n")

        return "\n".join(frontmatter)

    async def _create_index(self, entities: List[Entity], export_dir: Path) -> Path:
        """
        Create index file listing all entities.

        Args:
            entities: List of all entities
            export_dir: Export directory

        Returns:
            Path to index file
        """
        index_path = export_dir / "index.md"

        content = ["# Worldbuilding Canon Index\n"]
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        content.append(f"Total Entities: {len(entities)}\n")

        # Group by type
        by_type = {}
        for entity in entities:
            if entity.type not in by_type:
                by_type[entity.type] = []
            by_type[entity.type].append(entity)

        # Create sections
        for entity_type in sorted(by_type.keys()):
            content.append(f"\n## {entity_type.capitalize()}s ({len(by_type[entity_type])})\n")

            # Sort entities alphabetically
            sorted_entities = sorted(by_type[entity_type], key=lambda e: e.name)

            for entity in sorted_entities:
                confidence_badge = ""
                if entity.confidence_score:
                    if entity.confidence_score >= 0.8:
                        confidence_badge = " ⭐"
                    elif entity.confidence_score < 0.5:
                        confidence_badge = " ⚠️"

                content.append(f"- [[{entity.name}]]{confidence_badge}\n")

        # Write file
        index_path.write_text("".join(content), encoding="utf-8")

        return index_path

    async def _create_readme(
        self,
        export_dir: Path,
        entity_count: int,
        relationship_count: int
    ) -> Path:
        """
        Create README file for the export.

        Args:
            export_dir: Export directory
            entity_count: Number of entities
            relationship_count: Number of relationships

        Returns:
            Path to README file
        """
        readme_path = export_dir / "README.md"

        content = [
            "# AetherCanon Builder Export\n",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "\n## Contents\n",
            f"- **Entities:** {entity_count}\n",
            f"- **Relationships:** {relationship_count}\n",
            "\n## Structure\n",
            "```\n",
            "export/\n",
            "├── entities/\n",
            "│   ├── characters/\n",
            "│   ├── locations/\n",
            "│   ├── events/\n",
            "│   ├── concepts/\n",
            "│   └── items/\n",
            "├── index.md\n",
            "└── README.md\n",
            "```\n",
            "\n## How to Use\n",
            "1. Open this folder as an Obsidian vault\n",
            "2. Browse `index.md` for an overview\n",
            "3. Navigate using [[wikilinks]]\n",
            "4. Use Obsidian's graph view to visualize relationships\n",
            "\n## Legend\n",
            "- ⭐ High confidence (≥0.8)\n",
            "- ⚠️ Low confidence (<0.5)\n",
            "\n## Entity Types\n",
            "- **Characters:** People, creatures, beings\n",
            "- **Locations:** Places, regions, worlds\n",
            "- **Events:** Battles, ceremonies, happenings\n",
            "- **Concepts:** Ideas, systems, organizations\n",
            "- **Items:** Objects, artifacts, weapons\n"
        ]

        readme_path.write_text("".join(content), encoding="utf-8")

        return readme_path

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize entity name for filename.

        Args:
            name: Entity name

        Returns:
            Safe filename
        """
        # Remove/replace invalid characters
        safe = name.replace("/", "-").replace("\\", "-")
        safe = safe.replace(":", "-").replace("*", "-")
        safe = safe.replace("?", "").replace('"', "")
        safe = safe.replace("<", "").replace(">", "")
        safe = safe.replace("|", "-")

        # Limit length
        if len(safe) > 200:
            safe = safe[:200]

        return safe.strip()

    def _get_type_plural(self, entity_type: str) -> str:
        """
        Get plural form of entity type.

        Args:
            entity_type: Entity type (singular)

        Returns:
            Plural form
        """
        plurals = {
            "character": "characters",
            "location": "locations",
            "event": "events",
            "concept": "concepts",
            "item": "items"
        }

        return plurals.get(entity_type, entity_type + "s")

    async def create_zip(self, export_dir: Path) -> Path:
        """
        Create ZIP archive of export.

        Args:
            export_dir: Export directory

        Returns:
            Path to ZIP file
        """
        zip_path = self.export_path / f"{export_dir.name}.zip"

        # Create ZIP archive
        shutil.make_archive(
            str(zip_path.with_suffix("")),
            "zip",
            export_dir
        )

        return zip_path
