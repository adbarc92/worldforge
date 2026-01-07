"""
API routes for conflict and inconsistency detection.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from backend.app.database.connection import get_db
from backend.app.database.models import Conflict
from backend.app.api.schemas import (
    ConflictResponse,
    ConflictListResponse,
    ConflictDetectionRequest,
    ConflictDetectionResponse,
    ConflictResolutionRequest,
    APIResponse
)
from backend.app.consistency.detector import InconsistencyDetector


router = APIRouter()

# Initialize detector (singleton)
detector = None


def get_detector() -> InconsistencyDetector:
    """Get or create inconsistency detector instance."""
    global detector
    if detector is None:
        detector = InconsistencyDetector()
    return detector


@router.get("/", response_model=ConflictListResponse)
async def list_conflicts(
    status: Optional[str] = Query(None, description="Filter by status (resolved/unresolved)"),
    severity: Optional[str] = Query(None, description="Filter by severity (high/medium/low)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all detected conflicts with optional filters.

    Args:
        status: Filter by resolution status
        severity: Filter by severity level
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session

    Returns:
        List of conflicts with summary statistics
    """
    # Build query
    query = select(Conflict)

    if status:
        query = query.where(Conflict.status == status)
    if severity:
        query = query.where(Conflict.severity == severity)

    # Get total count
    count_query = select(func.count()).select_from(Conflict)
    if status:
        count_query = count_query.where(Conflict.status == status)
    if severity:
        count_query = count_query.where(Conflict.severity == severity)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Conflict.created_at.desc())
    result = await db.execute(query)
    conflicts = result.scalars().all()

    # Get statistics
    severity_stats = {}
    for sev in ["high", "medium", "low"]:
        sev_query = select(func.count()).select_from(Conflict).where(Conflict.severity == sev)
        sev_result = await db.execute(sev_query)
        severity_stats[sev] = sev_result.scalar()

    status_stats = {}
    for stat in ["resolved", "unresolved"]:
        stat_query = select(func.count()).select_from(Conflict).where(Conflict.status == stat)
        stat_result = await db.execute(stat_query)
        status_stats[stat] = stat_result.scalar()

    return ConflictListResponse(
        conflicts=[ConflictResponse.model_validate(c) for c in conflicts],
        total=total or 0,
        by_severity=severity_stats,
        by_status=status_stats
    )


