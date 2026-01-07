"""
Unit tests for document parser.
Tests: TEST-UNIT-001 through TEST-UNIT-005
"""

import pytest
from pathlib import Path
from backend.app.ingestion.parser import DocumentParser


class TestDocumentParser:
    """Test suite for DocumentParser class."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = DocumentParser()
        assert parser is not None
        assert hasattr(parser, 'SUPPORTED_FORMATS')

    def test_supported_formats(self):
        """Test supported formats are defined correctly."""
        parser = DocumentParser()
        expected_formats = {".pdf", ".docx", ".md", ".txt", ".markdown"}
        assert parser.SUPPORTED_FORMATS == expected_formats

    def test_is_supported_pdf(self):
        """Test PDF format is recognized as supported."""
        parser = DocumentParser()
        assert parser.is_supported("document.pdf") is True
        assert parser.is_supported("document.PDF") is True  # Case insensitive

    def test_is_supported_docx(self):
        """Test DOCX format is recognized as supported."""
        parser = DocumentParser()
        assert parser.is_supported("document.docx") is True

    def test_is_supported_markdown(self):
        """Test Markdown formats are recognized as supported."""
        parser = DocumentParser()
        assert parser.is_supported("document.md") is True
        assert parser.is_supported("document.markdown") is True

    def test_is_supported_text(self):
        """Test TXT format is recognized as supported."""
        parser = DocumentParser()
        assert parser.is_supported("document.txt") is True

    def test_is_not_supported(self):
        """Test unsupported formats are rejected."""
        parser = DocumentParser()
        assert parser.is_supported("document.xlsx") is False
        assert parser.is_supported("document.pptx") is False
        assert parser.is_supported("document.jpg") is False

    # TEST-UNIT-004: Reject Unsupported Format
    @pytest.mark.unit
    def test_reject_unsupported_format(self):
        """Test that unsupported formats raise ValueError."""
        parser = DocumentParser()
        unsupported_file = "tests/fixtures/sample.xlsx"

        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse(unsupported_file)

    # TEST-UNIT-005: Handle Missing File
    @pytest.mark.unit
    def test_handle_missing_file(self):
        """Test error handling for non-existent files."""
        parser = DocumentParser()
        missing_file = "tests/fixtures/nonexistent.pdf"

        with pytest.raises(FileNotFoundError):
            parser.parse(missing_file)

    @pytest.mark.unit
    def test_extract_text_only(self, sample_markdown, tmp_path):
        """Test extracting just text content."""
        parser = DocumentParser()

        # Create temporary markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text(sample_markdown)

        # Extract text
        text = parser.extract_text_only(str(test_file))

        assert isinstance(text, str)
        assert len(text) > 0
        assert "Aragorn" in text or "Test Document" in text

    # TEST-UNIT-003: Parse Markdown Document
    @pytest.mark.unit
    def test_parse_markdown_document(self, sample_markdown, tmp_path):
        """Test Markdown document parsing with headings."""
        parser = DocumentParser()

        # Create temporary markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text(sample_markdown)

        # Parse
        result = parser.parse(str(test_file))

        # Assertions
        assert result["file_type"] == "md"
        assert len(result["text"]) > 0
        assert result["metadata"]["total_elements"] > 0
        assert "elements" in result

        # Should preserve structure
        assert "Aragorn" in result["text"] or "Characters" in result["text"]

    @pytest.mark.unit
    def test_parse_text_document(self, sample_text, tmp_path):
        """Test plain text document parsing."""
        parser = DocumentParser()

        # Create temporary text file
        test_file = tmp_path / "test.txt"
        test_file.write_text(sample_text)

        # Parse
        result = parser.parse(str(test_file))

        # Assertions
        assert result["file_type"] == "txt"
        assert len(result["text"]) > 0
        assert "Aragorn" in result["text"]

    def test_process_elements_structure(self):
        """Test _process_elements returns correct structure."""
        parser = DocumentParser()

        # Mock elements
        class MockElement:
            def __init__(self, text, category="paragraph"):
                self.text = text
                self.category = category

            def __str__(self):
                return self.text

        elements = [
            MockElement("First paragraph"),
            MockElement("Second paragraph")
        ]

        result = parser._process_elements(elements, ".txt")

        # Check structure
        assert "text" in result
        assert "elements" in result
        assert "pages" in result
        assert "metadata" in result
        assert "file_type" in result

        assert len(result["elements"]) == 2
        assert result["metadata"]["total_elements"] == 2


class TestDocumentParserIntegration:
    """Integration tests for parser with real documents."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("tests/fixtures/documents/sample.pdf").exists(),
        reason="Sample PDF not found"
    )
    def test_parse_real_pdf(self):
        """TEST-UNIT-001: Parse real PDF document with page extraction."""
        parser = DocumentParser()
        sample_pdf = "tests/fixtures/documents/sample.pdf"

        result = parser.parse(sample_pdf)

        assert result["file_type"] == "pdf"
        assert len(result["text"]) > 0
        assert "pages" in result
        assert result["metadata"]["total_pages"] >= 0

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("tests/fixtures/documents/sample.docx").exists(),
        reason="Sample DOCX not found"
    )
    def test_parse_real_docx(self):
        """TEST-UNIT-002: Parse real DOCX document."""
        parser = DocumentParser()
        sample_docx = "tests/fixtures/documents/sample.docx"

        result = parser.parse(sample_docx)

        assert result["file_type"] == "docx"
        assert len(result["text"]) > 0
        assert result["metadata"]["total_elements"] > 0
