# AetherCanon Builder - Test Specifications
**Version:** 1.0
**Based on:** REQUIREMENTS.md v1.0
**Last Updated:** January 6, 2026

---

## 1. Testing Strategy Overview

### 1.1 Test Pyramid

```
                    /\
                   /  \
                  / E2E \ ──────── 10% (Critical user paths)
                 /______\
                /        \
               / Integration \ ──── 30% (API endpoints, workflows)
              /______________\
             /                \
            /   Unit Tests     \ ── 60% (Functions, classes, modules)
           /____________________\
```

### 1.2 Coverage Targets

| Test Type | Target Coverage | Current | Status |
|-----------|----------------|---------|--------|
| Unit Tests | ≥70% | 0% | ⚠️ Not Started |
| Integration Tests | All API endpoints | 0% | ⚠️ Not Started |
| E2E Tests | 5 critical paths | 0% | ⚠️ Not Started |
| Performance Tests | All NFRs | 0% | ⚠️ Not Started |

### 1.3 Test Environment

**Development:**
- Local Docker Compose setup
- SQLite for fast test execution
- Mocked LLM responses for speed

**CI/CD:**
- GitHub Actions
- Docker containers
- Test database fixtures
- Mocked external APIs

**Staging:**
- Full Docker Compose stack
- Real LLM (Ollama with small model)
- Real embeddings (BGE-small for speed)

---

## 2. Unit Test Specifications

### 2.1 Document Parser Tests
**Module:** `backend/app/ingestion/parser.py`
**Coverage Target:** ≥80%

#### TEST-UNIT-001: Parse PDF Document
**Requirements:** FR-1.1, FR-1.2
**Priority:** P0

```python
def test_parse_pdf_document():
    """Test PDF document parsing with page extraction."""
    # GIVEN
    parser = DocumentParser()
    sample_pdf = "tests/fixtures/sample_10_pages.pdf"

    # WHEN
    result = parser.parse(sample_pdf)

    # THEN
    assert result["file_type"] == "pdf"
    assert len(result["text"]) > 0
    assert len(result["pages"]) == 10
    assert result["metadata"]["total_pages"] == 10
    assert all("page_number" in page for page in result["pages"])
```

#### TEST-UNIT-002: Parse DOCX Document
**Requirements:** FR-1.1
**Priority:** P0

```python
def test_parse_docx_document():
    """Test DOCX document parsing."""
    # GIVEN
    parser = DocumentParser()
    sample_docx = "tests/fixtures/sample.docx"

    # WHEN
    result = parser.parse(sample_docx)

    # THEN
    assert result["file_type"] == "docx"
    assert len(result["text"]) > 0
    assert result["metadata"]["total_elements"] > 0
```

#### TEST-UNIT-003: Parse Markdown Document
**Requirements:** FR-1.1
**Priority:** P0

```python
def test_parse_markdown_document():
    """Test Markdown document parsing with headings."""
    # GIVEN
    parser = DocumentParser()
    sample_md = "tests/fixtures/sample.md"

    # WHEN
    result = parser.parse(sample_md)

    # THEN
    assert result["file_type"] == "md"
    assert len(result["text"]) > 0
    # Should preserve headings and structure
```

#### TEST-UNIT-004: Reject Unsupported Format
**Requirements:** FR-1.1
**Priority:** P0

```python
def test_reject_unsupported_format():
    """Test that unsupported formats are rejected."""
    # GIVEN
    parser = DocumentParser()
    unsupported_file = "tests/fixtures/sample.xlsx"

    # WHEN/THEN
    with pytest.raises(ValueError, match="Unsupported file format"):
        parser.parse(unsupported_file)
```

#### TEST-UNIT-005: Handle Missing File
**Requirements:** NFR-4.2 (Error Handling)
**Priority:** P1

```python
def test_handle_missing_file():
    """Test error handling for non-existent files."""
    # GIVEN
    parser = DocumentParser()
    missing_file = "tests/fixtures/nonexistent.pdf"

    # WHEN/THEN
    with pytest.raises(FileNotFoundError):
        parser.parse(missing_file)
```

---

### 2.2 Text Chunker Tests
**Module:** `backend/app/ingestion/chunker.py`
**Coverage Target:** ≥80%

