from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contradiction import Contradiction


class ContradictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        project_id: str,
        chunk_a_id: str,
        chunk_b_id: str,
        document_a_id: str,
        document_b_id: str,
        document_a_title: str,
        document_b_title: str,
        chunk_a_text: str,
        chunk_b_text: str,
        explanation: str,
    ) -> Contradiction:
        contradiction = Contradiction(
            project_id=project_id,
            chunk_a_id=chunk_a_id,
            chunk_b_id=chunk_b_id,
            document_a_id=document_a_id,
            document_b_id=document_b_id,
            document_a_title=document_a_title,
            document_b_title=document_b_title,
            chunk_a_text=chunk_a_text,
            chunk_b_text=chunk_b_text,
            explanation=explanation,
        )
        self.session.add(contradiction)
        await self.session.commit()
        await self.session.refresh(contradiction)
        return contradiction

    async def pair_exists(self, chunk_a_id: str, chunk_b_id: str) -> bool:
        """Check if a contradiction between these two chunks already exists (in either order)."""
        stmt = (
            select(func.count())
            .select_from(Contradiction)
            .where(
                or_(
                    and_(
                        Contradiction.chunk_a_id == chunk_a_id,
                        Contradiction.chunk_b_id == chunk_b_id,
                    ),
                    and_(
                        Contradiction.chunk_a_id == chunk_b_id,
                        Contradiction.chunk_b_id == chunk_a_id,
                    ),
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def list(
        self, project_id: str, status: str | None = "open", skip: int = 0, limit: int = 50
    ) -> list[Contradiction]:
        stmt = select(Contradiction).where(Contradiction.project_id == project_id)
        if status:
            stmt = stmt.where(Contradiction.status == status)
        stmt = stmt.order_by(Contradiction.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, project_id: str, status: str | None = "open") -> int:
        stmt = (
            select(func.count())
            .select_from(Contradiction)
            .where(Contradiction.project_id == project_id)
        )
        if status:
            stmt = stmt.where(Contradiction.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get(self, contradiction_id: str) -> Contradiction | None:
        result = await self.session.execute(
            select(Contradiction).where(Contradiction.id == contradiction_id)
        )
        return result.scalars().first()

    async def update_status(
        self, contradiction_id: str, status: str, resolution_note: str | None = None
    ) -> Contradiction | None:
        contradiction = await self.get(contradiction_id)
        if not contradiction:
            return None
        contradiction.status = status
        if status in ("resolved", "dismissed"):
            contradiction.resolved_at = datetime.utcnow()
            contradiction.resolution_note = resolution_note
        elif status == "open":
            contradiction.resolved_at = None
            contradiction.resolution_note = None
        await self.session.commit()
        await self.session.refresh(contradiction)
        return contradiction

    async def bulk_update_status(
        self, ids: list[str], status: str, resolution_note: str | None = None
    ) -> int:
        """Update status for multiple contradictions. Returns count updated."""
        updated = 0
        for cid in ids:
            result = await self.update_status(cid, status, resolution_note=resolution_note)
            if result:
                updated += 1
        return updated
