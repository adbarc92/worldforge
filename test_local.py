#!/usr/bin/env python3
"""
Local testing script for AetherCanon Builder.
Tests basic functionality without heavy dependencies (ChromaDB, embeddings, LLMs).
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that core modules can be imported."""
    print("=" * 60)
    print("TEST 1: Importing Core Modules")
    print("=" * 60)

    try:
        from backend.app.database.models import Document, Entity, Chunk, Relationship, ProposedContent, Conflict
        print("✓ Database models imported")
    except Exception as e:
        print(f"✗ Database models failed: {e}")
        return False

    try:
        from backend.app.config import settings
        print("✓ Configuration imported")
        print(f"  - Environment: {settings.environment}")
        print(f"  - Database: {settings.database_url}")
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False

    try:
        from backend.app.api.schemas import (
            DocumentResponse, QueryRequest, ConflictResponse,
            ReviewQueueResponse, ExportRequest
        )
        print("✓ API schemas imported")
    except Exception as e:
        print(f"✗ API schemas failed: {e}")
        return False

    print("\n✓ All core imports successful!\n")
    return True


def test_database_models():
    """Test that database models are correctly defined."""
    print("=" * 60)
    print("TEST 2: Database Models")
    print("=" * 60)

    try:
        from backend.app.database.models import Document, Entity, Base
        from sqlalchemy import inspect

        # Check Document table
        doc_columns = [c.name for c in inspect(Document).columns]
        print(f"✓ Document model has {len(doc_columns)} columns:")
        print(f"  {', '.join(doc_columns)}")

        # Check Entity table
        entity_columns = [c.name for c in inspect(Entity).columns]
        print(f"✓ Entity model has {len(entity_columns)} columns:")
        print(f"  {', '.join(entity_columns)}")

        # Verify metadata column exists (as database column)
        # but Python attribute is extra_metadata to avoid SQLAlchemy Base.metadata conflict
        assert 'metadata' in doc_columns, "Document should have metadata column in database"
        assert hasattr(Document, 'extra_metadata'), "Document should have extra_metadata Python attribute"
        print("✓ SQLAlchemy metadata conflict resolved (DB column: 'metadata', Python attr: 'extra_metadata')")

        print("\n✓ Database models are correctly defined!\n")
        return True
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_app():
    """Test that FastAPI app can be created (without heavy dependencies)."""
    print("=" * 60)
    print("TEST 3: FastAPI Application Structure")
    print("=" * 60)

    try:
        # Note: This will fail if we try to actually import routes that use
        # ChromaDB, embeddings, etc. But we can test the basic structure.
        from fastapi import FastAPI
        from backend.app.api import schemas

        # Create a minimal test app
        app = FastAPI(title="Test App")
        print("✓ FastAPI app can be created")

        # Test schemas
        test_request = schemas.QueryRequest(query="test", top_k=5)
        print(f"✓ QueryRequest schema works: {test_request.query}")

        print("\n✓ FastAPI structure is valid!\n")
        return True
    except Exception as e:
        print(f"✗ FastAPI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """Test that database can be initialized."""
    print("=" * 60)
    print("TEST 4: Database Connection")
    print("=" * 60)

    try:
        from backend.app.database.models import Base
        from sqlalchemy import create_engine

        # Create in-memory SQLite database for testing
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        tables = Base.metadata.tables.keys()
        print(f"✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        print("\n✓ Database initialization successful!\n")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  AetherCanon Builder - Local Testing Suite".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    tests = [
        ("Imports", test_imports),
        ("Database Models", test_database_models),
        ("FastAPI Structure", test_fastapi_app),
        ("Database Connection", test_database_connection),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}\n")
            results.append((name, False))

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Core structure is valid.")
        print("\nNote: This tests basic structure only.")
        print("Full functionality requires:")
        print("  - ChromaDB (vector database)")
        print("  - sentence-transformers (embeddings)")
        print("  - llama-index (RAG framework)")
        print("  - LLM provider (Claude API or Ollama)")
        print("\nThese dependencies require Python 3.11 or Docker.")
        return 0
    else:
        print("\n❌ Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
