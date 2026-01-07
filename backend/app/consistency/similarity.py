"""
Similarity computation utilities for inconsistency detection.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import chromadb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config import settings
from backend.app.database.models import Entity, ProposedContent
from backend.app.ingestion.embedder import Embedder


class SimilarityEngine:
    """
    Computes semantic similarity between entities and content.

    Used for detecting potential contradictions and duplicate entities.
    """

    def __init__(self, similarity_threshold: float = None):
        """
        Initialize similarity engine.

        Args:
            similarity_threshold: Minimum similarity score to consider (0-1)
                                  Defaults to settings.similarity_threshold
        """
        self.threshold = similarity_threshold or settings.similarity_threshold
        self.embedder = Embedder()

        # Initialize ChromaDB for entity embeddings
        self.chroma_client = chromadb.PersistentClient(path=settings.chromadb_path)
        self.entity_collection = self.chroma_client.get_or_create_collection(
            name="worldforge_entities",
            metadata={"hnsw:space": "cosine"}
        )

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)

        # Compute cosine similarity
        similarity = cosine_similarity(vec1, vec2)[0][0]

        return float(similarity)

    async def find_similar_entities(
        self,
        entity_description: str,
        entity_type: str,
        db: AsyncSession,
        top_k: int = 5,
        include_proposed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find entities similar to the given description.

        Args:
            entity_description: Entity description text
            entity_type: Entity type (character, location, etc.)
            db: Database session
            top_k: Number of similar entities to return
            include_proposed: Whether to include proposed entities

        Returns:
            List of similar entities with similarity scores
        """
        # Generate embedding for query
        query_embedding = self.embedder.embed(entity_description)

        # Search ChromaDB entity collection
        try:
            results = self.entity_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"type": entity_type} if entity_type else None,
                include=["metadatas", "documents", "distances"]
            )
        except Exception:
            # Collection might be empty
            return []

        # Format results
        similar_entities = []
        if results["ids"][0]:
            for idx, entity_id in enumerate(results["ids"][0]):
                similarity_score = 1 - results["distances"][0][idx]  # Convert distance to similarity

                # Only include if above threshold
                if similarity_score >= self.threshold:
                    similar_entities.append({
                        "entity_id": entity_id,
                        "description": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "similarity_score": similarity_score
                    })

        # Optionally fetch from database for full details
        if similar_entities:
            entity_ids = [e["entity_id"] for e in similar_entities]

            # Get canonical entities
            canonical_result = await db.execute(
                select(Entity).where(Entity.id.in_(entity_ids))
            )
            canonical_entities = canonical_result.scalars().all()

            # Get proposed entities if requested
            proposed_entities = []
            if include_proposed:
                proposed_result = await db.execute(
                    select(ProposedContent)
                    .where(ProposedContent.id.in_(entity_ids))
                    .where(ProposedContent.review_status == "pending")
                )
                proposed_entities = proposed_result.scalars().all()

            # Merge database info with similarity results
            entity_lookup = {}
            for entity in canonical_entities:
                entity_lookup[entity.id] = {
                    "source": "canonical",
                    "entity": entity
                }
            for entity in proposed_entities:
                entity_lookup[entity.id] = {
                    "source": "proposed",
                    "entity": entity
                }

            # Enrich similarity results
            enriched_results = []
            for sim_entity in similar_entities:
                entity_id = sim_entity["entity_id"]
                if entity_id in entity_lookup:
                    enriched = {
                        **sim_entity,
                        "source": entity_lookup[entity_id]["source"],
                        "entity_data": entity_lookup[entity_id]["entity"]
                    }
                    enriched_results.append(enriched)

            return enriched_results

        return similar_entities

    async def detect_duplicate_entities(
        self,
        entity_name: str,
        entity_description: str,
        entity_type: str,
        db: AsyncSession,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect potential duplicate entities.

        Args:
            entity_name: Name of the entity
            entity_description: Description of the entity
            entity_type: Entity type
            db: Database session
            threshold: Custom similarity threshold (uses default if None)

        Returns:
            List of potential duplicates
        """
        similarity_threshold = threshold or self.threshold

        # Find similar entities
        similar = await self.find_similar_entities(
            entity_description=entity_description,
            entity_type=entity_type,
            db=db,
            top_k=10,
            include_proposed=True
        )

        # Filter for high similarity (potential duplicates)
        duplicates = []
        for entity in similar:
            # Check both high similarity and name matching
            similarity_score = entity["similarity_score"]
            entity_metadata = entity.get("metadata", {})
            existing_name = entity_metadata.get("name", "")

            # Consider duplicate if:
            # 1. Very high similarity (>0.95) OR
            # 2. High similarity (>threshold) AND similar names
            is_duplicate = (
                similarity_score > 0.95 or
                (similarity_score > similarity_threshold and
                 self._names_are_similar(entity_name, existing_name))
            )

            if is_duplicate:
                duplicates.append({
                    **entity,
                    "reason": "High similarity + name match" if similarity_score < 0.95 else "Very high similarity",
                    "confidence": similarity_score
                })

        return duplicates

    def _names_are_similar(self, name1: str, name2: str) -> bool:
        """
        Check if two entity names are similar.

        Args:
            name1: First name
            name2: Second name

        Returns:
            True if names are similar
        """
        # Simple comparison - can be enhanced with fuzzy matching
        name1_lower = name1.lower().strip()
        name2_lower = name2.lower().strip()

        # Exact match
        if name1_lower == name2_lower:
            return True

        # One is substring of other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return True

        # Check for common aliases (e.g., "Bob" vs "Robert")
        # This would require a name alias database - placeholder for now
        return False

    async def store_entity_embedding(
        self,
        entity_id: str,
        entity_name: str,
        entity_description: str,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store entity embedding in ChromaDB for future similarity searches.

        Args:
            entity_id: Unique entity ID
            entity_name: Entity name
            entity_description: Entity description
            entity_type: Entity type
            metadata: Additional metadata
        """
        # Generate embedding
        embedding = self.embedder.embed(entity_description)

        # Prepare metadata
        meta = {
            "name": entity_name,
            "type": entity_type,
            **(metadata or {})
        }

        # Store in ChromaDB
        self.entity_collection.upsert(
            ids=[entity_id],
            embeddings=[embedding],
            documents=[entity_description],
            metadatas=[meta]
        )

    async def compare_entity_descriptions(
        self,
        entity1_id: str,
        entity2_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Compare two specific entities for contradictions.

        Args:
            entity1_id: First entity ID
            entity2_id: Second entity ID
            db: Database session

        Returns:
            Comparison result with similarity score
        """
        # Fetch both entities
        result = await db.execute(
            select(Entity).where(Entity.id.in_([entity1_id, entity2_id]))
        )
        entities = result.scalars().all()

        if len(entities) != 2:
            return {
                "error": "One or both entities not found",
                "similarity_score": 0.0
            }

        entity1 = next((e for e in entities if e.id == entity1_id), None)
        entity2 = next((e for e in entities if e.id == entity2_id), None)

        # Generate embeddings
        embedding1 = self.embedder.embed(entity1.canonical_description or "")
        embedding2 = self.embedder.embed(entity2.canonical_description or "")

        # Compute similarity
        similarity = self.compute_similarity(embedding1, embedding2)

        return {
            "entity1_id": entity1_id,
            "entity1_name": entity1.name,
            "entity2_id": entity2_id,
            "entity2_name": entity2.name,
            "similarity_score": similarity,
            "are_similar": similarity >= self.threshold
        }

    async def find_contradictory_chunks(
        self,
        query_text: str,
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any], float]]:
        """
        Find pairs of chunks that might contradict each other.

        Args:
            query_text: Topic or entity to check
            top_k: Number of chunks to retrieve

        Returns:
            List of (chunk1, chunk2, similarity_score) tuples
        """
        # Generate embedding for query
        query_embedding = self.embedder.embed(query_text)

        # Get chunks collection
        chunks_collection = self.chroma_client.get_collection("worldforge_chunks")

        # Query for similar chunks
        results = chunks_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "documents", "distances", "embeddings"]
        )

        # Compare chunks pairwise for contradictions
        contradictions = []
        if results["ids"][0]:
            chunks = []
            for idx in range(len(results["ids"][0])):
                chunks.append({
                    "id": results["ids"][0][idx],
                    "text": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "embedding": results["embeddings"][0][idx] if results.get("embeddings") else None
                })

            # Compare each pair
            for i in range(len(chunks)):
                for j in range(i + 1, len(chunks)):
                    chunk1 = chunks[i]
                    chunk2 = chunks[j]

                    # Skip if from same document (likely not contradictory)
                    if chunk1["metadata"].get("document_id") == chunk2["metadata"].get("document_id"):
                        continue

                    # Compute similarity
                    if chunk1["embedding"] and chunk2["embedding"]:
                        similarity = self.compute_similarity(
                            chunk1["embedding"],
                            chunk2["embedding"]
                        )

                        # High similarity might indicate contradiction if content differs
                        if similarity >= self.threshold:
                            contradictions.append((chunk1, chunk2, similarity))

        return contradictions

    def batch_compute_similarities(
        self,
        embeddings: List[List[float]]
    ) -> np.ndarray:
        """
        Compute pairwise similarities for a batch of embeddings.

        Args:
            embeddings: List of embedding vectors

        Returns:
            Matrix of pairwise similarities
        """
        # Convert to numpy array
        embeddings_array = np.array(embeddings)

        # Compute pairwise cosine similarity
        similarity_matrix = cosine_similarity(embeddings_array)

        return similarity_matrix
