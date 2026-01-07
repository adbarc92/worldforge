"""
Pydantic schemas for API request and response models.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Standard API response wrapper
class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)


# Document schemas
class DocumentBase(BaseModel):
    """Base document schema."""
    title: str
    file_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    pass


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: str
    original_filename: Optional[str] = None
    file_path: str
    upload_date: datetime
    status: str
    metadata: Optional[Dict] = None
    chunk_count: int = 0
    entity_count: int = 0

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""
    documents: List[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    document: DocumentResponse
    chunks_created: int
    entities_extracted: int
    processing_time_seconds: float


# Chunk schemas
class ChunkResponse(BaseModel):
    """Schema for chunk response."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Entity schemas
class EntityContent(BaseModel):
    """Schema for entity content (stored in ProposedContent.content)."""
    name: str
    type: str  # character, location, event, concept, item
    description: str
    confidence: float
    source_document_id: str
    source_chunk_index: Optional[int] = None
    source_page_number: Optional[int] = None


class ProposedContentResponse(BaseModel):
    """Schema for proposed content response."""
    id: str
    type: str
    content: Dict[str, Any]
    generation_metadata: Optional[Dict] = None
    coherence_score: Optional[float] = None
    conflicts: Optional[List] = Field(default_factory=list)
    review_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProposedContentListResponse(BaseModel):
    """Schema for list of proposed content."""
    items: List[ProposedContentResponse]
    total: int


# Query schemas
class QueryRequest(BaseModel):
    """Schema for semantic query request."""
    query: str = Field(..., min_length=1, description="Question or search query")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters (e.g., document_id)")
    search_type: Optional[str] = Field(default="vector", description="Search type: 'vector' or 'hybrid'")


class CitationResponse(BaseModel):
    """Schema for a single citation."""
    number: int
    document_id: Optional[str] = None
    document_title: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None


class RetrievedChunkResponse(BaseModel):
    """Schema for a retrieved chunk in query results."""
    chunk_id: str
    text: str
    score: float
    document_id: Optional[str] = None
    page_number: Optional[int] = None


class QueryResponse(BaseModel):
    """Schema for semantic query response."""
    answer: str
    citations: List[CitationResponse]
    retrieved_chunks: List[RetrievedChunkResponse]
    metadata: Dict[str, Any]


class CitationDetailRequest(BaseModel):
    """Schema for requesting citation details."""
    citation_numbers: List[int]


class CitationDetailResponse(BaseModel):
    """Schema for expandable citation details."""
    number: int
    title: str
    document_id: Optional[str] = None
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    preview: Optional[str] = None
    full_text: Optional[str] = None


# Conflict schemas
class ConflictResponse(BaseModel):
    """Schema for conflict/contradiction response."""
    id: str
    entity_id_1: Optional[str] = None
    entity_id_2: Optional[str] = None
    conflict_type: str
    severity: str
    description: str
    evidence_1: Optional[str] = None
    evidence_2: Optional[str] = None
    status: str
    resolution: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConflictListResponse(BaseModel):
    """Schema for list of conflicts."""
    conflicts: List[ConflictResponse]
    total: int
    by_severity: Dict[str, int]
    by_status: Dict[str, int]


class ConflictDetectionRequest(BaseModel):
    """Schema for manual conflict detection request."""
    entity_id: Optional[str] = Field(default=None, description="Specific entity to check")
    document_id: Optional[str] = Field(default=None, description="Check all entities from document")
    proposed_content_id: Optional[str] = Field(default=None, description="Check proposed content")
    run_full_check: bool = Field(default=False, description="Run full consistency check")


class ConflictDetectionResponse(BaseModel):
    """Schema for conflict detection results."""
    conflicts_detected: int
    conflicts: List[ConflictResponse]
    metadata: Dict[str, Any]


class ConflictResolutionRequest(BaseModel):
    """Schema for resolving a conflict."""
    resolution: str = Field(..., min_length=1, description="How the conflict was resolved")
    chosen_entity_id: Optional[str] = Field(default=None, description="Which entity is canonical")


# Review queue schemas
class ReviewQueueItemResponse(BaseModel):
    """Schema for a single review queue item."""
    item: ProposedContentResponse
    conflicts: List[ConflictResponse]
    has_conflicts: bool
    conflict_count: int
    priority_score: float


class ReviewQueueResponse(BaseModel):
    """Schema for review queue listing."""
    items: List[Dict[str, Any]]  # Includes item, conflicts, priority
    total: int
    skip: int
    limit: int
    filters: Dict[str, Any]


class ReviewQueueStatsResponse(BaseModel):
    """Schema for review queue statistics."""
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    items_with_conflicts: int
    average_confidence: float
    total_pending: int
    needs_review: int


class ApprovalRequest(BaseModel):
    """Schema for approving proposed content."""
    reviewed_by: Optional[str] = Field(default=None, description="User performing review")


class RejectionRequest(BaseModel):
    """Schema for rejecting proposed content."""
    reason: Optional[str] = Field(default=None, description="Reason for rejection")
    reviewed_by: Optional[str] = Field(default=None, description="User performing review")


class EditAndApproveRequest(BaseModel):
    """Schema for editing and approving content."""
    updated_content: Dict[str, Any] = Field(..., description="Updated content data")
    reviewed_by: Optional[str] = Field(default=None, description="User performing review")


class BulkApprovalRequest(BaseModel):
    """Schema for bulk approval."""
    item_ids: List[str] = Field(..., min_items=1, description="List of proposed content IDs")
    reviewed_by: Optional[str] = Field(default=None, description="User performing review")


class BulkApprovalResponse(BaseModel):
    """Schema for bulk approval results."""
    total_requested: int
    approved_entities: int
    approved_relationships: int
    errors: int
    error_details: List[Dict[str, Any]]


class MergeApprovalRequest(BaseModel):
    """Schema for approval with merge."""
    merge_with_entity_id: str = Field(..., description="Entity ID to merge into")
    reviewed_by: Optional[str] = Field(default=None, description="User performing review")


# Entity response schema
class EntityResponse(BaseModel):
    """Schema for entity response."""
    id: str
    name: str
    type: str
    canonical_description: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Relationship response schema
class RelationshipResponse(BaseModel):
    """Schema for relationship response."""
    id: str
    source_entity_id: Optional[str] = None
    target_entity_id: Optional[str] = None
    relation_type: str
    evidence_doc_id: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Export schemas
class ExportRequest(BaseModel):
    """Schema for export request."""
    export_name: Optional[str] = Field(default=None, description="Name for this export")
    include_graph: bool = Field(default=True, description="Include graph JSON")
    graph_format: str = Field(default="d3", description="Graph format: d3, cytoscape, simple")


class ExportResponse(BaseModel):
    """Schema for export response."""
    export_id: str
    export_name: str
    export_path: str
    entities_exported: int
    relationships_exported: int
    files_created: int
    created_at: str


# Health check schema
class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str
    environment: str
    llm_provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
