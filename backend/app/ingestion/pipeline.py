"""
Document ingestion pipeline orchestrating parsing, chunking, embedding, and entity extraction.
Main entry point for processing uploaded documents.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.models import Document, Chunk, ProposedContent
from ..database.connection import get_chroma
from .parser import DocumentParser
from .chunker import TextChunker
from .embedder import get_embedder
from .entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates the full document ingestion workflow:
    1. Parse document
    2. Chunk text
    3. Generate embeddings
    4. Store in ChromaDB
    5. Extract entities
    6. Store in database
    """

    def __init__(self):
        """Initialize ingestion pipeline components."""
        self.parser = DocumentParser()
        self.chunker = TextChunker()
        self.embedder = get_embedder()
        self.entity_extractor = EntityExtractor()
        self.chroma = get_chroma()

        # Get ChromaDB collection
        try:
            self.chunk_collection = self.chroma.get_collection("document_chunks")
        except Exception:
            self.chunk_collection = self.chroma.create_collection(
                name="document_chunks",
                metadata={"description": "Document text chunks with embeddings"}
            )

        logger.info("Ingestion pipeline initialized")

    async def process_document(
        self,
        file_path: str,
        title: str,
        db: AsyncSession,
        extract_entities: bool = True
    ) -> Document:
        """
        Process a document through the full ingestion pipeline.

        Args:
            file_path: Path to the document file
            title: Document title
            db: Database session
            extract_entities: Whether to extract entities (can be disabled for testing)

        Returns:
            Created Document object

        Raises:
            ValueError: If file format not supported
            Exception: If processing fails
        """
        try:
            logger.info(f"Starting ingestion pipeline for: {title}")

            # 1. Parse document
            logger.info("Step 1/5: Parsing document")
            parsed_doc = self.parser.parse(file_path)

            # 2. Create document record
            document_id = str(uuid.uuid4())
            document = Document(
                id=document_id,
                title=title,
                original_filename=Path(file_path).name,
                file_path=file_path,
                file_type=parsed_doc["file_type"],
                upload_date=datetime.utcnow(),
                status="processing",
                metadata=parsed_doc["metadata"]
            )
            db.add(document)
            await db.flush()  # Get the ID without committing

            # 3. Chunk text
            logger.info("Step 2/5: Chunking text")
            chunks = self.chunker.chunk_document(parsed_doc, document_id)
            chunk_stats = self.chunker.get_chunk_stats(chunks)
            logger.info(f"Created {len(chunks)} chunks: {chunk_stats}")

            # 4. Generate embeddings and store in ChromaDB
            logger.info("Step 3/5: Generating embeddings")
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedder.embed_batch(
                texts=chunk_texts,
                show_progress=len(chunks) > 10
            )

            # 5. Store chunks in ChromaDB
            logger.info("Step 4/5: Storing chunks in ChromaDB")
            chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

            self.chunk_collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=[
                    {
                        "document_id": document_id,
                        "document_title": title,
                        "chunk_index": chunk["chunk_index"],
                        "page_number": chunk["metadata"].get("page_number"),
                        "file_type": parsed_doc["file_type"]
                    }
                    for chunk in chunks
                ]
            )

            # 6. Store chunks in SQLite
            for i, chunk in enumerate(chunks):
                chunk_record = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=chunk["text"],
                    chunk_index=chunk["chunk_index"],
                    page_number=chunk["metadata"].get("page_number"),
                    chromadb_id=chunk_ids[i],
                    created_at=datetime.utcnow()
                )
                db.add(chunk_record)

            # 7. Extract entities (if enabled)
            entity_count = 0
            if extract_entities:
                logger.info("Step 5/5: Extracting entities")
                entities = await self.entity_extractor.extract_entities_from_chunks(
                    chunks=chunks,
                    document_id=document_id,
                    max_chunks=5  # Limit for MVP to avoid long processing times
                )

                # Store entities in proposed_content table
                for entity in entities:
                    proposed = ProposedContent(
                        id=str(uuid.uuid4()),
                        type="entity",
                        content=entity,
                        generation_metadata={
                            "model": settings.llm_provider,
                            "timestamp": datetime.utcnow().isoformat(),
                            "source_document_id": document_id
                        },
                        coherence_score=entity.get("confidence", 0.5),
                        review_status="pending",
                        created_at=datetime.utcnow()
                    )
                    db.add(proposed)
                    entity_count += 1

                logger.info(f"Extracted {entity_count} entities")

                # Run conflict detection for new entities (optional, can be async)
                # This detects conflicts between newly proposed entities and existing canon
                try:
                    from backend.app.consistency.detector import InconsistencyDetector
                    detector = InconsistencyDetector()

                    # Check document for conflicts (background task in production)
                    conflicts = await detector.check_document_for_conflicts(
                        document_id=document_id,
                        db=db
                    )

                    # Store detected conflicts
                    for conflict_data in conflicts:
                        await detector.store_conflict(conflict_data, db)

                    if conflicts:
                        logger.warning(f"Detected {len(conflicts)} potential conflicts for new entities")
                except Exception as e:
                    # Don't fail ingestion if conflict detection fails
                    logger.error(f"Conflict detection failed: {e}")

            else:
                logger.info("Step 5/5: Skipping entity extraction")

            # Update document with counts and status
            document.chunk_count = len(chunks)
            document.entity_count = entity_count
            document.status = "active"

            await db.commit()

            logger.info(
                f"Document ingestion complete: {title} "
                f"({len(chunks)} chunks, {entity_count} entities)"
            )

            return document

        except Exception as e:
            logger.error(f"Error in ingestion pipeline: {e}")
            if db:
                await db.rollback()
            raise

    async def delete_document(
        self,
        document_id: str,
        db: AsyncSession
    ) -> None:
        """
        Delete a document and all associated data.

        Args:
            document_id: Document ID to delete
            db: Database session
        """
        try:
            logger.info(f"Deleting document: {document_id}")

            # Delete from ChromaDB
            try:
                # Get all chunk IDs for this document
                results = self.chunk_collection.get(
                    where={"document_id": document_id}
                )
                if results and results["ids"]:
                    self.chunk_collection.delete(ids=results["ids"])
                    logger.info(f"Deleted {len(results['ids'])} chunks from ChromaDB")
            except Exception as e:
                logger.warning(f"Error deleting from ChromaDB: {e}")

            # SQLite cascading deletes will handle chunks
            # Just delete the document
            from sqlalchemy import select, delete
            await db.execute(
                delete(Document).where(Document.id == document_id)
            )
            await db.commit()

            logger.info(f"Document {document_id} deleted successfully")

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            await db.rollback()
            raise
