"""
API routes for review queue and approval workflow.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.app.database.connection import get_db
from backend.app.api.schemas import (
    ReviewQueueResponse,
    ReviewQueueStatsResponse,
    ApprovalRequest,
    RejectionRequest,
    EditAndApproveRequest,
    BulkApprovalRequest,
    BulkApprovalResponse,
    MergeApprovalRequest,
    ProposedContentResponse,
    EntityResponse,
    RelationshipResponse,
    APIResponse
)
from backend.app.review.queue import ReviewQueue
from backend.app.review.approval import ApprovalWorkflow


router = APIRouter()

# Initialize services (singletons)
review_queue = None
approval_workflow = None


def get_review_queue() -> ReviewQueue:
    """Get or create review queue instance."""
    global review_queue
    if review_queue is None:
        review_queue = ReviewQueue()
    return review_queue


def get_approval_workflow() -> ApprovalWorkflow:
    """Get or create approval workflow instance."""
    global approval_workflow
    if approval_workflow is None:
        approval_workflow = ApprovalWorkflow()
    return approval_workflow


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_queue(
    status: str = Query("pending", description="Filter by status"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    sort_by: str = Query("priority", description="Sort by: priority, date, confidence"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get review queue with filtering and sorting.

    Args:
        status: Review status (pending/approved/rejected)
        content_type: Content type filter (entity/relationship)
        sort_by: Sort order
        skip: Pagination offset
        limit: Max items
        db: Database session

    Returns:
        Review queue items with metadata
    """
    try:
        queue = get_review_queue()
        result = await queue.get_queue(
            db=db,
            status=status,
            content_type=content_type,
            sort_by=sort_by,
            skip=skip,
            limit=limit
        )

        return ReviewQueueResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch review queue: {str(e)}"
        )


@router.get("/queue/stats", response_model=ReviewQueueStatsResponse)
async def get_queue_stats(db: AsyncSession = Depends(get_db)):
    """
    Get review queue statistics.

    Args:
        db: Database session

    Returns:
        Queue statistics
    """
    try:
        queue = get_review_queue()
        stats = await queue.get_queue_statistics(db=db)

        return ReviewQueueStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch queue stats: {str(e)}"
        )


@router.get("/queue/high-priority", response_model=APIResponse)
async def get_high_priority(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get high-priority items that need immediate review.

    Args:
        limit: Max items to return
        db: Database session

    Returns:
        High-priority review items
    """
    try:
        queue = get_review_queue()
        items = await queue.get_high_priority_items(db=db, limit=limit)

        return APIResponse(
            success=True,
            data={"items": items, "count": len(items)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch high-priority items: {str(e)}"
        )


@router.post("/{proposed_content_id}/approve")
async def approve_item(
    proposed_content_id: str,
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a proposed content item.

    Moves the item from proposed_content to the canonical table
    (Entity or Relationship).

    Args:
        proposed_content_id: ProposedContent ID
        request: Approval request
        db: Database session

    Returns:
        Created canonical entity or relationship

    Raises:
        HTTPException: If approval fails
    """
    try:
        workflow = get_approval_workflow()

        # Try as entity first
        try:
            entity = await workflow.approve_entity(
                proposed_content_id=proposed_content_id,
                db=db,
                reviewed_by=request.reviewed_by
            )
            return {"type": "entity", "entity": EntityResponse.model_validate(entity)}

        except ValueError as e:
            if "not an entity" in str(e):
                # Try as relationship
                relationship = await workflow.approve_relationship(
                    proposed_content_id=proposed_content_id,
                    db=db,
                    reviewed_by=request.reviewed_by
                )
                return {
                    "type": "relationship",
                    "relationship": RelationshipResponse.model_validate(relationship)
                }
            else:
                raise

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Approval failed: {str(e)}"
        )


@router.post("/{proposed_content_id}/reject", response_model=ProposedContentResponse)
async def reject_item(
    proposed_content_id: str,
    request: RejectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a proposed content item.

    Args:
        proposed_content_id: ProposedContent ID
        request: Rejection request with reason
        db: Database session

    Returns:
        Updated proposed content

    Raises:
        HTTPException: If rejection fails
    """
    try:
        workflow = get_approval_workflow()

        rejected = await workflow.reject(
            proposed_content_id=proposed_content_id,
            db=db,
            reason=request.reason,
            reviewed_by=request.reviewed_by
        )

        return ProposedContentResponse.model_validate(rejected)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Rejection failed: {str(e)}"
        )


@router.put("/{proposed_content_id}/edit")
async def edit_and_approve(
    proposed_content_id: str,
    request: EditAndApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Edit proposed content and then approve it.

    Args:
        proposed_content_id: ProposedContent ID
        request: Edit and approval request
        db: Database session

    Returns:
        Created canonical entity or relationship

    Raises:
        HTTPException: If operation fails
    """
    try:
        workflow = get_approval_workflow()

        result = await workflow.edit_and_approve(
            proposed_content_id=proposed_content_id,
            updated_content=request.updated_content,
            db=db,
            reviewed_by=request.reviewed_by
        )

        # Check result type
        if hasattr(result, 'name'):  # Entity
            return {"type": "entity", "entity": EntityResponse.model_validate(result)}
        else:  # Relationship
            return {"type": "relationship", "relationship": RelationshipResponse.model_validate(result)}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Edit and approval failed: {str(e)}"
        )


@router.post("/bulk-approve", response_model=BulkApprovalResponse)
async def bulk_approve(
    request: BulkApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk approve multiple proposed items.

    Args:
        request: Bulk approval request
        db: Database session

    Returns:
        Bulk approval results

    Raises:
        HTTPException: If operation fails
    """
    try:
        workflow = get_approval_workflow()

        result = await workflow.bulk_approve(
            proposed_content_ids=request.item_ids,
            db=db,
            reviewed_by=request.reviewed_by
        )

        return BulkApprovalResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bulk approval failed: {str(e)}"
        )


@router.post("/{proposed_content_id}/approve-merge", response_model=EntityResponse)
async def approve_with_merge(
    proposed_content_id: str,
    request: MergeApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve by merging with an existing entity.

    Use when a proposed entity is a duplicate but has additional info.

    Args:
        proposed_content_id: ProposedContent ID
        request: Merge approval request
        db: Database session

    Returns:
        Updated entity

    Raises:
        HTTPException: If operation fails
    """
    try:
        workflow = get_approval_workflow()

        entity = await workflow.approve_with_merge(
            proposed_content_id=proposed_content_id,
            merge_with_entity_id=request.merge_with_entity_id,
            db=db,
            reviewed_by=request.reviewed_by
        )

        return EntityResponse.model_validate(entity)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Merge approval failed: {str(e)}"
        )


@router.get("/document/{document_id}/proposed", response_model=APIResponse)
async def get_proposed_by_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all proposed items from a specific document.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        List of proposed items

    Raises:
        HTTPException: If operation fails
    """
    try:
        queue = get_review_queue()

        items = await queue.get_items_by_document(
            db=db,
            document_id=document_id
        )

        return APIResponse(
            success=True,
            data={
                "items": [ProposedContentResponse.model_validate(item) for item in items],
                "count": len(items)
            },
            metadata={"document_id": document_id}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch proposed items: {str(e)}"
        )
