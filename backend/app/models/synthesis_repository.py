from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.synthesis import Synthesis


class SynthesisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        project_id: str,
        title: str = "World Primer",
        auto: bool = False,
    ) -> Synthesis:
        synthesis = Synthesis(
            project_id=project_id,
            title=title,
            outline_approved=auto,
        )
        self.session.add(synthesis)
        await self.session.commit()
        await self.session.refresh(synthesis)
        return synthesis

    async def get(self, synthesis_id: str) -> Synthesis | None:
        result = await self.session.execute(
            select(Synthesis).where(Synthesis.id == synthesis_id)
        )
        return result.scalars().first()

    async def list(
        self, project_id: str, skip: int = 0, limit: int = 20
    ) -> list[Synthesis]:
        stmt = (
            select(Synthesis)
            .where(Synthesis.project_id == project_id)
            .order_by(Synthesis.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_outline(
        self, synthesis_id: str, outline: list[dict]
    ) -> Synthesis | None:
        synthesis = await self.get(synthesis_id)
        if not synthesis:
            return None
        synthesis.outline = outline
        synthesis.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(synthesis)
        return synthesis

    async def update_status(
        self,
        synthesis_id: str,
        status: str,
        content: str | None = None,
        outline: list[dict] | None = None,
        outline_approved: bool | None = None,
        error_message: str | None = None,
    ) -> Synthesis | None:
        synthesis = await self.get(synthesis_id)
        if not synthesis:
            return None
        synthesis.status = status
        synthesis.updated_at = datetime.utcnow()
        if content is not None:
            synthesis.content = content
        if outline is not None:
            synthesis.outline = outline
        if outline_approved is not None:
            synthesis.outline_approved = outline_approved
        if error_message is not None:
            synthesis.error_message = error_message
        await self.session.commit()
        await self.session.refresh(synthesis)
        return synthesis
