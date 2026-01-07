"""
Review queue management for proposed content.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime

from backend.app.database.models import ProposedContent, Conflict


class ReviewQueue:
    """
    Manages the review queue for AI-proposed content.

    Features:
    - Fetch pending items sorted by priority
    - Filter by type, confidence score
    - Group by document or entity type
    - Priority scoring based on confidence and conflicts
    """

    def __init__(self):
        """Initialize review queue manager."""
        pass

    async def get_queue(
        self,
        db: AsyncSession,
        status: str = "pending",
        content_type: Optional[str] = None,
        sort_by: str = "priority",
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get review queue with optional filters and sorting.

        Args:
            db: Database session
            status: Review status filter (pending/approved/rejected)
            content_type: Filter by content type (entity/relationship)
            sort_by: Sort order (priority/date/confidence)
            skip: Pagination offset
            limit: Max items to return

        Returns:
            Dict with items and metadata
        """
        # Build base query
        query = select(ProposedContent)

        # Apply filters
        if status:
            query = query.where(ProposedContent.review_status == status)

        if content_type:
            query = query.where(ProposedContent.type == content_type)

        # Count total
        count_query = select(func.count()).select_from(ProposedContent)
        if status:
            count_query = count_query.where(ProposedContent.review_status == status)
        if content_type:
            count_query = count_query.where(ProposedContent.type == content_type)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        if sort_by == "priority":
            # Priority = high coherence + has conflicts = needs review
            # For now, sort by coherence desc, then created_at desc
            query = query.order_by(
                ProposedContent.coherence_score.desc(),
                ProposedContent.created_at.desc()
            )
        elif sort_by == "date":
            query = query.order_by(ProposedContent.created_at.desc())
        elif sort_by == "confidence":
            query = query.order_by(ProposedContent.coherence_score.desc())
        else:
            # Default to date
            query = query.order_by(ProposedContent.created_at.desc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        items = result.scalars().all()

        # Enrich with conflict information
        enriched_items = []
        for item in items:
            # Check if item has conflicts
            conflict_query = select(Conflict).where(
                and_(
                    Conflict.status == "unresolved",
                    or_(
                        Conflict.entity_id_1 == item.id,
                        Conflict.entity_id_2 == item.id
                    )
                )
            )
            conflict_result = await db.execute(conflict_query)
            conflicts = conflict_result.scalars().all()

            enriched_items.append({
                "item": item,
                "conflicts": conflicts,
                "has_conflicts": len(conflicts) > 0,
                "conflict_count": len(conflicts),
                "priority_score": self._calculate_priority(item, conflicts)
            })

        # Re-sort by priority if requested
        if sort_by == "priority":
            enriched_items.sort(key=lambda x: x["priority_score"], reverse=True)

        return {
            "items": enriched_items,
            "total": total or 0,
            "skip": skip,
            "limit": limit,
            "filters": {
                "status": status,
                "content_type": content_type,
                "sort_by": sort_by
            }
        }

    def _calculate_priority(
        self,
        item: ProposedContent,
        conflicts: List[Conflict]
    ) -> float:
        """
        Calculate priority score for a review item.

        Higher score = higher priority for review.

        Args:
            item: ProposedContent item
            conflicts: Associated conflicts

        Returns:
            Priority score (0-1)
        """
        # Start with coherence score
        priority = item.coherence_score or 0.5

        # Boost if has conflicts
        if conflicts:
            # High severity conflicts get bigger boost
            high_severity = sum(1 for c in conflicts if c.severity == "high")
            medium_severity = sum(1 for c in conflicts if c.severity == "medium")

            conflict_boost = (high_severity * 0.3) + (medium_severity * 0.15)
            priority += conflict_boost

        # Cap at 1.0
        return min(priority, 1.0)

    async def get_queue_statistics(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get statistics about the review queue.

        Args:
            db: Database session

        Returns:
            Queue statistics
        """
        # Total by status
        status_counts = {}
        for status in ["pending", "approved", "rejected"]:
            count_query = select(func.count()).select_from(ProposedContent).where(
                ProposedContent.review_status == status
            )
            result = await db.execute(count_query)
            status_counts[status] = result.scalar() or 0

        # By content type (pending only)
        type_counts = {}
        type_query = select(
            ProposedContent.type,
            func.count(ProposedContent.id)
        ).where(
            ProposedContent.review_status == "pending"
        ).group_by(ProposedContent.type)

        type_result = await db.execute(type_query)
        for row in type_result:
            type_counts[row[0]] = row[1]

        # Items with conflicts
        conflict_query = select(func.count(ProposedContent.id.distinct())).select_from(
            ProposedContent
        ).join(
            Conflict,
            or_(
                Conflict.entity_id_1 == ProposedContent.id,
                Conflict.entity_id_2 == ProposedContent.id
            )
        ).where(
            and_(
                ProposedContent.review_status == "pending",
                Conflict.status == "unresolved"
            )
        )
        conflict_result = await db.execute(conflict_query)
        items_with_conflicts = conflict_result.scalar() or 0

        # Average confidence score
        avg_query = select(func.avg(ProposedContent.coherence_score)).where(
            ProposedContent.review_status == "pending"
        )
        avg_result = await db.execute(avg_query)
        avg_confidence = avg_result.scalar() or 0.0

        return {
            "by_status": status_counts,
            "by_type": type_counts,
            "items_with_conflicts": items_with_conflicts,
            "average_confidence": float(avg_confidence),
            "total_pending": status_counts.get("pending", 0),
            "needs_review": status_counts.get("pending", 0)
        }

    async def get_high_priority_items(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get high-priority items that need immediate review.

        Criteria:
        - Has conflicts
        - Low confidence score (<0.5)
        - High confidence but conflicting

        Args:
            db: Database session
            limit: Max items to return

        Returns:
            List of high-priority items
        """
        # Get pending items with conflicts
        query = select(ProposedContent).where(
            ProposedContent.review_status == "pending"
        ).order_by(
            ProposedContent.coherence_score.desc()
        ).limit(limit * 3)  # Get more to filter

        result = await db.execute(query)
        items = result.scalars().all()

        # Enrich and filter
        high_priority = []
        for item in items:
            # Get conflicts
            conflict_query = select(Conflict).where(
                and_(
                    Conflict.status == "unresolved",
                    or_(
                        Conflict.entity_id_1 == item.id,
                        Conflict.entity_id_2 == item.id
                    )
                )
            )
            conflict_result = await db.execute(conflict_query)
            conflicts = conflict_result.scalars().all()

            # Check priority criteria
            has_conflicts = len(conflicts) > 0
            low_confidence = (item.coherence_score or 0.5) < 0.5
            high_severity_conflict = any(c.severity == "high" for c in conflicts)

            if has_conflicts or low_confidence or high_severity_conflict:
                high_priority.append({
                    "item": item,
                    "conflicts": conflicts,
                    "reason": self._get_priority_reason(item, conflicts),
                    "priority_score": self._calculate_priority(item, conflicts)
                })

        # Sort by priority and limit
        high_priority.sort(key=lambda x: x["priority_score"], reverse=True)
        return high_priority[:limit]

    def _get_priority_reason(
        self,
        item: ProposedContent,
        conflicts: List[Conflict]
    ) -> str:
        """
        Get human-readable reason for high priority.

        Args:
            item: ProposedContent item
            conflicts: Associated conflicts

        Returns:
            Reason string
        """
        reasons = []

        if conflicts:
            high_severity = sum(1 for c in conflicts if c.severity == "high")
            if high_severity > 0:
                reasons.append(f"{high_severity} high-severity conflict(s)")
            else:
                reasons.append(f"{len(conflicts)} conflict(s)")

        if (item.coherence_score or 0.5) < 0.5:
            reasons.append(f"Low confidence ({item.coherence_score:.2f})")

        if not reasons:
            reasons.append("Pending review")

        return ", ".join(reasons)

    async def get_items_by_document(
        self,
        db: AsyncSession,
        document_id: str
    ) -> List[ProposedContent]:
        """
        Get all proposed items from a specific document.

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            List of proposed items
        """
        # Query proposed content where source_document_id matches
        query = select(ProposedContent).where(
            ProposedContent.content["source_document_id"].as_string() == document_id
        ).order_by(ProposedContent.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    async def bulk_action(
        self,
        db: AsyncSession,
        item_ids: List[str],
        action: str,
        reviewed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform bulk action on multiple review items.

        Args:
            db: Database session
            item_ids: List of ProposedContent IDs
            action: "approve" or "reject"
            reviewed_by: User who performed the action

        Returns:
            Summary of bulk action
        """
        if action not in ["approve", "reject"]:
            raise ValueError("Action must be 'approve' or 'reject'")

        # Get items
        query = select(ProposedContent).where(
            ProposedContent.id.in_(item_ids)
        )
        result = await db.execute(query)
        items = result.scalars().all()

        # Update status
        updated_count = 0
        for item in items:
            if item.review_status == "pending":
                item.review_status = "approved" if action == "approve" else "rejected"
                item.reviewed_by = reviewed_by
                item.reviewed_at = datetime.utcnow()
                updated_count += 1

        await db.commit()

        return {
            "action": action,
            "total_requested": len(item_ids),
            "updated": updated_count,
            "skipped": len(item_ids) - updated_count
        }
