"""
Text chunking utilities for splitting documents into manageable pieces.
Uses semantic chunking with configurable size and overlap.
"""

import logging
from typing import List, Dict, Optional
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document as LlamaDocument

from ..config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunk text into overlapping segments for embedding and retrieval."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        logger.info(
            f"Initializing chunker: size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )

        # LlamaIndex sentence splitter
        self.splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            paragraph_separator="\n\n"
        )

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of chunk dictionaries with:
                - text: Chunk text
                - chunk_index: Index of this chunk
                - metadata: Chunk metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        try:
            # Create LlamaIndex document
            doc = LlamaDocument(text=text, metadata=metadata or {})

            # Split into chunks
            nodes = self.splitter.get_nodes_from_documents([doc])

            # Convert to dictionaries
            chunks = []
            for idx, node in enumerate(nodes):
                chunk_data = {
                    "text": node.get_content(),
                    "chunk_index": idx,
                    "metadata": node.metadata.copy() if node.metadata else {},
                    "start_char_idx": node.start_char_idx,
                    "end_char_idx": node.end_char_idx
                }
                chunks.append(chunk_data)

            logger.info(f"Chunked text into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise

    def chunk_document(
        self,
        parsed_document: Dict,
        document_id: str
    ) -> List[Dict]:
        """
        Chunk a parsed document with page-aware metadata.

        Args:
            parsed_document: Output from DocumentParser.parse()
            document_id: Document ID for reference

        Returns:
            List of chunk dictionaries with enhanced metadata
        """
        try:
            chunks = []

            # If document has pages, chunk each page separately
            if "pages" in parsed_document and parsed_document["pages"]:
                for page in parsed_document["pages"]:
                    page_text = page["text"]
                    page_number = page["page_number"]

                    # Chunk this page
                    page_chunks = self.chunk_text(
                        text=page_text,
                        metadata={
                            "document_id": document_id,
                            "page_number": page_number,
                            "file_type": parsed_document.get("file_type", "unknown")
                        }
                    )

                    chunks.extend(page_chunks)

            else:
                # No page info, chunk the full text
                chunks = self.chunk_text(
                    text=parsed_document["text"],
                    metadata={
                        "document_id": document_id,
                        "file_type": parsed_document.get("file_type", "unknown")
                    }
                )

            # Renumber chunks globally
            for idx, chunk in enumerate(chunks):
                chunk["chunk_index"] = idx

            logger.info(
                f"Chunked document {document_id} into {len(chunks)} chunks"
            )
            return chunks

        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            raise

    def get_chunk_stats(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about chunks.

        Args:
            chunks: List of chunk dictionaries

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_chars": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0
            }

        chunk_sizes = [len(chunk["text"]) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "total_chars": sum(chunk_sizes),
            "avg_chunk_size": sum(chunk_sizes) / len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes)
        }