@router.get("/{conflict_id}", response_model=ConflictResponse)
async def get_conflict(
    conflict_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific conflict.

    Args:
        conflict_id: Conflict ID
        db: Database session

    Returns:
        Conflict details

    Raises:
        HTTPException: If conflict not found
    """
    result = await db.execute(
        select(Conflict).where(Conflict.id == conflict_id)
    )
    conflict = result.scalar_one_or_none()

    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    return ConflictResponse.model_validate(conflict)


@router.post("/detect", response_model=ConflictDetectionResponse)
async def detect_conflicts(
    request: ConflictDetectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger conflict detection.

    Can detect conflicts for:
    - A specific entity
    - All entities from a document
    - A proposed content item
    - Full consistency check across all entities

    Args:
        request: Detection parameters
        db: Database session

    Returns:
        Detected conflicts

    Raises:
        HTTPException: If detection fails
    """
    try:
        detector_instance = get_detector()
        conflicts = []

        # Detect conflicts based on request type
        if request.entity_id:
            # Check specific entity
            detected = await detector_instance.detect_contradictions_for_entity(
                entity_id=request.entity_id,
                db=db
            )
            # Store conflicts
            for conflict_data in detected:
                stored = await detector_instance.store_conflict(conflict_data, db)
                conflicts.append(stored)

        elif request.document_id:
            # Check all proposed content from document
            detected = await detector_instance.check_document_for_conflicts(
                document_id=request.document_id,
                db=db
            )
            for conflict_data in detected:
                stored = await detector_instance.store_conflict(conflict_data, db)
                conflicts.append(stored)

        elif request.proposed_content_id:
            # Check proposed content
            detected = await detector_instance.detect_contradictions_for_proposed_content(
                proposed_content_id=request.proposed_content_id,
                db=db
            )
            for conflict_data in detected:
                stored = await detector_instance.store_conflict(conflict_data, db)
                conflicts.append(stored)

        elif request.run_full_check:
            # Run full consistency check
            result = await detector_instance.run_full_consistency_check(db=db)
            # Conflicts are already stored
            # Fetch them
            recent_query = select(Conflict).order_by(Conflict.created_at.desc()).limit(100)
            recent_result = await db.execute(recent_query)
            conflicts = recent_result.scalars().all()

            return ConflictDetectionResponse(
                conflicts_detected=result["conflicts_detected"],
                conflicts=[ConflictResponse.model_validate(c) for c in conflicts],
                metadata=result
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Must specify entity_id, document_id, proposed_content_id, or run_full_check"
            )

        return ConflictDetectionResponse(
            conflicts_detected=len(conflicts),
            conflicts=[ConflictResponse.model_validate(c) for c in conflicts],
            metadata={
                "entity_id": request.entity_id,
                "document_id": request.document_id,
                "proposed_content_id": request.proposed_content_id
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conflict detection failed: {str(e)}"
        )


@router.put("/{conflict_id}/resolve", response_model=ConflictResponse)
async def resolve_conflict(
    conflict_id: str,
    request: ConflictResolutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a conflict as resolved.

    Args:
        conflict_id: Conflict ID
        request: Resolution details
        db: Database session

    Returns:
        Updated conflict

    Raises:
        HTTPException: If conflict not found or resolution fails
    """
    try:
        detector_instance = get_detector()

        resolved = await detector_instance.resolve_conflict(
            conflict_id=conflict_id,
            resolution=request.resolution,
            db=db
        )

        if not resolved:
            raise HTTPException(status_code=404, detail="Conflict not found")

        return ConflictResponse.model_validate(resolved)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve conflict: {str(e)}"
        )


@router.delete("/{conflict_id}", response_model=APIResponse)
async def delete_conflict(
    conflict_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a conflict record.

    Use this for false positives or conflicts that are no longer relevant.

    Args:
        conflict_id: Conflict ID
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If conflict not found
    """
    result = await db.execute(
        select(Conflict).where(Conflict.id == conflict_id)
    )
    conflict = result.scalar_one_or_none()

    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    await db.delete(conflict)
    await db.commit()

    return APIResponse(
        success=True,
        data={"conflict_id": conflict_id},
        metadata={"action": "deleted"}
    )


@router.get("/stats/summary", response_model=APIResponse)
async def get_conflict_stats(db: AsyncSession = Depends(get_db)):
    """
    Get summary statistics about conflicts.

    Args:
        db: Database session

    Returns:
        Conflict statistics
    """
    # Total conflicts
    total_query = select(func.count()).select_from(Conflict)
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    # By severity
    by_severity = {}
    for severity in ["high", "medium", "low"]:
        sev_query = select(func.count()).select_from(Conflict).where(Conflict.severity == severity)
        sev_result = await db.execute(sev_query)
        by_severity[severity] = sev_result.scalar()

    # By status
    by_status = {}
    for status in ["resolved", "unresolved"]:
        status_query = select(func.count()).select_from(Conflict).where(Conflict.status == status)
        status_result = await db.execute(status_query)
        by_status[status] = status_result.scalar()

    # Recent conflicts (last 7 days)
    # For SQLite, we'll use a simple approach
    recent_query = select(func.count()).select_from(Conflict).limit(100)
    recent_result = await db.execute(recent_query)
    recent_count = min(total or 0, 100)

    stats = {
        "total_conflicts": total or 0,
        "by_severity": by_severity,
        "by_status": by_status,
        "recent_conflicts": recent_count,
        "resolution_rate": (by_status.get("resolved", 0) / total * 100) if total else 0
    }

    return APIResponse(
        success=True,
        data=stats
    )