#### TEST-UNIT-006: Chunk Text with Overlap
**Requirements:** FR-1.2
**Priority:** P0

```python
def test_chunk_text_with_overlap():
    """Test text chunking with specified overlap."""
    # GIVEN
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = "Lorem ipsum " * 200  # Long text

    # WHEN
    chunks = chunker.chunk_text(text)

    # THEN
    assert len(chunks) > 1
    assert all("text" in chunk for chunk in chunks)
    assert all("chunk_index" in chunk for chunk in chunks)
    # Verify overlap exists between consecutive chunks
    if len(chunks) > 1:
        chunk1_end = chunks[0]["text"][-50:]
        chunk2_start = chunks[1]["text"][:50]
        # Some overlap should exist
```

#### TEST-UNIT-007: Chunk Empty Text
**Requirements:** NFR-4.2
**Priority:** P1

```python
def test_chunk_empty_text():
    """Test chunking handles empty text gracefully."""
    # GIVEN
    chunker = TextChunker()

    # WHEN
    chunks = chunker.chunk_text("")

    # THEN
    assert chunks == []
```

#### TEST-UNIT-008: Chunk Document with Pages
**Requirements:** FR-1.2
**Priority:** P0

```python
def test_chunk_document_with_pages():
    """Test chunking preserves page metadata."""
    # GIVEN
    chunker = TextChunker()
    parsed_doc = {
        "text": "Full text here",
        "pages": [
            {"page_number": 1, "text": "Page 1 content"},
            {"page_number": 2, "text": "Page 2 content"}
        ],
        "file_type": "pdf"
    }
    document_id = "test-doc-123"

    # WHEN
    chunks = chunker.chunk_document(parsed_doc, document_id)

    # THEN
    assert len(chunks) > 0
    assert all("metadata" in chunk for chunk in chunks)
    assert all(chunk["metadata"]["document_id"] == document_id
               for chunk in chunks)
```

---

### 2.3 Embedder Tests
**Module:** `backend/app/ingestion/embedder.py`
**Coverage Target:** ≥70%

#### TEST-UNIT-009: Generate Single Embedding
**Requirements:** FR-1.2, TR-2.3
**Priority:** P0

```python
def test_generate_single_embedding():
    """Test embedding generation for single text."""
    # GIVEN
    embedder = get_embedder()
    text = "This is a test sentence for embedding."

    # WHEN
    embedding = embedder.embed(text)

    # THEN
    assert isinstance(embedding, list)
    assert len(embedding) == 1024  # BGE-large-en-v1.5 dimension
    assert all(isinstance(x, float) for x in embedding)
```

#### TEST-UNIT-010: Generate Batch Embeddings
**Requirements:** FR-1.2
**Priority:** P0

```python
def test_generate_batch_embeddings():
    """Test batch embedding generation."""
    # GIVEN
    embedder = get_embedder()
    texts = ["Text one", "Text two", "Text three"]

    # WHEN
    embeddings = embedder.embed_batch(texts, show_progress=False)

    # THEN
    assert len(embeddings) == 3
    assert all(len(emb) == 1024 for emb in embeddings)
```

#### TEST-UNIT-011: Embedding Similarity
**Requirements:** FR-3.1 (Similarity Search)
**Priority:** P0

```python
def test_embedding_similarity():
    """Test that similar texts have similar embeddings."""
    # GIVEN
    embedder = get_embedder()
    text1 = "The quick brown fox jumps over the lazy dog."
    text2 = "A fast brown fox leaps over a sleepy dog."
    text3 = "Python is a programming language."

    # WHEN
    emb1 = embedder.embed(text1)
    emb2 = embedder.embed(text2)
    emb3 = embedder.embed(text3)

    # THEN
    from numpy import dot
    from numpy.linalg import norm

    def cosine_sim(a, b):
        return dot(a, b) / (norm(a) * norm(b))

    sim_1_2 = cosine_sim(emb1, emb2)
    sim_1_3 = cosine_sim(emb1, emb3)

    # Similar texts should be more similar than dissimilar texts
    assert sim_1_2 > sim_1_3
    assert sim_1_2 > 0.7  # Should be quite similar
```

