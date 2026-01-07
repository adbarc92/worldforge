# Test Fixtures - Sample Documents

This directory contains sample documents for testing the AetherCanon Builder ingestion pipeline.

## Available Fixtures

### sample.md
- **Format:** Markdown
- **Size:** ~3KB
- **Content:** Middle-earth lore (Lord of the Rings)
- **Entities:** 9 characters, 3 locations, 2 items, 2 events, 2 concepts
- **Use Cases:**
  - Basic ingestion pipeline testing
  - Entity extraction validation
  - Markdown parsing tests
  - Integration tests

## Missing Fixtures (To Be Added)

For complete test coverage, add these fixtures:

### Required for Unit Tests
- `sample.pdf` - 10-page PDF document
- `sample.docx` - DOCX with headings and formatting
- `sample.txt` - Plain text file

### Required for Performance Tests
- `pdf_50_pages.pdf` - For ingestion performance testing (FR-1.4)
- `batch_pdfs_10_pages/` - 100 x 10-page PDFs for throughput testing

### Required for Contradiction Tests
- `doc_version_1.pdf` - Canon version 1
- `doc_version_2_conflicting.pdf` - Contradicts version 1

### Required for Precision Testing
- `annotated_corpus.json` - Ground truth entities for TEST-UNIT-014

## Creating Test Fixtures

### Generate PDF from Markdown
```bash
# Using pandoc
pandoc sample.md -o sample.pdf

# Using LibreOffice (for DOCX too)
libreoffice --headless --convert-to pdf sample.md
libreoffice --headless --convert-to docx sample.md
```

### Generate Large PDFs for Performance Testing
```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf(filename, num_pages):
    c = canvas.Canvas(filename, pagesize=letter)
    for i in range(num_pages):
        c.drawString(100, 750, f"Page {i+1} of {num_pages}")
        c.drawString(100, 700, "Lorem ipsum dolor sit amet...")
        # Add more content
        c.showPage()
    c.save()

create_test_pdf("pdf_50_pages.pdf", 50)
```

## Test Data Conventions

1. **Realistic Content:** Use actual worldbuilding content for better test validity
2. **Known Entities:** Document expected entities for validation
3. **Varied Formats:** Test different document structures
4. **Edge Cases:** Include documents that test boundary conditions

## Annotated Corpus Format

For `annotated_corpus.json`:

```json
[
  {
    "document_id": "test-001",
    "text": "Aragorn was the heir to Gondor's throne...",
    "entities": [
      {
        "name": "Aragorn",
        "type": "character",
        "start_char": 0,
        "end_char": 7
      },
      {
        "name": "Gondor",
        "type": "location",
        "start_char": 23,
        "end_char": 29
      }
    ]
  }
]
```

This allows precise calculation of entity extraction precision/recall.
