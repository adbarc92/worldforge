"""
API routes for semantic query and search functionality.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.app.database.connection import get_db
from backend.app.database.models import Chunk
from backend.app.api.schemas import (
    QueryRequest,
    QueryResponse,
    CitationResponse,
    RetrievedChunkResponse,
    CitationDetailRequest,
    CitationDetailResponse,
    APIResponse
)
from backend.app.retrieval.query_engine import QueryEngine
from backend.app.retrieval.citation_generator import CitationGenerator
from sqlalchemy import select


router = APIRouter()

# Initialize query engine (singleton)
query_engine = None


def get_query_engine() -> QueryEngine:
    """Get or create query engine instance."""
    global query_engine
    if query_engine is None:
        query_engine = QueryEngine(top_k=5)
    return query_engine


@router.post("/", response_model=QueryResponse)
async def semantic_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute semantic query against the knowledge base.

    Args:
        request: Query request with query text and parameters
        db: Database session

    Returns:
        Query response with answer, citations, and retrieved chunks

    Raises:
        HTTPException: If query fails
    """
    try:
        engine = get_query_engine()

        # Execute query based on search type
        if request.search_type == "hybrid":
            result = await engine.hybrid_search(
                query_text=request.query,
                db=db,
                top_k=request.top_k
            )
        else:
            result = await engine.query(
                query_text=request.query,
                db=db,
                filters=request.filters,
                top_k=request.top_k
            )

        # Format response
        response = QueryResponse(
            answer=result["answer"],
            citations=[CitationResponse(**c) for c in result["citations"]],
            retrieved_chunks=[
                RetrievedChunkResponse(**c) for c in result["retrieved_chunks"]
            ],
            metadata=result["metadata"]
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/citations/details", response_model=List[CitationDetailResponse])
async def get_citation_details(
    request: CitationDetailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get expanded details for specific citations.

    This endpoint allows the frontend to fetch full text and metadata
    for citations when the user expands them.

    Args:
        request: Request with citation numbers
        db: Database session

    Returns:
        List of citation details with full text

    Raises:
        HTTPException: If citation retrieval fails
    """
    try:
        # This would typically retrieve from a cache or recent query results
        # For now, we'll return a not implemented response
        # In production, you'd store recent query results in Redis or similar

        raise HTTPException(
            status_code=501,
            detail="Citation details endpoint not yet implemented. Use /query endpoint for full results."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve citation details: {str(e)}"
        )


@router.get("/history", response_model=APIResponse)
async def get_query_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent query history (placeholder for future feature).

    Args:
        limit: Number of recent queries to return
        db: Database session

    Returns:
        API response with query history

    Note:
        This requires a QueryHistory table which is not yet implemented.
    """
    # Placeholder for future implementation
    return APIResponse(
        success=True,
        data={
            "queries": [],
            "message": "Query history feature not yet implemented"
        },
        metadata={"limit": limit}
    )


@router.post("/validate", response_model=APIResponse)
async def validate_query(request: QueryRequest):
    """
    Validate a query without executing it.

    Useful for frontend validation and query suggestions.

    Args:
        request: Query request

    Returns:
        API response with validation results
    """
    validation_result = {
        "valid": True,
        "issues": [],
        "suggestions": []
    }

    # Check query length
    if len(request.query.strip()) < 3:
        validation_result["valid"] = False
        validation_result["issues"].append("Query too short (minimum 3 characters)")

    if len(request.query) > 1000:
        validation_result["valid"] = False
        validation_result["issues"].append("Query too long (maximum 1000 characters)")

    # Check for empty query
    if not request.query.strip():
        validation_result["valid"] = False
        validation_result["issues"].append("Query cannot be empty")

    # Provide suggestions for common patterns
    query_lower = request.query.lower()
    if query_lower.startswith("what is") or query_lower.startswith("who is"):
        validation_result["suggestions"].append(
            "Specific questions about entities often work well"
        )

    return APIResponse(
        success=True,
        data=validation_result,
        metadata={"query_length": len(request.query)}
    )


@router.get("/stats", response_model=APIResponse)
async def get_query_stats(db: AsyncSession = Depends(get_db)):
    """
    Get statistics about the knowledge base for query context.

    Args:
        db: Database session

    Returns:
        API response with knowledge base statistics
    """
    try:
        # Count total chunks
        chunk_count_result = await db.execute(select(Chunk))
        chunks = chunk_count_result.scalars().all()
        chunk_count = len(chunks)

        # Get ChromaDB stats
        engine = get_query_engine()
        collection_count = engine.collection.count()

        stats = {
            "total_chunks": chunk_count,
            "chromadb_vectors": collection_count,
            "embeddings_model": engine.embed_model.model_name,
            "default_top_k": engine.top_k
        }

        return APIResponse(
            success=True,
            data=stats
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.post("/format-citations", response_model=APIResponse)
async def format_citations(
    answer: str,
    citations: List[CitationResponse],
    format_type: str = "markdown"
):
    """
    Format answer and citations for different display formats.

    Args:
        answer: Answer text with inline citations
        citations: Citation metadata
        format_type: Output format ("markdown", "html", "plain")

    Returns:
        API response with formatted text
    """
    try:
        # Convert Pydantic models to dicts
        citations_dict = [c.model_dump() for c in citations]

        formatted = CitationGenerator.format_for_display(
            answer=answer,
            citations=citations_dict,
            format_type=format_type
        )

        return APIResponse(
            success=True,
            data={"formatted_text": formatted, "format_type": format_type}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to format citations: {str(e)}"
        )