---

### 2.4 Entity Extractor Tests
**Module:** `backend/app/ingestion/entity_extractor.py`
**Coverage Target:** ≥70%

#### TEST-UNIT-012: Extract Entities from Text
**Requirements:** FR-1.3
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_extract_entities_from_text():
    """Test entity extraction from sample text."""
    # GIVEN
    extractor = EntityExtractor()
    text = """
    Aragorn, the ranger from the North, traveled to Rivendell,
    an elven city in Middle-earth. He wielded the sword Andúril.
    """
    document_id = "test-doc-123"

    # WHEN
    entities = await extractor.extract_entities(text, document_id)

    # THEN
    assert len(entities) > 0

    # Should extract at least a character and location
    entity_types = [e["type"] for e in entities]
    assert "character" in entity_types or "location" in entity_types

    # Entities should have required fields
    for entity in entities:
        assert "name" in entity
        assert "type" in entity
        assert entity["type"] in {"character", "location", "event", "concept", "item"}
        assert "confidence" in entity
        assert 0 <= entity["confidence"] <= 1
```

#### TEST-UNIT-013: Entity Deduplication
**Requirements:** FR-1.3
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_entity_deduplication():
    """Test that duplicate entities are merged."""
    # GIVEN
    extractor = EntityExtractor()
    entities = [
        {"name": "Aragorn", "type": "character", "confidence": 0.8},
        {"name": "aragorn", "type": "character", "confidence": 0.9},  # Duplicate (case)
        {"name": "Gandalf", "type": "character", "confidence": 0.85}
    ]

    # WHEN
    deduplicated = extractor._deduplicate_entities(entities)

    # THEN
    assert len(deduplicated) == 2
    # Should keep the higher confidence version
    aragorn = next(e for e in deduplicated if e["name"].lower() == "aragorn")
    assert aragorn["confidence"] == 0.9
```

#### TEST-UNIT-014: Extract Entities with Precision Target
**Requirements:** FR-1.3 (≥70% precision)
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_entity_extraction_precision():
    """Test entity extraction meets precision target on annotated corpus."""
    # GIVEN
    extractor = EntityExtractor()

    # Load annotated test corpus
    test_corpus = load_test_corpus("tests/fixtures/annotated_corpus.json")

    true_positives = 0
    false_positives = 0

    # WHEN
    for sample in test_corpus:
        extracted = await extractor.extract_entities(
            sample["text"],
            sample["document_id"]
        )
        ground_truth = sample["entities"]

        # Compare extracted vs ground truth
        for entity in extracted:
            if is_match(entity, ground_truth):
                true_positives += 1
            else:
                false_positives += 1

    # THEN
    precision = true_positives / (true_positives + false_positives)
    assert precision >= 0.70, f"Precision {precision:.2%} < 70% target"
```

---

### 2.5 LLM Provider Tests
**Module:** `backend/app/llm/provider.py`, `claude_provider.py`, `ollama_provider.py`
**Coverage Target:** ≥60%

#### TEST-UNIT-015: Get LLM Provider (Claude)
**Requirements:** TR-2.3
**Priority:** P0

```python
def test_get_llm_provider_claude(monkeypatch):
    """Test LLM provider factory returns Claude when configured."""
    # GIVEN
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")

    # WHEN
    from backend.app.llm.provider import get_llm_provider
    provider = get_llm_provider()

    # THEN
    from backend.app.llm.claude_provider import ClaudeProvider
    assert isinstance(provider, ClaudeProvider)
```

#### TEST-UNIT-016: Generate Text with Claude
**Requirements:** TR-2.3
**Priority:** P1

```python
@pytest.mark.asyncio
@pytest.mark.integration  # Requires API key
async def test_generate_text_claude():
    """Test text generation with Claude provider."""
    # GIVEN
    from backend.app.llm.claude_provider import ClaudeProvider
    provider = ClaudeProvider(
        api_key=os.getenv("CLAUDE_API_KEY"),
        model="claude-3-5-sonnet-20241022"
    )

    # WHEN
    response = await provider.generate("Say 'Hello, World!' exactly.")

    # THEN
    assert "Hello, World!" in response
