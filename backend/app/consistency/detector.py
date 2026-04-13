"""
Inconsistency and contradiction detection using LLMs and similarity.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database.models import Entity, ProposedContent, Conflict
from backend.app.consistency.similarity import SimilarityEngine
from backend.app.llm.provider import get_llm_provider
from backend.app.llm.prompts import CONTRADICTION_DETECTION_PROMPT


class InconsistencyDetector:
    """
    Detects contradictions and inconsistencies in worldbuilding content.

    Workflow:
    1. Find semantically similar entities/content
    2. Use LLM to analyze for contradictions
    3. Assign severity scores
    4. Store in conflicts table
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize inconsistency detector.

        Args:
            similarity_threshold: Minimum similarity to consider for comparison
        """
        self.similarity_engine = SimilarityEngine(similarity_threshold)
        self.llm_provider = get_llm_provider()

    async def detect_contradictions_for_entity(
        self,
        entity_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions for a specific entity.

        Args:
            entity_id: Entity ID to check
            db: Database session

        Returns:
            List of detected conflicts
        """
        # Fetch entity
        result = await db.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        entity = result.scalar_one_or_none()

        if not entity:
            return []

        # Find similar entities
        similar_entities = await self.similarity_engine.find_similar_entities(
            entity_description=entity.canonical_description or "",
            entity_type=entity.type,
            db=db,
            top_k=10,
            include_proposed=False
        )

        # Analyze each similar entity for contradictions
        conflicts = []
        for similar in similar_entities:
            # Skip self
            if similar["entity_id"] == entity_id:
                continue

            # Analyze for contradiction
            conflict = await self._analyze_entity_pair(
                entity1_id=entity_id,
                entity2_id=similar["entity_id"],
                similarity_score=similar["similarity_score"],
                db=db
            )

            if conflict:
                conflicts.append(conflict)

        return conflicts

    async def detect_contradictions_for_proposed_content(
        self,
        proposed_content_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions for newly proposed content.

        This is run before content is approved to identify conflicts with
        existing canon.

        Args:
            proposed_content_id: ProposedContent ID
            db: Database session

        Returns:
            List of detected conflicts
        """
        # Fetch proposed content
        result = await db.execute(
            select(ProposedContent).where(ProposedContent.id == proposed_content_id)
        )
        proposed = result.scalar_one_or_none()

        if not proposed:
            return []

        # Extract entity info from content
        content = proposed.content
        entity_name = content.get("name", "")
        entity_description = content.get("description", "")
        entity_type = content.get("type", "")

        # Find similar entities in canon
        similar_entities = await self.similarity_engine.find_similar_entities(
            entity_description=entity_description,
            entity_type=entity_type,
            db=db,
            top_k=5,
            include_proposed=False  # Only check against canon
        )

        # Analyze for contradictions
        conflicts = []
        for similar in similar_entities:
            # Get canonical entity
            entity_result = await db.execute(
                select(Entity).where(Entity.id == similar["entity_id"])
            )
            canonical_entity = entity_result.scalar_one_or_none()

            if not canonical_entity:
                continue

            # Analyze contradiction
            is_contradiction, analysis = await self._llm_detect_contradiction(
                name1=entity_name,
                description1=entity_description,
                name2=canonical_entity.name,
                description2=canonical_entity.canonical_description or ""
            )

            if is_contradiction:
                conflict_data = {
                    "proposed_content_id": proposed_content_id,
                    "canonical_entity_id": canonical_entity.id,
                    "similarity_score": similar["similarity_score"],
                    "conflict_type": analysis.get("type", "description_mismatch"),
                    "severity": analysis.get("severity", "medium"),
                    "description": analysis.get("description", ""),
                    "evidence_proposed": entity_description[:500],
                    "evidence_canonical": canonical_entity.canonical_description[:500] if canonical_entity.canonical_description else ""
                }
                conflicts.append(conflict_data)

        return conflicts

    async def _analyze_entity_pair(
        self,
        entity1_id: str,
        entity2_id: str,
        similarity_score: float,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a pair of entities for contradictions.

        Args:
            entity1_id: First entity ID
            entity2_id: Second entity ID
            similarity_score: Similarity score between entities
            db: Database session

        Returns:
            Conflict data if contradiction found, None otherwise
        """
        # Fetch both entities
        result = await db.execute(
            select(Entity).where(Entity.id.in_([entity1_id, entity2_id]))
        )
        entities = result.scalars().all()

        if len(entities) != 2:
            return None

        entity1 = next((e for e in entities if e.id == entity1_id), None)
        entity2 = next((e for e in entities if e.id == entity2_id), None)

        # Use LLM to detect contradiction
        is_contradiction, analysis = await self._llm_detect_contradiction(
            name1=entity1.name,
            description1=entity1.canonical_description or "",
            name2=entity2.name,
            description2=entity2.canonical_description or ""
        )

        if is_contradiction:
            return {
                "entity1_id": entity1_id,
                "entity2_id": entity2_id,
                "similarity_score": similarity_score,
                "conflict_type": analysis.get("type", "description_mismatch"),
                "severity": analysis.get("severity", "medium"),
                "description": analysis.get("description", ""),
                "evidence1": entity1.canonical_description[:500] if entity1.canonical_description else "",
                "evidence2": entity2.canonical_description[:500] if entity2.canonical_description else ""
            }

        return None

    async def _llm_detect_contradiction(
        self,
        name1: str,
        description1: str,
        name2: str,
        description2: str
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Use LLM to detect contradictions between two entity descriptions.

        Args:
            name1: First entity name
            description1: First entity description
            name2: Second entity name
            description2: Second entity description

        Returns:
            Tuple of (is_contradiction, analysis_details)
        """
        prompt = CONTRADICTION_DETECTION_PROMPT.format(
            name1=name1,
            description1=description1,
            name2=name2,
            description2=description2
        )

        try:
            # Use structured output if available
            schema = {
                "type": "object",
                "properties": {
                    "is_contradiction": {"type": "boolean"},
                    "type": {"type": "string"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "description": {"type": "string"},
                    "explanation": {"type": "string"}
                },
                "required": ["is_contradiction", "severity", "description"]
            }

            result = await self.llm_provider.generate_structured(
                prompt=prompt,
                schema=schema,
                max_tokens=500,
                temperature=0.1  # Low temperature for consistency
            )

            is_contradiction = result.get("is_contradiction", False)
            return is_contradiction, result

        except Exception:
            # Fallback to unstructured response
            response = await self.llm_provider.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1
            )

            # Simple parsing
            is_contradiction = "contradiction" in response.lower() or "conflict" in response.lower()
            analysis = {
                "type": "unknown",
                "severity": "medium",
                "description": response[:200],
                "explanation": response
            }

            return is_contradiction, analysis

    async def store_conflict(
        self,
        conflict_data: Dict[str, Any],
        db: AsyncSession
    ) -> Conflict:
        """
        Store a detected conflict in the database.

        Args:
            conflict_data: Conflict information
            db: Database session

        Returns:
            Created Conflict object
        """
        conflict = Conflict(
            id=str(uuid.uuid4()),
            entity_id_1=conflict_data.get("entity1_id"),
            entity_id_2=conflict_data.get("entity2_id"),
            conflict_type=conflict_data.get("conflict_type", "description_mismatch"),
            severity=conflict_data.get("severity", "medium"),
            description=conflict_data.get("description", ""),
            evidence_1=conflict_data.get("evidence1", ""),
            evidence_2=conflict_data.get("evidence2", ""),
            status="unresolved",
            created_at=datetime.utcnow()
        )

        db.add(conflict)
        await db.commit()
        await db.refresh(conflict)

        return conflict

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        db: AsyncSession
    ) -> Optional[Conflict]:
        """
        Mark a conflict as resolved.

        Args:
            conflict_id: Conflict ID
            resolution: Resolution description
            db: Database session

        Returns:
            Updated Conflict object
        """
        result = await db.execute(
            select(Conflict).where(Conflict.id == conflict_id)
        )
        conflict = result.scalar_one_or_none()

        if not conflict:
            return None

        conflict.status = "resolved"
        conflict.resolution = resolution
        conflict.resolved_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conflict)

        return conflict

    async def run_full_consistency_check(
        self,
        db: AsyncSession,
        entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a full consistency check across all entities.

        Args:
            db: Database session
            entity_type: Optional entity type filter

        Returns:
            Summary of detected conflicts
        """
        # Get all canonical entities
        query = select(Entity)
        if entity_type:
            query = query.where(Entity.type == entity_type)

        result = await db.execute(query)
        entities = result.scalars().all()

        # Track conflicts
        all_conflicts = []
        checked_pairs = set()

        # Check each entity
        for entity in entities:
            # Find similar entities
            similar_entities = await self.similarity_engine.find_similar_entities(
                entity_description=entity.canonical_description or "",
                entity_type=entity.type,
                db=db,
                top_k=5,
                include_proposed=False
            )

            # Check each similar entity
            for similar in similar_entities:
                similar_id = similar["entity_id"]

                # Skip self and already checked pairs
                if similar_id == entity.id:
                    continue

                pair_key = tuple(sorted([entity.id, similar_id]))
                if pair_key in checked_pairs:
                    continue

                checked_pairs.add(pair_key)

                # Analyze for contradiction
                conflict = await self._analyze_entity_pair(
                    entity1_id=entity.id,
                    entity2_id=similar_id,
                    similarity_score=similar["similarity_score"],
                    db=db
                )

                if conflict:
                    # Store conflict
                    stored_conflict = await self.store_conflict(conflict, db)
                    all_conflicts.append(stored_conflict)

        return {
            "total_entities_checked": len(entities),
            "total_pairs_checked": len(checked_pairs),
            "conflicts_detected": len(all_conflicts),
            "conflicts_by_severity": {
                "high": len([c for c in all_conflicts if c.severity == "high"]),
                "medium": len([c for c in all_conflicts if c.severity == "medium"]),
                "low": len([c for c in all_conflicts if c.severity == "low"])
            }
        }

    async def check_document_for_conflicts(
        self,
        document_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Check all proposed entities from a document for conflicts.

        Args:
            document_id: Document ID
            db: Database session

        Returns:
            List of detected conflicts
        """
        # Get all proposed content from this document
        result = await db.execute(
            select(ProposedContent)
            .where(ProposedContent.content["source_document_id"].as_string() == document_id)
            .where(ProposedContent.review_status == "pending")
        )
        proposed_items = result.scalars().all()

        # Check each for conflicts
        all_conflicts = []
        for item in proposed_items:
            conflicts = await self.detect_contradictions_for_proposed_content(
                proposed_content_id=item.id,
                db=db
            )
            all_conflicts.extend(conflicts)

        return all_conflicts
