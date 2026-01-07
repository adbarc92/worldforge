"""
Entity extraction using LLM to identify characters, locations, events, concepts, and items.
Extracts structured entities from narrative text.
"""

import logging
from typing import List, Dict, Optional
import json

from ..llm.provider import get_llm_provider
from ..llm.prompts import (
    ENTITY_EXTRACTION_PROMPT,
    ENTITY_EXTRACTION_SCHEMA
)

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract worldbuilding entities from text using LLM."""

    ENTITY_TYPES = {"character", "location", "event", "concept", "item"}

    def __init__(self):
        """Initialize entity extractor with LLM provider."""
        self.llm = get_llm_provider()
        logger.info(f"Entity extractor initialized with LLM provider")

    async def extract_entities(
        self,
        text: str,
        document_id: str,
        chunk_info: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Extract entities from text using LLM.

        Args:
            text: Text to analyze
            document_id: Source document ID
            chunk_info: Optional chunk metadata

        Returns:
            List of extracted entity dictionaries
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for entity extraction")
            return []

        try:
            # Truncate text if too long (avoid token limits)
            max_text_length = 4000
            if len(text) > max_text_length:
                logger.warning(
                    f"Text too long ({len(text)} chars), truncating to {max_text_length}"
                )
                text = text[:max_text_length] + "..."

            # Format prompt
            prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)

            # Call LLM
            logger.debug(f"Extracting entities from {len(text)} chars of text")
            result = await self.llm.generate_structured(
                prompt=prompt,
                schema=ENTITY_EXTRACTION_SCHEMA,
                temperature=0.0
            )

            # Validate and enrich entities
            entities = []
            if isinstance(result, list):
                for entity_data in result:
                    entity = self._validate_and_enrich_entity(
                        entity_data,
                        document_id,
                        chunk_info
                    )
                    if entity:
                        entities.append(entity)

            logger.info(f"Extracted {len(entities)} entities")
            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            # Return empty list rather than failing completely
            return []

    async def extract_entities_from_chunks(
        self,
        chunks: List[Dict],
        document_id: str,
        max_chunks: Optional[int] = None
    ) -> List[Dict]:
        """
        Extract entities from multiple text chunks.

        Args:
            chunks: List of chunk dictionaries
            document_id: Source document ID
            max_chunks: Optional limit on chunks to process (for testing)

        Returns:
            Deduplicated list of entities
        """
        if not chunks:
            logger.warning("No chunks provided for entity extraction")
            return []

        try:
            all_entities = []

            # Process chunks (limit if specified)
            chunks_to_process = chunks[:max_chunks] if max_chunks else chunks
            logger.info(f"Processing {len(chunks_to_process)} chunks for entity extraction")

            for idx, chunk in enumerate(chunks_to_process):
                logger.debug(f"Processing chunk {idx + 1}/{len(chunks_to_process)}")

                chunk_entities = await self.extract_entities(
                    text=chunk["text"],
                    document_id=document_id,
                    chunk_info={
                        "chunk_index": chunk.get("chunk_index"),
                        "page_number": chunk.get("metadata", {}).get("page_number")
                    }
                )

                all_entities.extend(chunk_entities)

            # Deduplicate entities by name (case-insensitive)
            deduplicated = self._deduplicate_entities(all_entities)

            logger.info(
                f"Extracted {len(all_entities)} total entities, "
                f"{len(deduplicated)} after deduplication"
            )

            return deduplicated

        except Exception as e:
            logger.error(f"Error extracting entities from chunks: {e}")
            return []

    def _validate_and_enrich_entity(
        self,
        entity_data: Dict,
        document_id: str,
        chunk_info: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Validate and enrich entity data.

        Args:
            entity_data: Raw entity from LLM
            document_id: Source document ID
            chunk_info: Optional chunk metadata

        Returns:
            Enriched entity dictionary or None if invalid
        """
        try:
            # Validate required fields
            if not entity_data.get("name"):
                logger.warning("Entity missing name, skipping")
                return None

            if entity_data.get("type") not in self.ENTITY_TYPES:
                logger.warning(
                    f"Invalid entity type: {entity_data.get('type')}, skipping"
                )
                return None

            # Enrich with metadata
            enriched = {
                "name": entity_data["name"].strip(),
                "type": entity_data["type"],
                "description": entity_data.get("description", "").strip(),
                "confidence": entity_data.get("confidence", 0.5),
                "source_document_id": document_id,
                "source_chunk_index": chunk_info.get("chunk_index") if chunk_info else None,
                "source_page_number": chunk_info.get("page_number") if chunk_info else None
            }

            return enriched

        except Exception as e:
            logger.error(f"Error validating entity: {e}")
            return None

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Deduplicate entities by name (case-insensitive), keeping highest confidence.

        Args:
            entities: List of entity dictionaries

        Returns:
            Deduplicated list
        """
        # Group by lowercase name
        entity_map = {}

        for entity in entities:
            name_key = entity["name"].lower()

            if name_key not in entity_map:
                entity_map[name_key] = entity
            else:
                # Keep entity with higher confidence
                if entity["confidence"] > entity_map[name_key]["confidence"]:
                    entity_map[name_key] = entity

        return list(entity_map.values())

    async def extract_relationships(
        self,
        entities: List[Dict],
        text: str,
        document_id: str
    ) -> List[Dict]:
        """
        Extract relationships between entities (for future enhancement).

        Args:
            entities: List of entities found in text
            text: Source text
            document_id: Source document ID

        Returns:
            List of relationship dictionaries
        """
        # TODO: Implement relationship extraction in future iteration
        # For MVP, we'll focus on entities only
        logger.info("Relationship extraction not yet implemented")
        return []
