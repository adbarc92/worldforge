"""
Approval workflow for moving proposed content to canonical tables.
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database.models import ProposedContent, Entity, Relationship
from backend.app.consistency.similarity import SimilarityEngine


class ApprovalWorkflow:
    """
    Handles approval and rejection of proposed content.

    Workflow:
    1. Approve → Move to canonical tables + store embedding
    2. Reject → Mark as rejected
    3. Edit → Update content, then approve
    """

    def __init__(self):
        """Initialize approval workflow."""
        self.similarity_engine = SimilarityEngine()

    async def approve_entity(
        self,
        proposed_content_id: str,
        db: AsyncSession,
        reviewed_by: Optional[str] = None
    ) -> Entity:
        """
        Approve a proposed entity and move to canonical Entity table.

        Args:
            proposed_content_id: ProposedContent ID
            db: Database session
            reviewed_by: User who approved

        Returns:
            Created Entity object

        Raises:
            ValueError: If content not found or not an entity
        """
        # Get proposed content
        result = await db.execute(
            select(ProposedContent).where(ProposedContent.id == proposed_content_id)
        )
        proposed = result.scalar_one_or_none()

        if not proposed:
            raise ValueError("Proposed content not found")

        if proposed.type != "entity":
            raise ValueError(f"Content is not an entity (type: {proposed.type})")

        # Extract entity data
        content = proposed.content
        entity_name = content.get("name", "")
        entity_type = content.get("type", "")
        entity_description = content.get("description", "")
        confidence = content.get("confidence", 0.5)

        # Create canonical entity
        entity = Entity(
            id=str(uuid.uuid4()),
            name=entity_name,
            type=entity_type,
            canonical_description=entity_description,
            confidence_score=confidence,
            metadata={
                "source_proposed_id": proposed_content_id,
                "source_document_id": content.get("source_document_id"),
                "approved_by": reviewed_by,
                "approved_at": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )

        db.add(entity)

        # Update proposed content status
        proposed.review_status = "approved"
        proposed.reviewed_by = reviewed_by
        proposed.reviewed_at = datetime.utcnow()

        # Store entity embedding for future similarity searches
        await self.similarity_engine.store_entity_embedding(
            entity_id=entity.id,
            entity_name=entity_name,
            entity_description=entity_description,
            entity_type=entity_type,
            metadata={
                "confidence": confidence,
                "source": "approved_content"
            }
        )

        await db.commit()
        await db.refresh(entity)

        return entity

    async def approve_relationship(
        self,
        proposed_content_id: str,
        db: AsyncSession,
        reviewed_by: Optional[str] = None
    ) -> Relationship:
        """
        Approve a proposed relationship and move to canonical Relationship table.

        Args:
            proposed_content_id: ProposedContent ID
            db: Database session
            reviewed_by: User who approved

        Returns:
            Created Relationship object

        Raises:
            ValueError: If content not found or not a relationship
        """
        # Get proposed content
        result = await db.execute(
            select(ProposedContent).where(ProposedContent.id == proposed_content_id)
        )
        proposed = result.scalar_one_or_none()

        if not proposed:
            raise ValueError("Proposed content not found")

        if proposed.type != "relationship":
            raise ValueError(f"Content is not a relationship (type: {proposed.type})")

        # Extract relationship data
        content = proposed.content
        source_entity_id = content.get("source_entity_id")
        target_entity_id = content.get("target_entity_id")
        relation_type = content.get("relation_type", "")
        evidence_doc_id = content.get("evidence_doc_id")
        confidence = content.get("confidence", 0.5)

        # Create canonical relationship
        relationship = Relationship(
            id=str(uuid.uuid4()),
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation_type=relation_type,
            evidence_doc_id=evidence_doc_id,
            confidence_score=confidence,
            metadata={
                "source_proposed_id": proposed_content_id,
                "approved_by": reviewed_by,
                "approved_at": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )

        db.add(relationship)

        # Update proposed content status
        proposed.review_status = "approved"
        proposed.reviewed_by = reviewed_by
        proposed.reviewed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(relationship)

        return relationship

    async def reject(
        self,
        proposed_content_id: str,
        db: AsyncSession,
        reason: Optional[str] = None,
        reviewed_by: Optional[str] = None
    ) -> ProposedContent:
        """
        Reject proposed content.

        Args:
            proposed_content_id: ProposedContent ID
            db: Database session
            reason: Reason for rejection
            reviewed_by: User who rejected

        Returns:
            Updated ProposedContent object

        Raises:
            ValueError: If content not found
        """
        # Get proposed content
        result = await db.execute(
            select(ProposedContent).where(ProposedContent.id == proposed_content_id)
        )
        proposed = result.scalar_one_or_none()

        if not proposed:
            raise ValueError("Proposed content not found")

        # Update status
        proposed.review_status = "rejected"
        proposed.reviewed_by = reviewed_by
        proposed.reviewed_at = datetime.utcnow()

        # Store rejection reason in metadata
        if reason:
            if not proposed.generation_metadata:
                proposed.generation_metadata = {}
            proposed.generation_metadata["rejection_reason"] = reason

        await db.commit()
        await db.refresh(proposed)

        return proposed

    async def edit_and_approve(
        self,
        proposed_content_id: str,
        updated_content: Dict[str, Any],
        db: AsyncSession,
        reviewed_by: Optional[str] = None
    ) -> Any:
        """
        Edit proposed content and then approve it.

        Args:
            proposed_content_id: ProposedContent ID
            updated_content: Updated content data
            db: Database session
            reviewed_by: User who approved

        Returns:
            Created canonical entity or relationship

        Raises:
            ValueError: If content not found
        """
        # Get proposed content
        result = await db.execute(
            select(ProposedContent).where(ProposedContent.id == proposed_content_id)
        )
        proposed = result.scalar_one_or_none()

        if not proposed:
            raise ValueError("Proposed content not found")

        # Update content
        proposed.content = updated_content

        # Mark as edited
        if not proposed.generation_metadata:
            proposed.generation_metadata = {}
        proposed.generation_metadata["edited"] = True
        proposed.generation_metadata["edited_by"] = reviewed_by
        proposed.generation_metadata["edited_at"] = datetime.utcnow().isoformat()

        await db.commit()

        # Now approve
        if proposed.type == "entity":
            return await self.approve_entity(proposed_content_id, db, reviewed_by)
        elif proposed.type == "relationship":
            return await self.approve_relationship(proposed_content_id, db, reviewed_by)
        else:
            raise ValueError(f"Unknown content type: {proposed.type}")

    async def bulk_approve(
        self,
        proposed_content_ids: list[str],
        db: AsyncSession,
        reviewed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk approve multiple proposed items.

        Args:
            proposed_content_ids: List of ProposedContent IDs
            db: Database session
            reviewed_by: User who approved

        Returns:
            Summary of bulk approval
        """
        approved_entities = []
        approved_relationships = []
        errors = []

        for content_id in proposed_content_ids:
            try:
                # Get proposed content
                result = await db.execute(
                    select(ProposedContent).where(ProposedContent.id == content_id)
                )
                proposed = result.scalar_one_or_none()

                if not proposed:
                    errors.append({
                        "id": content_id,
                        "error": "Not found"
                    })
                    continue

                # Approve based on type
                if proposed.type == "entity":
                    entity = await self.approve_entity(content_id, db, reviewed_by)
                    approved_entities.append(entity)
                elif proposed.type == "relationship":
                    relationship = await self.approve_relationship(content_id, db, reviewed_by)
                    approved_relationships.append(relationship)
                else:
                    errors.append({
                        "id": content_id,
                        "error": f"Unknown type: {proposed.type}"
                    })

            except Exception as e:
                errors.append({
                    "id": content_id,
                    "error": str(e)
                })

        return {
            "total_requested": len(proposed_content_ids),
            "approved_entities": len(approved_entities),
            "approved_relationships": len(approved_relationships),
            "errors": len(errors),
            "error_details": errors
        }

    async def approve_with_merge(
        self,
        proposed_content_id: str,
        merge_with_entity_id: str,
        db: AsyncSession,
        reviewed_by: Optional[str] = None
    ) -> Entity:
        """
        Approve by merging with existing entity.

        Use this when a proposed entity is a duplicate but has additional info.

        Args:
            proposed_content_id: ProposedContent ID
            merge_with_entity_id: Existing Entity ID to merge into
            db: Database session
            reviewed_by: User who approved

        Returns:
            Updated Entity object

        Raises:
            ValueError: If content or entity not found
        """
        # Get proposed content
        result = await db.execute(
            select(ProposedContent).where(ProposedContent.id == proposed_content_id)
        )
        proposed = result.scalar_one_or_none()

        if not proposed:
            raise ValueError("Proposed content not found")

        # Get existing entity
        entity_result = await db.execute(
            select(Entity).where(Entity.id == merge_with_entity_id)
        )
        entity = entity_result.scalar_one_or_none()

        if not entity:
            raise ValueError("Entity to merge with not found")

        # Extract new info
        content = proposed.content
        new_description = content.get("description", "")

        # Merge descriptions (simple concatenation - can be enhanced)
        if new_description and new_description not in (entity.canonical_description or ""):
            merged_description = f"{entity.canonical_description}\n\n{new_description}"
            entity.canonical_description = merged_description

        # Update metadata
        if not entity.metadata:
            entity.metadata = {}
        entity.metadata["merged_from"] = entity.metadata.get("merged_from", [])
        entity.metadata["merged_from"].append({
            "proposed_id": proposed_content_id,
            "merged_by": reviewed_by,
            "merged_at": datetime.utcnow().isoformat()
        })

        # Update proposed content status
        proposed.review_status = "approved"
        proposed.reviewed_by = reviewed_by
        proposed.reviewed_at = datetime.utcnow()
        if not proposed.generation_metadata:
            proposed.generation_metadata = {}
        proposed.generation_metadata["merged_into"] = merge_with_entity_id

        await db.commit()
        await db.refresh(entity)

        return entity
