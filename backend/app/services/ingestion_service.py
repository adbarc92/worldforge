"""
Document ingestion pipeline service
Handles document upload, parsing, chunking, and indexing
"""
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from app.core.config import settings
from app.services.ollama_service import OllamaService
from app.services.qdrant_service import QdrantService


class IngestionService:
    """Service for document ingestion pipeline"""

    def __init__(self):
        """Initialize ingestion service"""
        self.ollama_service = OllamaService()
        self.qdrant_service = QdrantService()
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    async def process_document(
        self,
        file_path: str,
        document_id: str,
        title: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Process a document through the full ingestion pipeline

        Steps:
        1. Parse document (extract text)
        2. Chunk text
        3. Generate embeddings
        4. Store in Qdrant
        5. Return metadata

        Args:
            file_path: Path to document file
            document_id: Unique document identifier
            title: Document title
            user_id: User who uploaded the document

        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing document: {title} (ID: {document_id})")

        try:
            # Step 1: Parse document
            text = await self._parse_document(file_path)
            logger.info(f"Extracted {len(text)} characters from document")

            # Step 2: Chunk text
            chunks = await self._chunk_text(text, document_id, title)
            logger.info(f"Created {len(chunks)} chunks")

            # Step 3: Generate embeddings
            embeddings = await self._generate_embeddings(chunks)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Step 4: Store in Qdrant
            await self._store_in_qdrant(
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata={
                    "title": title,
                    "user_id": user_id,
                    "canon_status": "canonical"
                }
            )

            return {
                "success": True,
                "document_id": document_id,
                "chunk_count": len(chunks),
                "char_count": len(text)
            }

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            raise

    async def _parse_document(self, file_path: str) -> str:
        """
        Parse document and extract text

        TODO: Integrate with Unstructured.io for advanced parsing
        For MVP, handle basic text files

        Args:
            file_path: Path to document

        Returns:
            Extracted text
        """
        try:
            # For MVP: Simple text file reading
            # TODO: Add PDF, DOCX, image OCR support via Unstructured.io
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            return text

        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            # Try binary mode if UTF-8 fails
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    text = content.decode('utf-8', errors='ignore')
                return text
            except:
                raise Exception(f"Could not parse document: {e}")

    async def _chunk_text(
        self,
        text: str,
        document_id: str,
        title: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk text using LlamaIndex

        Args:
            text: Document text
            document_id: Document identifier
            title: Document title

        Returns:
            List of chunk dictionaries
        """
        try:
            # Create LlamaIndex document
            llama_doc = LlamaDocument(
                text=text,
                metadata={
                    "document_id": document_id,
                    "title": title
                }
            )

            # Initialize sentence splitter
            splitter = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )

            # Split into nodes
            nodes = splitter.get_nodes_from_documents([llama_doc])

            # Convert to dictionaries
            chunks = []
            for i, node in enumerate(nodes):
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{i}",
                    "text": node.get_content(),
                    "chunk_index": i,
                    "document_id": document_id,
                    "title": title
                })

            return chunks

        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise

    async def _generate_embeddings(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[List[float]]:
        """
        Generate embeddings for chunks

        Args:
            chunks: List of chunk dictionaries

        Returns:
            List of embedding vectors
        """
        try:
            texts = [chunk["text"] for chunk in chunks]
            embeddings = await self.ollama_service.embed_batch(texts)
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def _store_in_qdrant(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ):
        """
        Store chunks and embeddings in Qdrant

        Args:
            document_id: Document identifier
            chunks: List of chunks
            embeddings: List of embedding vectors
            metadata: Document metadata
        """
        try:
            # Ensure collection exists
            await self.qdrant_service.ensure_collection()

            # Prepare payloads
            payloads = []
            ids = []
            for chunk in chunks:
                payload = {
                    **chunk,
                    **metadata
                }
                payloads.append(payload)
                ids.append(chunk["chunk_id"])

            # Store in Qdrant
            await self.qdrant_service.add_vectors(
                vectors=embeddings,
                payloads=payloads,
                ids=ids
            )

            logger.info(f"Stored {len(chunks)} chunks in Qdrant for document {document_id}")

        except Exception as e:
            logger.error(f"Error storing in Qdrant: {e}")
            raise

    async def delete_document(self, document_id: str):
        """
        Delete all data for a document

        Args:
            document_id: Document identifier
        """
        try:
            # Delete from Qdrant
            await self.qdrant_service.delete_by_document_id(document_id)

            # TODO: Delete from filesystem
            # TODO: Delete from Neo4j (will be in entity service)

            logger.info(f"Deleted document: {document_id}")

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
