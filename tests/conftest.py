"""
Pytest configuration and shared fixtures.
"""

import os
import sys
import asyncio
import pytest
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Configure test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["LLM_PROVIDER"] = "claude"  # or mock
os.environ["DATABASE_URL"] = "sqlite:///test_worldforge.db"
os.environ["CHROMADB_PATH"] = "test_chromadb"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "fixtures" / "documents"


@pytest.fixture
def sample_text():
    """Return sample text for testing."""
    return """
    Aragorn, son of Arathorn, was the heir to the throne of Gondor.
    He was raised in Rivendell by Elrond after his father's death.
    As a Ranger of the North, he protected the Shire from danger.
    He wielded the sword Andúril, reforged from the shards of Narsil.
    """


@pytest.fixture
def sample_markdown():
    """Return sample markdown content."""
    return """# Test Document

## Characters

- **Aragorn**: The heir to Gondor's throne
- **Gandalf**: A wizard of great power

## Locations

- **Rivendell**: An elven refuge in Middle-earth
- **The Shire**: Home of the hobbits

## Events

- **The Council of Elrond**: A meeting to decide the Ring's fate
"""


@pytest.fixture
def sample_entities():
    """Return sample entity data."""
    return [
        {
            "name": "Aragorn",
            "type": "character",
            "description": "Heir to the throne of Gondor",
            "confidence": 0.95,
            "source_document_id": "test-doc-123",
            "source_chunk_index": 0,
            "source_page_number": 1
        },
        {
            "name": "Rivendell",
            "type": "location",
            "description": "An elven refuge",
            "confidence": 0.88,
            "source_document_id": "test-doc-123",
            "source_chunk_index": 1,
            "source_page_number": 1
        },
        {
            "name": "Andúril",
            "type": "item",
            "description": "Aragorn's reforged sword",
            "confidence": 0.82,
            "source_document_id": "test-doc-123",
            "source_chunk_index": 0,
            "source_page_number": 1
        }
    ]


@pytest.fixture
async def test_db():
    """Provide test database session."""
    from backend.app.database.connection import async_engine, AsyncSessionLocal
    from backend.app.database.models import Base

    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with AsyncSessionLocal() as session:
        yield session

    # Cleanup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_llm_response():
    """Return mock LLM response for entity extraction."""
    return [
        {
            "name": "Aragorn",
            "type": "character",
            "description": "The heir to the throne of Gondor",
            "confidence": 0.95
        },
        {
            "name": "Rivendell",
            "type": "location",
            "description": "An elven refuge in Middle-earth",
            "confidence": 0.88
        }
    ]


@pytest.fixture
def cleanup_test_files():
    """Cleanup test files after tests."""
    test_files = []

    def register_file(filepath):
        test_files.append(filepath)
        return filepath

    yield register_file

    # Cleanup
    for filepath in test_files:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
