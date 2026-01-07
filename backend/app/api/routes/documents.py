"""
Document API routes for upload, list, and delete operations.
"""

import logging
import os
import time
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ...config import settings
from ...database.connection import get_db
from ...database.models import Document, Chunk, ProposedContent
from ...ingestion.pipeline import IngestionPipeline
from ..schemas import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    APIResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize pipeline (singleton)
_pipeline = None


def get_pipeline() -> IngestionPipeline:
    """Get or create ingestion pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = IngestionPipeline()
    return _pipeline


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = None,
    extract_entities: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a document.

    Args:
        file: The uploaded file (PDF, DOCX, MD, TXT)
        title: Optional document title (defaults to filename)
        extract_entities: Whether to extract entities (default: True)
        db: Database session

    Returns:
        Document with processing statistics
    """
    start_time = time.time()

    try:
        # Validate file type
        suffix = Path(file.filename).suffix.lower()
        supported_formats = {".pdf", ".docx", ".md", ".txt", ".markdown"}

        if suffix not in supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {suffix}. Supported: {supported_formats}"
            )

        # Use filename as title if not provided
        if not title:
            title = Path(file.filename).stem

        # Ensure documents directory exists
        os.makedirs(settings.documents_path, exist_ok=True)

        # Save file to disk
        file_path = os.path.join(
            settings.documents_path,
            f"{int(time.time())}_{file.filename}"
        )

        logger.info(f"Saving uploaded file to: {file_path}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process document through pipeline
        logger.info(f"Processing document: {title}")
        pipeline = get_pipeline()

        document = await pipeline.process_document(
            file_path=file_path,
            title=title,
            db=db,
            extract_entities=extract_entities
        )

        processing_time = time.time() - start_time

        logger.info(
            f"Document uploaded successfully: {document.id} "
            f"({processing_time:.2f}s)"
        )

        return DocumentUploadResponse(
            document=DocumentResponse.from_orm(document),
            chunks_created=document.chunk_count,
            entities_extracted=document.entity_count,
            processing_time_seconds=round(processing_time, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents with optional filtering.

    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        status_filter: Optional status filter (active, archived, processing)
        db: Database session

    Returns:
        List of documents with total count
    """
    try:
        # Build query
        query = select(Document).order_by(Document.upload_date.desc())

        if status_filter:
            query = query.where(Document.status == status_filter)

        # Get total count
        count_query = select(Document)
        if status_filter:
            count_query = count_query.where(Document.status == status_filter)

        count_result = await db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        documents = result.scalars().all()

        return DocumentListResponse(
            documents=[DocumentResponse.from_orm(doc) for doc in documents],
            total=total
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific document by ID.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Document details
    """
    try:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        return DocumentResponse.from_orm(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document: {str(e)}"
        )


@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and all associated data.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Success response
    """
    try:
        # Check if document exists
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        # Delete through pipeline (handles ChromaDB cleanup)
        pipeline = get_pipeline()
        await pipeline.delete_document(document_id, db)

        # Delete file from disk if it exists
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
                logger.info(f"Deleted file: {document.file_path}")
        except Exception as e:
            logger.warning(f"Could not delete file: {e}")

        logger.info(f"Document deleted: {document_id}")

        return APIResponse(
            success=True,
            data={"document_id": document_id},
            metadata={"message": "Document deleted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


@router.get("/{document_id}/chunks", response_model=List)
async def get_document_chunks(
    document_id: str,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chunks for a specific document.

    Args:
        document_id: Document ID
        skip: Number of chunks to skip
        limit: Maximum chunks to return
        db: Database session

    Returns:
        List of chunks
    """
    try:
        query = (
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        chunks = result.scalars().all()

        return chunks

    except Exception as e:
        logger.error(f"Error getting chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting chunks: {str(e)}"
        )
