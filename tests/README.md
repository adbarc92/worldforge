# AetherCanon Builder - Test Suite

Comprehensive test suite for the AetherCanon Builder project.

## Test Structure

```
tests/
├── unit/                    # Unit tests (60% of pyramid)
│   ├── test_parser.py      # Document parser tests
│   ├── test_chunker.py     # Text chunker tests
│   ├── test_embedder.py    # Embedding generator tests
│   └── test_entity_extractor.py  # Entity extraction tests
├── integration/             # Integration tests (30% of pyramid)
│   └── test_documents_api.py     # API endpoint tests
├── performance/             # Performance tests (10% of pyramid)
│   └── (to be added)
├── fixtures/                # Test data and fixtures
│   └── documents/          # Sample documents
└── conftest.py             # Shared fixtures and configuration
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
```

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_parser.py

# Run specific test
pytest tests/unit/test_parser.py::TestDocumentParser::test_parse_markdown_document
```

### By Test Type

```bash
# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v -m integration

# Exclude slow tests
pytest -v -m "not slow"

# Run only fast unit tests
pytest tests/unit -v -m "unit and not slow"
```

### With Coverage

```bash
# Run tests with coverage report
pytest --cov=backend/app --cov-report=html

# View coverage report
open htmlcov/index.html

# Fail if coverage below 70%
pytest --cov=backend/app --cov-fail-under=70
```

### Specific Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only performance tests
pytest -m performance

# Run slow tests
pytest -m slow

# Run async tests
pytest -m asyncio
```

## Test Markers

Tests are marked with pytest markers for easy filtering:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (require services)
- `@pytest.mark.performance` - Performance tests (slow, benchmarks)
- `@pytest.mark.slow` - Slow tests (>5 seconds)
- `@pytest.mark.asyncio` - Async tests

## Coverage Targets

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| parser.py | ≥80% | TBD | 🟡 Pending |
| chunker.py | ≥80% | TBD | 🟡 Pending |
| embedder.py | ≥70% | TBD | 🟡 Pending |
| entity_extractor.py | ≥70% | TBD | 🟡 Pending |
| pipeline.py | ≥70% | TBD | 🟡 Pending |
| **Overall** | **≥70%** | **TBD** | **🟡 Pending** |

## Writing New Tests

### Test Naming Convention

```python
# Test files: test_<module>.py
# Test classes: Test<ClassName>
# Test functions: test_<functionality>

def test_parse_pdf_document():  # Good
    pass

def testParsePDF():  # Bad - doesn't follow convention
    pass
```

### Test Structure (Arrange-Act-Assert)

```python
def test_chunk_text_with_overlap():
    # GIVEN (Arrange)
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = "Sample text..."

    # WHEN (Act)
    chunks = chunker.chunk_text(text)

    # THEN (Assert)
    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)
```

### Async Test Template

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await some_async_function()
    assert result is not None
```

### Mock Example

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value="response")

    with patch('module.get_llm', return_value=mock_llm):
        result = await function_using_llm()
        assert result == "response"
```

## Environment Variables for Testing

```bash
# Required for tests
export ENVIRONMENT=test
export LLM_PROVIDER=claude
export CLAUDE_API_KEY=your-api-key

# Optional (use defaults if not set)
export DATABASE_URL=sqlite:///test_worldforge.db
export CHROMADB_PATH=test_chromadb
```

## Troubleshooting

### Import Errors

```bash
# Add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/backend"

# Or use editable install
pip install -e backend/
```

### Async Test Failures

```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Ensure pytest.ini has asyncio marker configured
```

### Fixture Not Found

```bash
# Check conftest.py is present in test directory
# Fixtures are automatically discovered from conftest.py
```

### Slow Tests Timing Out

```bash
# Increase timeout for slow tests
pytest --timeout=300 tests/

# Or skip slow tests
pytest -m "not slow"
```

## CI/CD Integration

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

### GitHub Actions Workflow

See `.github/workflows/test.yml` for configuration.

**Jobs:**
1. **Lint** - Ruff linting and mypy type checking
2. **Unit Tests** - Fast unit tests with coverage
3. **Integration Tests** - API and workflow tests
4. **Docker Build** - Verify Docker image builds

### Pre-commit Hooks (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Test Data

Sample documents are in `tests/fixtures/documents/`:
- `sample.md` - Middle-earth lore (Markdown)
- More fixtures needed (see fixtures/documents/README.md)

### Creating Test Data

```bash
# Convert markdown to PDF
pandoc tests/fixtures/documents/sample.md -o sample.pdf

# Generate large PDFs for performance testing
python scripts/generate_test_pdfs.py
```

## Performance Benchmarks

Target performance (from requirements):
- Document ingestion: 50 pages in <2 minutes
- Query latency: <5 seconds (p95)
- Entity extraction precision: ≥70%
- Contradiction detection: ≥85%

Run performance tests:
```bash
pytest tests/performance -v -m performance
```

## Test Specifications

See `docs/TEST_SPECIFICATIONS.md` for detailed test specifications and requirements mapping.

## Contributing Tests

When adding new features:
1. Write tests first (TDD)
2. Ensure ≥70% coverage for new code
3. Add integration tests for API endpoints
4. Update this README if adding new test types

## Questions?

- See `docs/TEST_SPECIFICATIONS.md` for detailed specifications
- Check `docs/REQUIREMENTS.md` for requirements
- Review existing tests for examples
