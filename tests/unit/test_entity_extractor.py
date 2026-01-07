"""
Unit tests for entity extractor.
Tests: TEST-UNIT-012 through TEST-UNIT-014
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.ingestion.entity_extractor import EntityExtractor


class TestEntityExtractor:
    """Test suite for EntityExtractor class."""

    def test_extractor_initialization(self):
        """Test entity extractor can be initialized."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()
            assert extractor is not None
            assert hasattr(extractor, 'ENTITY_TYPES')

    def test_entity_types_defined(self):
        """Test that entity types are properly defined."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()
            expected_types = {"character", "location", "event", "concept", "item"}
            assert extractor.ENTITY_TYPES == expected_types

    # TEST-UNIT-012: Extract Entities from Text
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_entities_from_text(self, mock_llm_response):
        """Test entity extraction from sample text."""
        # Mock LLM provider
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=mock_llm_response)

        with patch('backend.app.ingestion.entity_extractor.get_llm_provider', return_value=mock_llm):
            extractor = EntityExtractor()

            text = """
            Aragorn, the ranger from the North, traveled to Rivendell,
            an elven city in Middle-earth. He wielded the sword Andúril.
            """
            document_id = "test-doc-123"

            entities = await extractor.extract_entities(text, document_id)

            # Assertions
            assert len(entities) > 0

            # Entities should have required fields
            for entity in entities:
                assert "name" in entity
                assert "type" in entity
                assert entity["type"] in extractor.ENTITY_TYPES
                assert "confidence" in entity
                assert 0 <= entity["confidence"] <= 1
                assert entity["source_document_id"] == document_id

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_entities_empty_text(self):
        """Test extraction handles empty text gracefully."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            entities = await extractor.extract_entities("", "doc-123")

            assert entities == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_entities_with_chunk_info(self):
        """Test extraction includes chunk information."""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=[
            {"name": "Gandalf", "type": "character", "description": "A wizard", "confidence": 0.9}
        ])

        with patch('backend.app.ingestion.entity_extractor.get_llm_provider', return_value=mock_llm):
            extractor = EntityExtractor()

            chunk_info = {
                "chunk_index": 5,
                "page_number": 3
            }

            entities = await extractor.extract_entities(
                "Gandalf was a wizard",
                "doc-123",
                chunk_info=chunk_info
            )

            assert len(entities) > 0
            assert entities[0]["source_chunk_index"] == 5
            assert entities[0]["source_page_number"] == 3

    # TEST-UNIT-013: Entity Deduplication
    @pytest.mark.unit
    def test_entity_deduplication(self):
        """Test that duplicate entities are merged."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            entities = [
                {
                    "name": "Aragorn",
                    "type": "character",
                    "description": "Ranger",
                    "confidence": 0.8,
                    "source_document_id": "doc-123"
                },
                {
                    "name": "aragorn",  # Duplicate (different case)
                    "type": "character",
                    "description": "King",
                    "confidence": 0.9,
                    "source_document_id": "doc-123"
                },
                {
                    "name": "Gandalf",
                    "type": "character",
                    "description": "Wizard",
                    "confidence": 0.85,
                    "source_document_id": "doc-123"
                }
            ]

            deduplicated = extractor._deduplicate_entities(entities)

            # Should keep only 2 entities
            assert len(deduplicated) == 2

            # Should keep the higher confidence version of Aragorn
            aragorn = next((e for e in deduplicated if e["name"].lower() == "aragorn"), None)
            assert aragorn is not None
            assert aragorn["confidence"] == 0.9

    @pytest.mark.unit
    def test_deduplication_case_insensitive(self):
        """Test deduplication is case-insensitive."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            entities = [
                {"name": "RIVENDELL", "type": "location", "confidence": 0.7, "description": "City", "source_document_id": "doc-1"},
                {"name": "Rivendell", "type": "location", "confidence": 0.8, "description": "City", "source_document_id": "doc-1"},
                {"name": "rivendell", "type": "location", "confidence": 0.9, "description": "City", "source_document_id": "doc-1"}
            ]

            deduplicated = extractor._deduplicate_entities(entities)

            assert len(deduplicated) == 1
            assert deduplicated[0]["confidence"] == 0.9  # Highest

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_entities_from_chunks(self, mock_llm_response):
        """Test extracting entities from multiple chunks."""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=mock_llm_response)

        with patch('backend.app.ingestion.entity_extractor.get_llm_provider', return_value=mock_llm):
            extractor = EntityExtractor()

            chunks = [
                {"text": "Chunk 1 about Aragorn", "chunk_index": 0, "metadata": {}},
                {"text": "Chunk 2 about Rivendell", "chunk_index": 1, "metadata": {"page_number": 2}}
            ]

            entities = await extractor.extract_entities_from_chunks(
                chunks,
                "doc-123"
            )

            # Should have extracted from multiple chunks
            assert len(entities) > 0
            assert mock_llm.generate_structured.call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_entities_max_chunks_limit(self, mock_llm_response):
        """Test extraction respects max_chunks parameter."""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=mock_llm_response)

        with patch('backend.app.ingestion.entity_extractor.get_llm_provider', return_value=mock_llm):
            extractor = EntityExtractor()

            chunks = [
                {"text": f"Chunk {i}", "chunk_index": i, "metadata": {}}
                for i in range(10)
            ]

            entities = await extractor.extract_entities_from_chunks(
                chunks,
                "doc-123",
                max_chunks=3
            )

            # Should only process 3 chunks
            assert mock_llm.generate_structured.call_count == 3

    def test_validate_and_enrich_entity(self):
        """Test entity validation and enrichment."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            entity_data = {
                "name": "Frodo",
                "type": "character",
                "description": "A hobbit",
                "confidence": 0.95
            }

            chunk_info = {"chunk_index": 2, "page_number": 5}

            enriched = extractor._validate_and_enrich_entity(
                entity_data,
                "doc-456",
                chunk_info
            )

            assert enriched is not None
            assert enriched["name"] == "Frodo"
            assert enriched["source_document_id"] == "doc-456"
            assert enriched["source_chunk_index"] == 2
            assert enriched["source_page_number"] == 5

    def test_validate_entity_missing_name(self):
        """Test validation rejects entity without name."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            entity_data = {
                "type": "character",
                "description": "A hobbit"
            }

            enriched = extractor._validate_and_enrich_entity(
                entity_data,
                "doc-456",
                None
            )

            assert enriched is None

    def test_validate_entity_invalid_type(self):
        """Test validation rejects invalid entity type."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            entity_data = {
                "name": "Invalid",
                "type": "invalid_type",  # Not in ENTITY_TYPES
                "description": "Test"
            }

            enriched = extractor._validate_and_enrich_entity(
                entity_data,
                "doc-456",
                None
            )

            assert enriched is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_entities_handles_llm_error(self):
        """Test extraction handles LLM errors gracefully."""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(side_effect=Exception("LLM Error"))

        with patch('backend.app.ingestion.entity_extractor.get_llm_provider', return_value=mock_llm):
            extractor = EntityExtractor()

            entities = await extractor.extract_entities(
                "Some text",
                "doc-123"
            )

            # Should return empty list on error, not raise
            assert entities == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_entities_truncates_long_text(self):
        """Test extraction truncates very long text."""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=[])

        with patch('backend.app.ingestion.entity_extractor.get_llm_provider', return_value=mock_llm):
            extractor = EntityExtractor()

            # Create text longer than 4000 chars
            long_text = "Lorem ipsum " * 500  # ~6000 chars

            await extractor.extract_entities(long_text, "doc-123")

            # Verify LLM was called (text should be truncated, not rejected)
            assert mock_llm.generate_structured.called

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_relationships_not_implemented(self):
        """Test relationship extraction placeholder."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            relationships = await extractor.extract_relationships(
                [],
                "Some text",
                "doc-123"
            )

            # Currently returns empty list (not implemented in MVP)
            assert relationships == []


class TestEntityTypes:
    """Test entity type validation."""

    @pytest.mark.unit
    def test_all_valid_entity_types(self):
        """Test all entity types are recognized."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            valid_types = ["character", "location", "event", "concept", "item"]

            for entity_type in valid_types:
                assert entity_type in extractor.ENTITY_TYPES

    @pytest.mark.unit
    def test_invalid_entity_type(self):
        """Test invalid entity types are rejected."""
        with patch('backend.app.ingestion.entity_extractor.get_llm_provider'):
            extractor = EntityExtractor()

            invalid_types = ["person", "place", "thing", "other"]

            for entity_type in invalid_types:
                assert entity_type not in extractor.ENTITY_TYPES
