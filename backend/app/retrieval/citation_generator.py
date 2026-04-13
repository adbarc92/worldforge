"""
Citation generation and formatting utilities.
"""

from typing import List, Dict, Any, Optional
import re


class CitationGenerator:
    """
    Generates and formats citations for RAG responses.

    Supports multiple citation formats:
    - Inline citations: [^1], [^2]
    - Footnote format
    - Hover tooltips (for frontend)
    - Expandable source panels
    """

    @staticmethod
    def format_inline_citations(text: str, citations: List[Dict[str, Any]]) -> str:
        """
        Ensure inline citations are properly formatted in text.

        Args:
            text: Text with inline citation markers
            citations: List of citation metadata

        Returns:
            Text with formatted citations
        """
        # Citation markers should already be in text from LLM
        # This method validates and ensures consistency
        for idx, citation in enumerate(citations, start=1):
            marker = f"[^{idx}]"
            if marker not in text:
                # If LLM didn't include citation, we could add it at the end
                # of sentences mentioning the source (advanced feature)
                pass

        return text

    @staticmethod
    def generate_footnotes(citations: List[Dict[str, Any]]) -> List[str]:
        """
        Generate footnote-style citation strings.

        Args:
            citations: List of citation metadata

        Returns:
            List of formatted footnote strings

        Example:
            [^1]: Document Title, Page 5
            [^2]: Another Document, Page 12
        """
        footnotes = []

        for citation in citations:
            number = citation.get("number", 0)
            title = citation.get("document_title", "Unknown Document")
            page = citation.get("page_number")

            if page:
                footnote = f"[^{number}]: {title}, Page {page}"
            else:
                footnote = f"[^{number}]: {title}"

            footnotes.append(footnote)

        return footnotes

    @staticmethod
    def generate_bibliography(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate bibliography entries with full metadata.

        Args:
            citations: List of citation metadata

        Returns:
            List of bibliography entries

        Example:
            [
                {
                    "number": 1,
                    "title": "Document Title",
                    "page": 5,
                    "document_id": "doc-123",
                    "chunk_index": 3
                }
            ]
        """
        bibliography = []

        for citation in citations:
            entry = {
                "number": citation.get("number"),
                "title": citation.get("document_title", "Unknown Document"),
                "document_id": citation.get("document_id"),
                "page": citation.get("page_number"),
                "chunk_index": citation.get("chunk_index")
            }
            bibliography.append(entry)

        return bibliography

    @staticmethod
    def extract_citation_numbers(text: str) -> List[int]:
        """
        Extract citation numbers from text.

        Args:
            text: Text containing inline citations

        Returns:
            List of citation numbers found

        Example:
            "Text with [^1] and [^2] citations" -> [1, 2]
        """
        pattern = r"\[\^(\d+)\]"
        matches = re.findall(pattern, text)
        return [int(m) for m in matches]

    @staticmethod
    def validate_citations(text: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that all citation numbers in text have corresponding metadata.

        Args:
            text: Text with inline citations
            citations: Citation metadata

        Returns:
            Validation results with any issues
        """
        cited_numbers = CitationGenerator.extract_citation_numbers(text)
        available_numbers = [c.get("number") for c in citations]

        missing_metadata = [n for n in cited_numbers if n not in available_numbers]
        unused_metadata = [n for n in available_numbers if n not in cited_numbers]

        return {
            "valid": len(missing_metadata) == 0,
            "cited_numbers": cited_numbers,
            "available_numbers": available_numbers,
            "missing_metadata": missing_metadata,
            "unused_metadata": unused_metadata
        }

    @staticmethod
    def format_for_display(
        answer: str,
        citations: List[Dict[str, Any]],
        format_type: str = "markdown"
    ) -> str:
        """
        Format answer and citations for display.

        Args:
            answer: Answer text with inline citations
            citations: Citation metadata
            format_type: Output format ("markdown", "html", "plain")

        Returns:
            Formatted text ready for display
        """
        if format_type == "markdown":
            return CitationGenerator._format_markdown(answer, citations)
        elif format_type == "html":
            return CitationGenerator._format_html(answer, citations)
        else:
            return CitationGenerator._format_plain(answer, citations)

    @staticmethod
    def _format_markdown(answer: str, citations: List[Dict[str, Any]]) -> str:
        """
        Format as Markdown with footnotes.

        Args:
            answer: Answer text
            citations: Citation metadata

        Returns:
            Markdown formatted text
        """
        footnotes = CitationGenerator.generate_footnotes(citations)

        output = f"{answer}\n\n---\n\n**Sources:**\n\n"
        output += "\n".join(footnotes)

        return output

    @staticmethod
    def _format_html(answer: str, citations: List[Dict[str, Any]]) -> str:
        """
        Format as HTML with hover tooltips.

        Args:
            answer: Answer text
            citations: Citation metadata

        Returns:
            HTML formatted text
        """
        # Replace citation markers with HTML spans with tooltips
        html = answer

        for citation in citations:
            number = citation.get("number")
            title = citation.get("document_title", "Unknown")
            page = citation.get("page_number")

            tooltip = f"{title}"
            if page:
                tooltip += f", Page {page}"

            marker = f"[^{number}]"
            html_marker = f'<sup><a href="#citation-{number}" title="{tooltip}">[{number}]</a></sup>'
            html = html.replace(marker, html_marker)

        # Add footnotes section
        html += '\n\n<hr>\n\n<h4>Sources</h4>\n<ol>\n'

        for citation in citations:
            number = citation.get("number")
            title = citation.get("document_title", "Unknown")
            page = citation.get("page_number")

            source_text = f"{title}"
            if page:
                source_text += f", Page {page}"

            html += f'<li id="citation-{number}">{source_text}</li>\n'

        html += '</ol>\n'

        return html

    @staticmethod
    def _format_plain(answer: str, citations: List[Dict[str, Any]]) -> str:
        """
        Format as plain text with simple references.

        Args:
            answer: Answer text
            citations: Citation metadata

        Returns:
            Plain text formatted output
        """
        output = f"{answer}\n\n"
        output += "=" * 50 + "\n"
        output += "SOURCES:\n"
        output += "=" * 50 + "\n\n"

        for citation in citations:
            number = citation.get("number")
            title = citation.get("document_title", "Unknown")
            page = citation.get("page_number")

            source_text = f"[{number}] {title}"
            if page:
                source_text += f" (Page {page})"

            output += f"{source_text}\n"

        return output

    @staticmethod
    def group_citations_by_document(
        citations: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group citations by source document.

        Args:
            citations: List of citation metadata

        Returns:
            Dict mapping document_id to list of citations from that document
        """
        grouped = {}

        for citation in citations:
            doc_id = citation.get("document_id", "unknown")

            if doc_id not in grouped:
                grouped[doc_id] = []

            grouped[doc_id].append(citation)

        return grouped

    @staticmethod
    def generate_citation_summary(citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics about citations.

        Args:
            citations: List of citation metadata

        Returns:
            Summary statistics
        """
        if not citations:
            return {
                "total_citations": 0,
                "unique_documents": 0,
                "documents": []
            }

        unique_docs = set()
        doc_titles = {}

        for citation in citations:
            doc_id = citation.get("document_id")
            doc_title = citation.get("document_title")

            if doc_id:
                unique_docs.add(doc_id)
                if doc_id not in doc_titles:
                    doc_titles[doc_id] = doc_title

        documents = [
            {"id": doc_id, "title": doc_titles.get(doc_id, "Unknown")}
            for doc_id in unique_docs
        ]

        return {
            "total_citations": len(citations),
            "unique_documents": len(unique_docs),
            "documents": documents
        }

    @staticmethod
    def create_expandable_citation(
        citation: Dict[str, Any],
        chunk_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an expandable citation object for frontend display.

        Args:
            citation: Citation metadata
            chunk_text: Optional full chunk text for preview

        Returns:
            Expandable citation object
        """
        expandable = {
            "number": citation.get("number"),
            "title": citation.get("document_title", "Unknown Document"),
            "document_id": citation.get("document_id"),
            "page": citation.get("page_number"),
            "chunk_index": citation.get("chunk_index"),
            "preview": chunk_text[:200] + "..." if chunk_text and len(chunk_text) > 200 else chunk_text,
            "full_text": chunk_text
        }

        return expandable
