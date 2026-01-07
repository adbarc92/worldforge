"""
Unit tests for text chunker.
Tests: TEST-UNIT-006 through TEST-UNIT-008
"""

import pytest
from backend.app.ingestion.chunker import TextChunker


class TestTextChunker:
    """Test suite for TextChunker class."""

    def test_chunker_initialization(self):
        """Test chunker can be initialized with defaults."""
        chunker = TextChunker()
        assert chunker is not None
        assert chunker.chunk_size > 0
        assert chunker.chunk_overlap >= 0

    def test_chunker_custom_parameters(self):
        """Test chunker accepts custom parameters."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 20

    # TEST-UNIT-007: Chunk Empty Text
    @pytest.mark.unit
    def test_chunk_empty_text(self):
        """Test chunking handles empty text gracefully."""
        chunker = TextChunker()

        chunks = chunker.chunk_text("")

        assert chunks == []

    @pytest.mark.unit
    def test_chunk_none_text(self):
        """Test chunking handles None text gracefully."""
        chunker = TextChunker()

        chunks = chunker.chunk_text(None)

        assert chunks == []

    @pytest.mark.unit
    def test_chunk_whitespace_only(self):
        """Test chunking handles whitespace-only text."""
        chunker = TextChunker()

        chunks = chunker.chunk_text("   \n\n  \t  ")

        assert chunks == []

    # TEST-UNIT-006: Chunk Text with Overlap
    @pytest.mark.unit
    def test_chunk_text_with_overlap(self, sample_text):
        """Test text chunking with specified overlap."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        chunks = chunker.chunk_text(sample_text)

        # Basic assertions
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("chunk_index" in chunk for chunk in chunks)

        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i

    @pytest.mark.unit
    def test_chunk_long_text(self):
        """Test chunking handles long text properly."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        # Create long text
        long_text = "Lorem ipsum dolor sit amet. " * 200  # ~5600 chars

        chunks = chunker.chunk_text(long_text)

        # Should create multiple chunks
        assert len(chunks) > 1

        # All chunks should have content
        assert all(len(chunk["text"]) > 0 for chunk in chunks)

        # Chunks should have metadata
        assert all("start_char_idx" in chunk for chunk in chunks)
        assert all("end_char_idx" in chunk for chunk in chunks)

    @pytest.mark.unit
    def test_chunk_short_text(self):
        """Test chunking handles text shorter than chunk size."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)

        short_text = "This is a short text that fits in one chunk."

        chunks = chunker.chunk_text(short_text)

        # Should create exactly one chunk
        assert len(chunks) == 1
        assert chunks[0]["text"] == short_text
        assert chunks[0]["chunk_index"] == 0

    # TEST-UNIT-008: Chunk Document with Pages
    @pytest.mark.unit
    def test_chunk_document_with_pages(self):
        """Test chunking preserves page metadata."""
        chunker = TextChunker()

        parsed_doc = {
            "text": "Full text here",
            "pages": [
                {"page_number": 1, "text": "Page 1 content with some text here."},
                {"page_number": 2, "text": "Page 2 content with more text here."}
            ],
            "file_type": "pdf"
        }
        document_id = "test-doc-123"

        chunks = chunker.chunk_document(parsed_doc, document_id)

        # Basic assertions
        assert len(chunks) > 0
        assert all("metadata" in chunk for chunk in chunks)

        # Verify document_id in metadata
        assert all(
            chunk["metadata"]["document_id"] == document_id
            for chunk in chunks
        )

        # Verify file_type in metadata
        assert all(
            chunk["metadata"]["file_type"] == "pdf"
            for chunk in chunks
        )

        # Should have page numbers
        assert any(
            chunk["metadata"].get("page_number") is not None
            for chunk in chunks
        )

    @pytest.mark.unit
    def test_chunk_document_without_pages(self):
        """Test chunking document without page information."""
        chunker = TextChunker()

        parsed_doc = {
            "text": "Document without page information. " * 50,
            "pages": [],
            "file_type": "txt"
        }
        document_id = "test-doc-456"

        chunks = chunker.chunk_document(parsed_doc, document_id)

        assert len(chunks) > 0
        assert all(chunk["metadata"]["document_id"] == document_id for chunk in chunks)

        # Should not have page numbers
        assert all(
            chunk["metadata"].get("page_number") is None
            for chunk in chunks
        )

    def test_get_chunk_stats(self):
        """Test chunk statistics calculation."""
        chunker = TextChunker()

        chunks = [
            {"text": "A" * 100, "chunk_index": 0, "metadata": {}},
            {"text": "B" * 200, "chunk_index": 1, "metadata": {}},
            {"text": "C" * 150, "chunk_index": 2, "metadata": {}}
        ]

        stats = chunker.get_chunk_stats(chunks)

        assert stats["total_chunks"] == 3
        assert stats["total_chars"] == 450
        assert stats["avg_chunk_size"] == 150
        assert stats["min_chunk_size"] == 100
        assert stats["max_chunk_size"] == 200

    def test_get_chunk_stats_empty(self):
        """Test chunk statistics with empty list."""
        chunker = TextChunker()

        stats = chunker.get_chunk_stats([])

        assert stats["total_chunks"] == 0
        assert stats["total_chars"] == 0
        assert stats["avg_chunk_size"] == 0

    @pytest.mark.unit
    def test_chunk_preserves_metadata(self):
        """Test that custom metadata is preserved in chunks."""
        chunker = TextChunker()

        metadata = {
            "author": "Tolkien",
            "title": "LOTR",
            "custom_field": "value"
        }

        text = "Sample text for metadata preservation test."

        chunks = chunker.chunk_text(text, metadata=metadata)

        # Metadata should be in chunks
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["metadata"]["author"] == "Tolkien"
            assert chunk["metadata"]["title"] == "LOTR"
            assert chunk["metadata"]["custom_field"] == "value"

    @pytest.mark.unit
    def test_chunk_indices_are_sequential(self):
        """Test that chunk indices are properly sequential."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        long_text = "Word " * 200

        chunks = chunker.chunk_text(long_text)

        # Verify indices are 0, 1, 2, 3, ...
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
