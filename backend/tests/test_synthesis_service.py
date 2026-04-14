import json

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.synthesis_service import SynthesisService


@pytest.fixture
def mock_llm_service():
    return AsyncMock()


@pytest.fixture
def mock_qdrant_service():
    return AsyncMock()


@pytest.fixture
def mock_contradiction_repo():
    return AsyncMock()


@pytest.fixture
def mock_synthesis_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_llm_service, mock_qdrant_service, mock_contradiction_repo, mock_synthesis_repo):
    return SynthesisService(
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service,
        contradiction_repo=mock_contradiction_repo,
        synthesis_repo=mock_synthesis_repo,
    )


@pytest.mark.asyncio
async def test_gate_check_blocks_with_open_contradictions(service, mock_contradiction_repo):
    mock_contradiction_repo.count.return_value = 3
    with pytest.raises(ValueError, match="contradictions"):
        await service.check_gate("proj-1")
    mock_contradiction_repo.count.assert_called_once_with("proj-1", status="open")


@pytest.mark.asyncio
async def test_gate_check_passes_with_no_open_contradictions(service, mock_contradiction_repo):
    mock_contradiction_repo.count.return_value = 0
    await service.check_gate("proj-1")  # Should not raise


@pytest.mark.asyncio
async def test_generate_outline_returns_sections(service, mock_llm_service, mock_qdrant_service):
    # Simulate 2 chunks (single batch)
    mock_qdrant_service.search_by_filter.return_value = [
        {"id": "c1", "text": "The world began in fire.", "document_id": "d1", "title": "Creation", "project_id": "proj-1"},
        {"id": "c2", "text": "The Elders founded the Council.", "document_id": "d1", "title": "Creation", "project_id": "proj-1"},
    ]

    outline_json = json.dumps([
        {"title": "Cosmogony", "description": "How the world was created"},
        {"title": "Factions", "description": "Major political groups"},
    ])

    # First call: topic extraction; Second call: consolidation
    mock_llm_service.generate.side_effect = [
        "Cosmogony, Factions, Key Events",
        outline_json,
    ]

    result = await service.generate_outline("proj-1")

    assert len(result) == 2
    assert result[0]["title"] == "Cosmogony"
    assert result[1]["title"] == "Factions"
    assert result[1]["description"] == "Major political groups"


@pytest.mark.asyncio
async def test_generate_outline_handles_markdown_json(service, mock_llm_service, mock_qdrant_service):
    mock_qdrant_service.search_by_filter.return_value = [
        {"id": "c1", "text": "Some lore text.", "document_id": "d1", "title": "Lore", "project_id": "proj-1"},
    ]

    outline_json = json.dumps([
        {"title": "Geography", "description": "The lands and seas"},
    ])
    markdown_wrapped = f"```json\n{outline_json}\n```"

    mock_llm_service.generate.side_effect = [
        "Geography",
        markdown_wrapped,
    ]

    result = await service.generate_outline("proj-1")

    assert len(result) == 1
    assert result[0]["title"] == "Geography"


@pytest.mark.asyncio
async def test_generate_section_includes_resolution_notes(
    service, mock_llm_service, mock_qdrant_service, mock_contradiction_repo
):
    # Mock embedding + search
    mock_llm_service.embed.return_value = [[0.1, 0.2, 0.3]]
    mock_qdrant_service.search.return_value = [
        {"id": "c1", "score": 0.95, "payload": {"text": "The king rules the north.", "document_id": "d1", "title": "Politics"}},
    ]

    # Mock resolved contradiction with a resolution note
    resolved_contradiction = MagicMock()
    resolved_contradiction.resolution_note = "Version 2 is canon"
    resolved_contradiction.chunk_a_text = "The king rules the north lands and mountains beyond"
    resolved_contradiction.chunk_b_text = "The queen rules the north lands and mountains beyond"
    mock_contradiction_repo.list.return_value = [resolved_contradiction]

    mock_llm_service.generate.return_value = "The northern realm is governed by a wise monarch."

    section = {"title": "Governance", "description": "Political structure"}
    result = await service.generate_section("proj-1", section)

    assert result == "The northern realm is governed by a wise monarch."

    # Verify the LLM prompt included resolution notes
    call_args = mock_llm_service.generate.call_args
    prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
    assert "Version 2 is canon" in prompt


@pytest.mark.asyncio
async def test_generate_section_works_without_resolution_notes(
    service, mock_llm_service, mock_qdrant_service, mock_contradiction_repo
):
    mock_llm_service.embed.return_value = [[0.1, 0.2, 0.3]]
    mock_qdrant_service.search.return_value = [
        {"id": "c1", "score": 0.9, "payload": {"text": "Dragons once roamed.", "document_id": "d1", "title": "Beasts"}},
    ]
    mock_contradiction_repo.list.return_value = []
    mock_llm_service.generate.return_value = "In ancient times, great dragons soared above."

    section = {"title": "Creatures", "description": "Beasts of the world"}
    result = await service.generate_section("proj-1", section)

    assert result == "In ancient times, great dragons soared above."


def test_assemble_document(service):
    sections = [
        {"title": "Cosmogony", "content": "The world began in fire."},
        {"title": "Factions", "content": "Three great houses emerged."},
    ]
    document = service.assemble_document(sections)

    assert "# Cosmogony" in document
    assert "The world began in fire." in document
    assert "# Factions" in document
    assert "Three great houses emerged." in document
    assert "---" in document
