"""
Entity extraction and knowledge graph construction service
"""
from typing import List, Dict, Any
import json
from loguru import logger

from app.core.config import settings
from app.services.ollama_service import OllamaService
from app.services.neo4j_service import Neo4jService


class EntityService:
    """Service for entity extraction and graph construction"""

    def __init__(self):
        """Initialize entity service"""
        self.ollama_service = OllamaService()
        self.neo4j_service = Neo4jService()

    async def extract_entities(
        self,
        text: str,
        document_id: str,
        document_title: str
    ) -> Dict[str, Any]:
        """
        Extract entities from text using LLM

        Args:
            text: Input text
            document_id: Source document ID
            document_title: Source document title

        Returns:
            Dictionary with entities and relationships
        """
        logger.info(f"Extracting entities from document: {document_id}")

        try:
            # Step 1: Extract entities
            entities = await self._extract_entities_with_llm(text)

            # Step 2: Extract relationships
            relationships = await self._extract_relationships_with_llm(text, entities)

            # Step 3: Build graph
            await self._build_graph(
                entities=entities,
                relationships=relationships,
                document_id=document_id,
                document_title=document_title
            )

            return {
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "entities": entities,
                "relationships": relationships
            }

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            raise

    async def _extract_entities_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """
        Use LLM to extract entities with structured output

        Args:
            text: Input text

        Returns:
            List of entity dictionaries
        """
        try:
            system_prompt = """You are an entity extraction system for worldbuilding documents.

Your task is to identify and extract entities from text. Extract:
- Characters (people, sentient beings)
- Locations (places, regions, buildings)
- Events (battles, meetings, significant occurrences)
- Concepts (ideas, systems, philosophies)
- Objects (artifacts, items, weapons)

Return ONLY valid JSON with this structure:
{
  "entities": [
    {
      "name": "Entity Name",
      "type": "CHARACTER|LOCATION|EVENT|CONCEPT|OBJECT",
      "description": "Brief description",
      "properties": {
        "key": "value"
      }
    }
  ]
}

Be thorough but avoid duplicates. Extract only explicitly mentioned entities."""

            user_prompt = f"""Extract entities from the following text:

{text[:2000]}

Return JSON:"""

            response = await self.ollama_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1  # Low temperature for structured output
            )

            # Parse JSON response
            try:
                # Clean response - LLMs sometimes add markdown
                cleaned = response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                data = json.loads(cleaned)
                entities = data.get("entities", [])

                logger.info(f"Extracted {len(entities)} entities")
                return entities

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse entity JSON: {e}")
                logger.debug(f"Response was: {response}")
                return []

        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            return []

    async def _extract_relationships_with_llm(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities

        Args:
            text: Input text
            entities: Previously extracted entities

        Returns:
            List of relationship dictionaries
        """
        if not entities:
            return []

        try:
            entity_names = [e["name"] for e in entities]
            entity_list = ", ".join(entity_names)

            system_prompt = """You are a relationship extraction system for worldbuilding knowledge graphs.

Your task is to identify relationships between entities.

Return ONLY valid JSON with this structure:
{
  "relationships": [
    {
      "source": "Entity Name",
      "target": "Entity Name",
      "type": "RELATIONSHIP_TYPE",
      "description": "Brief description of relationship"
    }
  ]
}

Common relationship types:
- LOCATED_IN, RULES, ALLY_OF, ENEMY_OF, CREATED, DESTROYED,
- PARTICIPATED_IN, OWNS, SIBLING_OF, PARENT_OF, MEMBER_OF, etc.

Use uppercase with underscores for relationship types."""

            user_prompt = f"""Extract relationships between these entities:

Entities: {entity_list}

From this text:
{text[:2000]}

Return JSON:"""

            response = await self.ollama_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )

            # Parse JSON response
            try:
                # Clean response
                cleaned = response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                data = json.loads(cleaned)
                relationships = data.get("relationships", [])

                logger.info(f"Extracted {len(relationships)} relationships")
                return relationships

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse relationship JSON: {e}")
                logger.debug(f"Response was: {response}")
                return []

        except Exception as e:
            logger.error(f"Error in relationship extraction: {e}")
            return []

    async def _build_graph(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        document_id: str,
        document_title: str
    ):
        """
        Build knowledge graph in Neo4j

        Args:
            entities: List of entities
            relationships: List of relationships
            document_id: Source document ID
            document_title: Source document title
        """
        try:
            # Create document node
            await self.neo4j_service.create_entity(
                entity_id=document_id,
                entity_type="Document",
                properties={
                    "title": document_title,
                    "id": document_id
                }
            )

            # Create entity nodes
            entity_id_map = {}
            for entity in entities:
                entity_id = f"{document_id}_{entity['name'].replace(' ', '_').lower()}"
                entity_id_map[entity["name"]] = entity_id

                await self.neo4j_service.create_entity(
                    entity_id=entity_id,
                    entity_type=entity.get("type", "Entity"),
                    properties={
                        "name": entity["name"],
                        "description": entity.get("description", ""),
                        "id": entity_id,
                        **entity.get("properties", {})
                    }
                )

                # Link entity to document
                await self.neo4j_service.create_relationship(
                    source_id=document_id,
                    target_id=entity_id,
                    relationship_type="CONTAINS",
                    properties={}
                )

            # Create relationships between entities
            for rel in relationships:
                source_name = rel.get("source")
                target_name = rel.get("target")

                if source_name in entity_id_map and target_name in entity_id_map:
                    await self.neo4j_service.create_relationship(
                        source_id=entity_id_map[source_name],
                        target_id=entity_id_map[target_name],
                        relationship_type=rel.get("type", "RELATED_TO"),
                        properties={
                            "description": rel.get("description", "")
                        }
                    )

            logger.info(f"Built graph for document {document_id}: "
                       f"{len(entities)} entities, {len(relationships)} relationships")

        except Exception as e:
            logger.error(f"Error building graph: {e}")
            raise

    async def get_entity_by_id(self, entity_id: str) -> Dict[str, Any]:
        """
        Get entity details from graph

        Args:
            entity_id: Entity identifier

        Returns:
            Entity dictionary
        """
        # TODO: Implement Neo4j query
        raise NotImplementedError("Entity retrieval not yet implemented")

    async def get_related_entities(
        self,
        entity_id: str,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get entities related to a given entity

        Args:
            entity_id: Entity identifier
            depth: Traversal depth

        Returns:
            List of related entities
        """
        return await self.neo4j_service.get_related_entities(entity_id, depth)

    async def find_contradictions(
        self,
        document_id_1: str,
        document_id_2: str
    ) -> List[Dict[str, Any]]:
        """
        Find potential contradictions between two documents

        Args:
            document_id_1: First document ID
            document_id_2: Second document ID

        Returns:
            List of potential contradictions
        """
        try:
            # Step 1: Find overlapping entities
            overlaps = await self.neo4j_service.find_entity_overlaps(
                document_id_1,
                document_id_2
            )

            if not overlaps:
                return []

            # Step 2: Use LLM to check for contradictions
            # TODO: Implement LLM-based contradiction checking
            # For now, just return the overlapping entities
            contradictions = []
            for entity in overlaps:
                contradictions.append({
                    "entity": entity,
                    "severity": "minor",
                    "description": f"Entity {entity['id']} appears in both documents - manual review needed"
                })

            return contradictions

        except Exception as e:
            logger.error(f"Error finding contradictions: {e}")
            raise
