"""
SQLAlchemy database models for AetherCanon Builder.
Defines the schema for documents, entities, relationships, and review queue.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def generate_uuid() -> str:
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class Document(Base):
    """Document model - represents uploaded documents."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False, index=True)
    original_filename = Column(String)
    file_path = Column(String, nullable=False)
    file_type = Column(String)  # pdf, docx, md, txt
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String, default="active")  # active, archived
    git_commit_hash = Column(String)
    extra_metadata = Column("metadata", JSON, default=dict)  # Renamed to avoid SQLAlchemy conflict
    chunk_count = Column(Integer, default=0)
    entity_count = Column(Integer, default=0)

    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    relationships_as_evidence = relationship("Relationship", back_populates="evidence_document")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title})>"


class Entity(Base):
    """Entity model - represents canonical entities (characters, locations, etc.)."""

    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # character, location, event, concept, item
    canonical_description = Column(Text)
    first_mentioned_doc_id = Column(String, ForeignKey("documents.id"))
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    extra_metadata = Column("metadata", JSON, default=dict)  # Renamed to avoid SQLAlchemy conflict

    # Relationships
    outgoing_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.source_entity_id",
        back_populates="source_entity"
    )
    incoming_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.target_entity_id",
        back_populates="target_entity"
    )
    conflicts_as_entity_1 = relationship(
        "Conflict",
        foreign_keys="Conflict.entity_id_1",
        back_populates="entity_1"
    )
    conflicts_as_entity_2 = relationship(
        "Conflict",
        foreign_keys="Conflict.entity_id_2",
        back_populates="entity_2"
    )

    def __repr__(self) -> str:
        return f"<Entity(id={self.id}, name={self.name}, type={self.type})>"


class Relationship(Base):
    """Relationship model - represents relationships between entities."""

    __tablename__ = "relationships"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    target_entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    relation_type = Column(String, nullable=False)  # located_in, allied_with, created_by, etc.
    evidence_doc_id = Column(String, ForeignKey("documents.id"))
    evidence_excerpt = Column(Text)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    extra_metadata = Column("metadata", JSON, default=dict)  # Renamed to avoid SQLAlchemy conflict

    # Relationships
    source_entity = relationship(
        "Entity",
        foreign_keys=[source_entity_id],
        back_populates="outgoing_relationships"
    )
    target_entity = relationship(
        "Entity",
        foreign_keys=[target_entity_id],
        back_populates="incoming_relationships"
    )
    evidence_document = relationship("Document", back_populates="relationships_as_evidence")

    def __repr__(self) -> str:
        return f"<Relationship(id={self.id}, type={self.relation_type})>"


class Chunk(Base):
    """Chunk model - represents text chunks from documents."""

    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer)
    section_title = Column(String)
    chromadb_id = Column(String, index=True)  # Reference to vector in ChromaDB
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class ProposedContent(Base):
    """Proposed content model - review queue for AI-generated content."""

    __tablename__ = "proposed_content"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String, nullable=False, index=True)  # entity, relationship, document_extension
    content = Column(JSON, nullable=False)  # Flexible structure based on type
    generation_metadata = Column(JSON, default=dict)  # model, prompt, timestamp, etc.
    coherence_score = Column(Float)
    conflicts = Column(JSON, default=list)  # [{severity, with_entity_id, reason}]
    review_status = Column(String, default="pending", index=True)  # pending, approved, rejected, edited
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<ProposedContent(id={self.id}, type={self.type}, status={self.review_status})>"


class Conflict(Base):
    """Conflict model - represents detected inconsistencies."""

    __tablename__ = "conflicts"

    id = Column(String, primary_key=True, default=generate_uuid)
    entity_id_1 = Column(String, ForeignKey("entities.id"), index=True)
    entity_id_2 = Column(String, ForeignKey("entities.id"), index=True)
    conflict_type = Column(String, nullable=False)  # contradiction, inconsistent_characterization, timeline_mismatch
    severity = Column(String, nullable=False, index=True)  # high, medium, low
    description = Column(Text, nullable=False)
    evidence_1 = Column(Text)
    evidence_2 = Column(Text)
    source_doc_1_id = Column(String, ForeignKey("documents.id"))
    source_doc_2_id = Column(String, ForeignKey("documents.id"))
    status = Column(String, default="unresolved", index=True)  # unresolved, not_a_conflict, resolved
    resolved_by = Column(String)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    entity_1 = relationship(
        "Entity",
        foreign_keys=[entity_id_1],
        back_populates="conflicts_as_entity_1"
    )
    entity_2 = relationship(
        "Entity",
        foreign_keys=[entity_id_2],
        back_populates="conflicts_as_entity_2"
    )

    def __repr__(self) -> str:
        return f"<Conflict(id={self.id}, type={self.conflict_type}, severity={self.severity})>"
