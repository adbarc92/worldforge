"""
Neo4j graph database service for knowledge graph
"""
from typing import List, Dict, Any
from neo4j import GraphDatabase
from loguru import logger

from app.core.config import settings


class Neo4jService:
    """Service for interacting with Neo4j knowledge graph"""

    def __init__(self):
        """Initialize Neo4j driver"""
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        """Close the Neo4j driver"""
        self.driver.close()

    async def create_entity(
        self,
        entity_id: str,
        entity_type: str,
        properties: Dict[str, Any]
    ):
        """
        Create an entity node in the graph

        Args:
            entity_id: Unique entity identifier
            entity_type: Type of entity (Character, Location, etc.)
            properties: Entity properties
        """
        with self.driver.session() as session:
            query = f"""
            MERGE (e:{entity_type} {{id: $entity_id}})
            SET e += $properties
            RETURN e
            """
            try:
                result = session.run(
                    query,
                    entity_id=entity_id,
                    properties=properties
                )
                logger.info(f"Created entity: {entity_id} ({entity_type})")
                return result.single()
            except Exception as e:
                logger.error(f"Error creating entity in Neo4j: {e}")
                raise

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ):
        """
        Create a relationship between two entities

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
        """
        with self.driver.session() as session:
            query = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[r:{relationship_type}]->(target)
            SET r += $properties
            RETURN r
            """
            try:
                properties = properties or {}
                result = session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    properties=properties
                )
                logger.info(f"Created relationship: {source_id} -{relationship_type}-> {target_id}")
                return result.single()
            except Exception as e:
                logger.error(f"Error creating relationship in Neo4j: {e}")
                raise

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
        with self.driver.session() as session:
            query = f"""
            MATCH path = (start {{id: $entity_id}})-[*1..{depth}]-(related)
            RETURN DISTINCT related, length(path) as distance
            ORDER BY distance
            LIMIT 50
            """
            try:
                result = session.run(query, entity_id=entity_id)
                entities = []
                for record in result:
                    node = record["related"]
                    entities.append({
                        "id": node.get("id"),
                        "type": list(node.labels)[0] if node.labels else "Unknown",
                        "properties": dict(node),
                        "distance": record["distance"]
                    })
                return entities
            except Exception as e:
                logger.error(f"Error getting related entities: {e}")
                raise

    async def find_entity_overlaps(
        self,
        doc_id_1: str,
        doc_id_2: str
    ) -> List[Dict[str, Any]]:
        """
        Find entities that appear in both documents

        Args:
            doc_id_1: First document ID
            doc_id_2: Second document ID

        Returns:
            List of overlapping entities
        """
        with self.driver.session() as session:
            query = """
            MATCH (d1:Document {id: $doc_id_1})-[:CONTAINS]->(e)<-[:CONTAINS]-(d2:Document {id: $doc_id_2})
            RETURN e, labels(e) as types
            """
            try:
                result = session.run(query, doc_id_1=doc_id_1, doc_id_2=doc_id_2)
                entities = []
                for record in result:
                    node = record["e"]
                    entities.append({
                        "id": node.get("id"),
                        "types": record["types"],
                        "properties": dict(node)
                    })
                return entities
            except Exception as e:
                logger.error(f"Error finding entity overlaps: {e}")
                raise

    async def delete_document_entities(self, document_id: str):
        """Delete all entities and relationships for a document"""
        with self.driver.session() as session:
            query = """
            MATCH (d:Document {id: $document_id})-[r:CONTAINS]->(e)
            DETACH DELETE e, r
            """
            try:
                session.run(query, document_id=document_id)
                logger.info(f"Deleted entities for document: {document_id}")
            except Exception as e:
                logger.error(f"Error deleting document entities: {e}")
                raise
