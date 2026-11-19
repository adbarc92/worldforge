"""
SQLAlchemy database models
"""
from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import (
    Column, String, DateTime, Float, Boolean, Integer,
    ForeignKey, Table, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# Association tables
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True)
)

proposal_sources = Table(
    'proposal_sources',
    Base.metadata,
    Column('proposal_id', UUID(as_uuid=True), ForeignKey('proposals.id'), primary_key=True),
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('relevance_score', Float)
)

contradiction_documents = Table(
    'contradiction_documents',
    Base.metadata,
    Column('contradiction_id', UUID(as_uuid=True), ForeignKey('contradictions.id'), primary_key=True),
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('statement', Text)
)


class User(Base):
    """User model"""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="user")
    proposals = relationship("Proposal", back_populates="user", foreign_keys="Proposal.user_id")


class Document(Base):
    """Document model"""
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    canon_status = Column(String(50), nullable=False, default='canonical')
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    file_path = Column(Text, nullable=False)
    description = Column(Text)
    chunk_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")


class Tag(Base):
    """Tag model for categorization"""
    __tablename__ = 'tags'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('tags.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", secondary=document_tags, back_populates="tags")
    parent = relationship("Tag", remote_side=[id])


class Proposal(Base):
    """Proposal model for AI-generated content"""
    __tablename__ = 'proposals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content = Column(Text, nullable=False)
    coherence_score = Column(Float)
    status = Column(String(50), nullable=False, default='proposed')
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    user = relationship("User", back_populates="proposals", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class Contradiction(Base):
    """Contradiction detection model"""
    __tablename__ = 'contradictions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)
    resolved = Column(Boolean, default=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    resolution_text = Column(Text, nullable=True)

    # Relationships
    resolver = relationship("User")


class AuditLog(Base):
    """Audit log for tracking all actions"""
    __tablename__ = 'audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    details = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


class SessionState(Base):
    """User session and preferences"""
    __tablename__ = 'session_state'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    preferences = Column(JSON, default={})
    feature_toggles = Column(JSON, default={})
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
