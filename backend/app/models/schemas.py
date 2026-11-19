"""
Pydantic models for request/response validation
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Enums
class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CanonStatus(str, Enum):
    """Canon status for content"""
    CANONICAL = "canonical"
    PROPOSED = "proposed"
    REJECTED = "rejected"


class ProposalAction(str, Enum):
    """Actions for proposal review"""
    ACCEPT = "accept"
    REJECT = "reject"
    EDIT = "edit"
    REVISE = "revise"


class EntityType(str, Enum):
    """Types of entities in knowledge graph"""
    CHARACTER = "character"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    OBJECT = "object"


class SeverityLevel(str, Enum):
    """Severity levels for contradictions"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


# Authentication
class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str


class UserRegister(BaseModel):
    """User registration request"""
    username: str
    email: str
    password: str


class Token(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    created_at: datetime


# Documents
class DocumentUpload(BaseModel):
    """Document upload metadata"""
    title: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class Document(BaseModel):
    """Document model"""
    id: str
    title: str
    status: DocumentStatus
    canon_status: CanonStatus
    tags: List[str]
    upload_date: datetime
    user_id: str
    file_path: str
    description: Optional[str] = None
    chunk_count: Optional[int] = None


class DocumentList(BaseModel):
    """List of documents response"""
    documents: List[Document]
    total: int


# Query and Retrieval
class QueryRequest(BaseModel):
    """Natural language query request"""
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(default=10, ge=1, le=50)
    include_proposed: bool = Field(default=False)


class Citation(BaseModel):
    """Citation/source for answer"""
    document_id: str
    document_title: str
    chunk_text: str
    relevance_score: float


class QueryResponse(BaseModel):
    """Query response with answer and citations"""
    answer: str
    citations: List[Citation]
    processing_time_ms: float


# Extensions and Proposals
class ExtensionRequest(BaseModel):
    """Request to generate an extension proposal"""
    prompt: str = Field(..., min_length=1, max_length=2000)
    context_documents: Optional[List[str]] = Field(default=None)
    creativity_level: float = Field(default=0.7, ge=0.0, le=1.0)


class Proposal(BaseModel):
    """AI-generated proposal model"""
    id: str
    content: str
    coherence_score: float
    status: CanonStatus
    created_at: datetime
    user_id: str
    prompt: str
    supporting_sources: List[str]
    potential_contradictions: List[str] = Field(default_factory=list)


class ProposalReview(BaseModel):
    """Proposal review decision"""
    action: ProposalAction
    edited_content: Optional[str] = None
    feedback: Optional[str] = None


# Knowledge Graph
class Entity(BaseModel):
    """Entity in knowledge graph"""
    id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_documents: List[str]


class Relationship(BaseModel):
    """Relationship between entities"""
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphQuery(BaseModel):
    """Graph query request"""
    entity_id: str
    depth: int = Field(default=2, ge=1, le=5)


# Consistency
class Contradiction(BaseModel):
    """Detected contradiction"""
    id: str
    description: str
    severity: SeverityLevel
    source_documents: List[str]
    conflicting_statements: List[str]
    detected_at: datetime
    resolved: bool = False


class ContradictionResolution(BaseModel):
    """Resolution for a contradiction"""
    resolution_text: str
    resolved_by: str


# System
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    environment: str
    services: Dict[str, Optional[str]]
