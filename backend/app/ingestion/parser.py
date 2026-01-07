"""
Document parser using Unstructured.io for multi-format support.
Handles PDF, DOCX, Markdown, and plain text files.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.md import partition_md
from unstructured.partition.text import partition_text

logger = logging.getLogger(__name__)


class DocumentParser:
    """Parse documents and extract text with metadata."""

    SUPPORTED_FORMATS = {".pdf", ".docx", ".md", ".txt", ".markdown"}

    def __init__(self):
        """Initialize document parser."""
        pass

    def is_supported(self, file_path: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if format is supported
        """
        suffix = Path(file_path).suffix.lower()
        return suffix in self.SUPPORTED_FORMATS

    def parse(self, file_path: str) -> Dict:
        """
        Parse document and extract structured content.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with:
                - text: Full text content
                - elements: List of structured elements with metadata
                - metadata: Document-level metadata
                - file_type: Detected file type

        Raises:
            ValueError: If file format not supported
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.is_supported(file_path):
            raise ValueError(
                f"Unsupported file format. Supported: {self.SUPPORTED_FORMATS}"
            )

        suffix = Path(file_path).suffix.lower()
        logger.info(f"Parsing document: {file_path} (type: {suffix})")

        try:
            # Parse based on file type
            if suffix == ".pdf":
                elements = partition_pdf(
                    filename=file_path,
                    strategy="auto",  # Use OCR if needed
                    include_page_breaks=True
                )
            elif suffix == ".docx":
                elements = partition_docx(filename=file_path)
            elif suffix in {".md", ".markdown"}:
                elements = partition_md(filename=file_path)
            elif suffix == ".txt":
                elements = partition_text(filename=file_path)
            else:
                # Fallback to auto-detection
                elements = partition(filename=file_path)

            # Extract structured data
            result = self._process_elements(elements, suffix)
            logger.info(
                f"Parsed {len(elements)} elements, "
                f"{len(result['text'])} chars total"
            )

            return result

        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            raise

    def _process_elements(self, elements: List, file_type: str) -> Dict:
        """
        Process parsed elements into structured format.

        Args:
            elements: List of unstructured elements
            file_type: File extension

        Returns:
            Structured document data
        """
        processed_elements = []
        full_text_parts = []
        page_texts = {}  # Map page numbers to text

        for element in elements:
            element_data = {
                "text": str(element),
                "type": element.category if hasattr(element, "category") else "unknown",
                "metadata": {}
            }

            # Extract metadata
            if hasattr(element, "metadata"):
                metadata = element.metadata
                if hasattr(metadata, "page_number"):
                    element_data["metadata"]["page_number"] = metadata.page_number

                    # Build page-wise text
                    page_num = metadata.page_number
                    if page_num not in page_texts:
                        page_texts[page_num] = []
                    page_texts[page_num].append(str(element))

                if hasattr(metadata, "filename"):
                    element_data["metadata"]["filename"] = metadata.filename

                if hasattr(metadata, "filetype"):
                    element_data["metadata"]["filetype"] = metadata.filetype

            processed_elements.append(element_data)
            full_text_parts.append(str(element))

        # Join all text
        full_text = "\n\n".join(full_text_parts)

        # Build page summaries
        pages = []
        for page_num in sorted(page_texts.keys()):
            pages.append({
                "page_number": page_num,
                "text": "\n\n".join(page_texts[page_num])
            })

        return {
            "text": full_text,
            "elements": processed_elements,
            "pages": pages,
            "metadata": {
                "total_elements": len(processed_elements),
                "total_chars": len(full_text),
                "total_pages": len(pages),
                "file_type": file_type
            },
            "file_type": file_type.lstrip(".")
        }

    def extract_text_only(self, file_path: str) -> str:
        """
        Extract just the text content from a document.

        Args:
            file_path: Path to the document

        Returns:
            Plain text content

        Raises:
            ValueError: If file format not supported
            FileNotFoundError: If file doesn't exist
        """
        result = self.parse(file_path)
        return result["text"]