```

#### TEST-UNIT-017: Generate Structured JSON
**Requirements:** FR-1.3
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_generate_structured_json(mock_llm):
    """Test structured JSON generation."""
    # GIVEN
    provider = mock_llm
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        }
    }

    # WHEN
    result = await provider.generate_structured(
        "Extract name and age",
        schema
    )

    # THEN
    assert "name" in result
    assert "age" in result
    assert isinstance(result["age"], (int, float))
```

---

## 3. Integration Test Specifications

### 3.1 Document Upload API Tests
**Endpoint:** `POST /api/documents/upload`
**Coverage Target:** All success and error paths

#### TEST-INT-001: Upload PDF Document
**Requirements:** FR-1, TR-4.1
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_upload_pdf_document(test_client, sample_pdf):
    """Test complete PDF upload workflow."""
    # GIVEN
    files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
    params = {"title": "Test Document", "extract_entities": True}

    # WHEN
    response = await test_client.post(
        "/api/documents/upload",
        files=files,
        params=params
    )

    # THEN
    assert response.status_code == 200
    data = response.json()

    assert "document" in data
    assert data["document"]["title"] == "Test Document"
    assert data["chunks_created"] > 0
    assert data["entities_extracted"] >= 0
    assert data["processing_time_seconds"] > 0
```

#### TEST-INT-002: Upload Without Entity Extraction
**Requirements:** FR-1
**Priority:** P1

```python
@pytest.mark.asyncio
async def test_upload_without_entity_extraction(test_client, sample_pdf):
    """Test upload with entity extraction disabled."""
    # GIVEN
    files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
    params = {"extract_entities": False}

    # WHEN
    response = await test_client.post(
        "/api/documents/upload",
        files=files,
        params=params
    )

    # THEN
    assert response.status_code == 200
    data = response.json()
    assert data["entities_extracted"] == 0
    assert data["chunks_created"] > 0
```

#### TEST-INT-003: Reject Unsupported File Type
**Requirements:** FR-1.1, NFR-4.2
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_reject_unsupported_file_type(test_client):
    """Test API rejects unsupported file formats."""
    # GIVEN
    files = {"file": ("test.xlsx", b"fake excel data", "application/vnd.ms-excel")}

    # WHEN
    response = await test_client.post("/api/documents/upload", files=files)

    # THEN
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
```

#### TEST-INT-004: Upload Creates Database Records
**Requirements:** FR-1.2, DR-1
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_upload_creates_database_records(test_client, sample_pdf, test_db):
    """Test upload creates correct database records."""
    # GIVEN
    files = {"file": ("test.pdf", sample_pdf, "application/pdf")}

    # WHEN
    response = await test_client.post("/api/documents/upload", files=files)
    document_id = response.json()["document"]["id"]

    # THEN
    from sqlalchemy import select
    from backend.app.database.models import Document, Chunk, ProposedContent

    # Check document record
    doc = await test_db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = doc.scalar_one()
    assert doc.status == "active"
    assert doc.chunk_count > 0

    # Check chunks exist
    chunks = await test_db.execute(
        select(Chunk).where(Chunk.document_id == document_id)
    )
    chunks = chunks.scalars().all()
    assert len(chunks) == doc.chunk_count

    # Check proposed entities exist
    proposed = await test_db.execute(
        select(ProposedContent).where(
            ProposedContent.content["source_document_id"].astext == document_id
        )
    )
    proposed = proposed.scalars().all()
    assert len(proposed) == doc.entity_count
