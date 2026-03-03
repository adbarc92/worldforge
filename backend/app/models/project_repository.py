import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Project, Document


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, description: str | None = None) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get(self, project_id: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalars().first()

    async def list(self) -> list[Project]:
        result = await self.session.execute(
            select(Project).order_by(Project.created_at.asc())
        )
        return list(result.scalars().all())

    async def update(self, project_id: str, name: str | None = None, description: str | None = None) -> Project | None:
        project = await self.get(project_id)
        if not project:
            return None
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete(self, project_id: str) -> bool:
        project = await self.get(project_id)
        if not project:
            return False
        await self.session.delete(project)
        await self.session.commit()
        return True

    async def get_document_count(self, project_id: str) -> int:
        result = await self.session.execute(
            select(func.count(Document.id)).where(Document.project_id == project_id)
        )
        return result.scalars().one()
