import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.models.database import Base


class Contradiction(Base):
    __tablename__ = "contradictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chunk_a_id = Column(String, nullable=False)
    chunk_b_id = Column(String, nullable=False)
    document_a_id = Column(String, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    document_b_id = Column(String, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    document_a_title = Column(String, nullable=False, default="")
    document_b_title = Column(String, nullable=False, default="")
    chunk_a_text = Column(Text, nullable=False)
    chunk_b_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="open")
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