```

---

### 3.2 Document List API Tests
**Endpoint:** `GET /api/documents/`
**Coverage Target:** All query parameters

#### TEST-INT-005: List All Documents
**Requirements:** TR-4.1
**Priority:** P0

```python
@pytest.mark.asyncio
async def test_list_all_documents(test_client, populated_db):
    """Test listing all documents."""
    # WHEN
    response = await test_client.get("/api/documents/")

    # THEN
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert data["total"] >= 0
```

#### TEST-INT-006: List with Pagination
**Requirements:** TR-4.1
**Priority:** P1

```python
@pytest.mark.asyncio
async def test_list_with_pagination(test_client, populated_db):
    """Test document listing pagination."""
    # WHEN
    response = await test_client.get("/api/documents/?skip=0&limit=5")

    # THEN
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) <= 5
```

---

### 3.3 End-to-End Ingestion Workflow
**Coverage:** Complete document lifecycle

#### TEST-INT-007: Complete Ingestion Pipeline
**Requirements:** FR-1 (all sub-requirements)
**Priority:** P0

```python
@pytest.mark.asyncio
@pytest.mark.slow
async def test_complete_ingestion_pipeline(test_client, test_db, sample_pdf):
    """Test end-to-end document ingestion pipeline."""
    # GIVEN
    files = {"file": ("lotr_excerpt.pdf", sample_pdf, "application/pdf")}

    # WHEN - Upload
    response = await test_client.post("/api/documents/upload", files=files)

    # THEN - Verify response
    assert response.status_code == 200
    data = response.json()
    doc_id = data["document"]["id"]

    # Verify document in DB
    from backend.app.database.models import Document
    doc = await test_db.get(Document, doc_id)
    assert doc is not None
    assert doc.status == "active"

    # Verify chunks in ChromaDB
    from backend.app.database.connection import get_chroma
    chroma = get_chroma()
    collection = chroma.get_collection("document_chunks")
    results = collection.get(where={"document_id": doc_id})
    assert len(results["ids"]) == data["chunks_created"]

    # Verify proposed entities
    from backend.app.database.models import ProposedContent
    from sqlalchemy import select
    proposed = await test_db.execute(
        select(ProposedContent).where(
            ProposedContent.type == "entity"
        )
    )
    proposed_entities = proposed.scalars().all()
    assert len(proposed_entities) == data["entities_extracted"]
```

---

## 4. Performance Test Specifications

### 4.1 Ingestion Performance Tests
**Requirements:** FR-1.4, NFR-1.2

#### TEST-PERF-001: Ingestion Time for 50-Page Document
**Requirements:** FR-1.4
**Priority:** P0
**Target:** <2 minutes

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_ingestion_time_50_pages(test_client, pdf_50_pages):
    """Test ingestion time meets requirement for 50-page document."""
    # GIVEN
    files = {"file": ("50_pages.pdf", pdf_50_pages, "application/pdf")}

    # WHEN
    import time
    start = time.time()
    response = await test_client.post("/api/documents/upload", files=files)
    duration = time.time() - start

    # THEN
    assert response.status_code == 200
    assert duration < 120, f"Ingestion took {duration:.1f}s, target is <120s"
```

#### TEST-PERF-002: Ingestion Throughput
**Requirements:** QR-1.3 (100 docs in <1 hour)
**Priority:** P1
**Target:** 100 documents in <3600 seconds

```python
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_ingestion_throughput(test_client, batch_pdfs_10_pages):
    """Test ingestion can process 100 documents in under 1 hour."""
    # GIVEN
    documents = batch_pdfs_10_pages  # 100 x 10-page PDFs

    # WHEN
    import time
    start = time.time()

    for i, pdf in enumerate(documents):
        files = {"file": (f"doc_{i}.pdf", pdf, "application/pdf")}
        response = await test_client.post("/api/documents/upload", files=files)
        assert response.status_code == 200

    duration = time.time() - start

    # THEN
    assert duration < 3600, f"100 docs took {duration:.1f}s, target is <3600s"
```

---

### 4.2 Query Performance Tests
**Requirements:** FR-2.4, NFR-1.1

#### TEST-PERF-003: Query Latency Single User
**Requirements:** FR-2.4
**Priority:** P0
**Target:** <5 seconds (p95)

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_query_latency_single_user(test_client, populated_db):
    """Test query latency for single user."""
    # GIVEN
    queries = [
        "Who is Aragorn?",
        "What is Rivendell?",
        "Tell me about the One Ring.",
        # ... 100 test queries
    ]

    # WHEN
    latencies = []
    for query in queries:
        import time
        start = time.time()
        response = await test_client.post("/api/query", json={"query": query})
        latency = time.time() - start
        latencies.append(latency)
        assert response.status_code == 200

    # THEN
    import numpy as np
    p95_latency = np.percentile(latencies, 95)
    assert p95_latency < 5.0, f"P95 latency {p95_latency:.2f}s, target is <5s"
