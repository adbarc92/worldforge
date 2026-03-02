import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, title: str, file_path: str) -> Document:
        doc = Document(
            id=str(uuid.uuid4()),
            title=title,
            file_path=file_path,
            status="pending",
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get(self, doc_id: str) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.id == doc_id)
        )
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 50) -> list[Document]:
        result = await self.session.execute(
            select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self, doc_id: str, status: str, chunk_count: int | None = None, error_message: str | None = None
    ) -> Document | None:
        doc = await self.get(doc_id)
        if not doc:
            return None
        doc.status = status
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def delete(self, doc_id: str) -> bool:
        doc = await self.get(doc_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.commit()
        return True
