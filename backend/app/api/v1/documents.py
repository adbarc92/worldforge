"""
Document management endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import List
from loguru import logger

from app.models.schemas import Document, DocumentList, DocumentUpload
from app.core.security import get_current_user

router = APIRouter()


@router.post("/upload", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    metadata: DocumentUpload = Depends(),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a new document to the canon

    Accepts: PDF, DOCX, TXT, Markdown, Images

    TODO: Implement document processing pipeline
    """
    logger.info(f"Uploading document: {file.filename}")

    # TODO:
    # 1. Save file to disk
    # 2. Parse with Unstructured.io
    # 3. Chunk with LlamaIndex
    # 4. Generate embeddings
    # 5. Store in Qdrant
    # 6. Extract entities and build graph
    # 7. Store metadata in PostgreSQL

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document upload pipeline not yet implemented"
    )


@router.get("", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    List all documents in the canon

    TODO: Implement database query
    """
    logger.info(f"Listing documents (skip={skip}, limit={limit})")

    # TODO: Query PostgreSQL for document list

    return DocumentList(documents=[], total=0)


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details for a specific document

    TODO: Implement database lookup
    """
    logger.info(f"Getting document: {document_id}")

    # TODO: Query database for document

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document {document_id} not found"
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a document from the canon

    TODO: Implement deletion with cleanup
    """
    logger.info(f"Deleting document: {document_id}")

    # TODO:
    # 1. Remove from filesystem
    # 2. Remove from Qdrant
    # 3. Remove from Neo4j
    # 4. Remove from PostgreSQL

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document deletion not yet implemented"
    )