```

#### TEST-PERF-004: Concurrent Query Performance
**Requirements:** NFR-1.3 (10 concurrent users)
**Priority:** P1
**Target:** <5s with 10 concurrent users

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_query_performance(test_client, populated_db):
    """Test query latency with 10 concurrent users."""
    # GIVEN
    import asyncio

    async def run_query(query):
        import time
        start = time.time()
        response = await test_client.post("/api/query", json={"query": query})
        return time.time() - start

    queries = ["Who is Aragorn?"] * 10  # 10 concurrent queries

    # WHEN
    latencies = await asyncio.gather(*[run_query(q) for q in queries])

    # THEN
    max_latency = max(latencies)
    assert max_latency < 5.0, f"Max latency {max_latency:.2f}s with 10 concurrent users"
```

---

## 5. User Acceptance Test (UAT) Specifications

### 5.1 UAT Scenario 1: Upload and Query Workflow
**Requirements:** FR-1, FR-2
**Priority:** P0

#### TEST-UAT-001: Upload Document and Query Canon
**User Story:** As a worldbuilder, I want to upload my lore document and ask questions about it.

**Test Steps:**
1. Navigate to Upload page
2. Select a PDF file (10-20 pages of worldbuilding lore)
3. Click "Process Document"
4. Wait for processing to complete
5. Verify success message and statistics
6. Navigate to Query page
7. Enter question: "Who are the main characters?"
8. Verify answer includes character names
9. Verify citations link to uploaded document
10. Click a citation
11. Verify it shows correct source excerpt

**Acceptance Criteria:**
- Upload completes in <2 minutes
- Entities are extracted
- Query returns relevant answer
- Citations are accurate
- User satisfaction: "Easy to use" ≥7/10

---

### 5.2 UAT Scenario 2: Review and Approve Entities
**Requirements:** FR-4
**Priority:** P0

#### TEST-UAT-002: Review AI-Extracted Entities
**User Story:** As a worldbuilder, I want to review AI-extracted entities before they become canon.

**Test Steps:**
1. Upload a document with entity extraction enabled
2. Navigate to Review Queue page
3. See list of proposed entities
4. Click on first entity
5. Review entity details (name, type, description)
6. Verify source document reference
7. Click "Approve"
8. Verify entity moves to canonical
9. Click second entity
10. Click "Edit"
11. Modify description
12. Click "Save & Approve"
13. Verify edited entity in canonical

**Acceptance Criteria:**
- All proposed entities visible
- Can approve, reject, and edit entities
- Changes persist
- User satisfaction: "Review process is clear" ≥7/10

---

### 5.3 UAT Scenario 3: Detect Inconsistencies
**Requirements:** FR-3
**Priority:** P0

#### TEST-UAT-003: Detect Contradictions in Lore
**User Story:** As a worldbuilder, I want to be alerted when new content contradicts existing canon.

**Test Steps:**
1. Upload first document: "Gandalf is a wizard who lives in the Shire"
2. Approve extracted entities
3. Upload second document: "Gandalf is a warrior from Gondor"
4. Navigate to Conflicts page
5. Verify conflict detected between two documents
6. Review conflict details
7. See evidence from both sources
8. Verify severity classification
9. Mark conflict as "Not actually conflicting" OR resolve it
10. Verify conflict status updates

**Acceptance Criteria:**
- Contradiction is detected automatically
- Conflict shows evidence from both sources
- Severity is appropriate
- User can resolve or dismiss conflicts
- User satisfaction: "Conflict detection is helpful" ≥7/10

---

## 6. Test Fixtures and Data

### 6.1 Sample Documents Required

```python
# tests/fixtures/documents.py

FIXTURES = {
    # Basic format tests
    "sample_10_pages.pdf": "PDF with 10 pages, mixed content",
    "sample.docx": "DOCX with headings and paragraphs",
    "sample.md": "Markdown with headings, lists, code blocks",
    "sample.txt": "Plain text file",

    # Entity extraction tests
    "lotr_excerpt.pdf": "Lord of the Rings excerpt with characters/locations",
    "fantasy_world.md": "Custom fantasy world with entities",

    # Contradiction tests
    "doc_version_1.pdf": "Canon version 1",
    "doc_version_2_conflicting.pdf": "Contradicts version 1",

    # Performance tests
    "pdf_50_pages.pdf": "50-page document for performance testing",
    "batch_pdfs_10_pages": "100 x 10-page PDFs for throughput testing",

    # Annotated corpus
    "annotated_corpus.json": "Ground truth entities for precision testing"
}
```

### 6.2 Database Fixtures

```python
# tests/fixtures/db_fixtures.py

@pytest.fixture
async def test_db():
    """Provide clean test database."""
    # Create test database
    # Run migrations
    # Yield session
    # Teardown

@pytest.fixture
async def populated_db(test_db):
    """Provide database with sample data."""
    # Insert sample documents
    # Insert sample entities
    # Insert sample proposed content
    # Yield session
```

### 6.3 Mock LLM Responses

```python
# tests/fixtures/mock_llm.py

@pytest.fixture
def mock_llm(monkeypatch):
    """Provide mocked LLM for fast testing."""

    class MockLLMProvider:
        async def generate(self, prompt):
            # Return predefined responses

        async def generate_structured(self, prompt, schema):
            # Return mock structured data

    return MockLLMProvider()
```

---

## 7. Test Execution Plan

### 7.1 Local Development

```bash
# Run all unit tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit --cov=backend/app --cov-report=html

# Run specific test file
pytest tests/unit/test_parser.py -v

# Run integration tests (requires Docker)
pytest tests/integration -v

# Run performance tests (slow)
pytest tests/performance -v -m performance
```

### 7.2 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest tests/unit --cov=backend/app --cov-fail-under=70

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      chromadb:
        image: chromadb/chroma:latest
    steps:
      - uses: actions/checkout@v2
      - name: Run integration tests
        run: pytest tests/integration -v

  performance-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Run performance tests
        run: pytest tests/performance -v
```

### 7.3 Test Schedule

| Test Type | Frequency | Trigger | Duration |
|-----------|-----------|---------|----------|
| Unit Tests | Every commit | Pre-commit hook | <2 min |
| Integration Tests | Every push | CI/CD | <10 min |
| Performance Tests | Daily | Scheduled | <30 min |
| UAT | Weekly | Manual | 1-2 hours |
| Load Tests | Pre-release | Manual | 2-4 hours |

---

## 8. Test Metrics and Reporting

### 8.1 Coverage Metrics

```bash
# Generate coverage report
pytest --cov=backend/app --cov-report=html

# View report
open htmlcov/index.html
```

**Target Coverage:**
- Overall: ≥70%
- Critical modules (parser, pipeline): ≥80%
- LLM providers: ≥60% (due to external API mocking complexity)

### 8.2 Test Result Dashboard

Track in GitHub/project management:
- ✅ Tests passing
- ⚠️ Tests failing
- 📊 Coverage percentage
- ⏱️ Performance benchmarks
- 📈 Trend over time

### 8.3 Quality Gates

**Pre-merge requirements:**
- ✅ All unit tests pass
- ✅ Coverage ≥70%
- ✅ No new linting errors
- ✅ Integration tests pass

**Pre-release requirements:**
- ✅ All tests pass (unit + integration + performance)
- ✅ UAT scenarios completed
- ✅ Performance benchmarks meet targets
- ✅ No critical bugs open

---

## 9. Test Maintenance

### 9.1 Adding New Tests

When adding a new feature:
1. Write test specification in this document
2. Implement unit tests (TDD preferred)
3. Implement integration tests
4. Update fixtures if needed
5. Update CI/CD if needed

### 9.2 Updating Existing Tests

When requirements change:
1. Update test specification
2. Update test implementation
3. Update fixtures
4. Verify all tests still pass

### 9.3 Test Review Checklist

- [ ] Test has clear requirement mapping
- [ ] Test has priority assigned
- [ ] Test has acceptance criteria
- [ ] Test is deterministic (no flaky tests)
- [ ] Test runs in reasonable time
- [ ] Test has proper cleanup
- [ ] Test is documented

---

**Document Owner:** QA Team
**Last Updated:** January 6, 2026
**Status:** Active
**Next Review:** End of Phase 1 (3 months)
