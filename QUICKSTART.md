# AetherCanon Builder - Quick Start Guide

## 🚀 Getting Started

### Prerequisites

- **Docker Desktop** installed and running
- **8GB RAM minimum** (16GB recommended)
- **10GB free disk space**

### Step 1: Start Docker

1. Open **Docker Desktop**
2. Wait for Docker to fully start (whale icon in system tray/menu bar should be active)
3. Verify Docker is running:
   ```bash
   docker --version
   docker ps
   ```

### Step 2: Build the Application

From the `worldforge` directory:

```bash
# Build Docker containers (first time only, takes 5-10 minutes)
docker-compose build

# This will:
# - Download Python 3.11 base image
# - Install system dependencies (libmagic, poppler, tesseract)
# - Install Python packages (FastAPI, Streamlit, LlamaIndex, etc.)
# - Download BGE-large-en-v1.5 embedding model (~1.3GB)
# - Set up the application
```

### Step 3: Start the Application

```bash
# Start all services
docker-compose up

# Or run in detached mode (background)
docker-compose up -d
```

**Services will start on:**
- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Ollama LLM**: http://localhost:11434

### Step 4: Download Ollama Model (First Time Only)

```bash
# In a new terminal, download the Mistral model
docker exec -it worldforge-ollama ollama pull mistral:7b-instruct

# This downloads ~4GB, takes 5-10 minutes depending on connection
```

### Step 5: Access the Application

1. Open your browser to **http://localhost:8501**
2. You should see the AetherCanon Builder home page

---

## 📝 Testing the MVP Features

### Feature 1: Document Ingestion

1. Navigate to **📤 Upload Documents** in the sidebar
2. Click **Browse files**
3. Upload the test document: `tests/fixtures/documents/sample.md`
4. Check **Extract Entities** option
5. Click **Upload**
6. Wait for processing (30-60 seconds)
7. **Expected Result:**
   - Document appears in the list
   - Chunks created (~10-15 chunks)
   - Entities extracted (9+ entities)
   - Processing time displayed

### Feature 2: Semantic Query

1. Navigate to **🔍 Query Your World**
2. In the chat input, ask: "Who is Aragorn?"
3. **Expected Result:**
   - Answer generated with description of Aragorn
   - Inline citations [^1], [^2]
   - Expandable "View Sources" section
   - Retrieved chunks shown (if enabled)

**Try more queries:**
- "What is Rivendell?"
- "Tell me about the One Ring"
- "What happened at the Council of Elrond?"

### Feature 3: Inconsistency Detection

1. Navigate to **📤 Upload Documents** again
2. Create a conflicting document (or use API):
   ```bash
   # Example: Upload a document that contradicts existing canon
   curl -X POST "http://localhost:8000/api/documents/upload" \
     -F "file=@conflicting_doc.md" \
     -F "title=Conflicting Lore" \
     -F "extract_entities=true"
   ```
3. Check API for conflicts:
   ```bash
   curl http://localhost:8000/api/conflicts/
   ```
4. **Expected Result:**
   - Conflicts detected automatically
   - Severity levels assigned (high/medium/low)
   - Evidence from both sources shown

### Feature 4: Review Queue

1. Navigate to **✅ Review Queue**
2. **Expected Results:**
   - See all proposed entities from uploaded documents
   - Queue stats displayed (total pending, conflicts, avg confidence)
   - Items sorted by priority
   - Conflicts highlighted with ⚠️ icon

3. **Review an entity:**
   - Click **✅ Approve** to accept
   - Click **❌ Reject** to dismiss
   - Select multiple items for bulk approval

4. **Check approved entities:**
   ```bash
   # View approved entities
   curl http://localhost:8000/api/review/queue?status=approved
   ```

### Feature 5: Obsidian Export

1. Navigate to **📦 Export Your Canon**
2. (Optional) Enter export name: "middle_earth_export"
3. Select graph format: "d3"
4. Check **Include Graph JSON**
5. Click **🚀 Export to Obsidian**
6. **Expected Result:**
   - Export completes in 5-10 seconds
   - Shows entity/relationship counts
   - Files created count displayed
   - Export path shown

7. **Download the export:**
   ```bash
   # Download via API
   curl -O http://localhost:8000/api/export/obsidian/middle_earth_export/download
   ```

8. **Open in Obsidian:**
   - Extract the ZIP file
   - Open Obsidian → "Open folder as vault"
   - Select the exported folder
   - Browse `index.md` or navigate via wikilinks

---

## 🧪 API Testing (cURL Examples)

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@tests/fixtures/documents/sample.md" \
  -F "title=Middle-earth Lore" \
  -F "extract_entities=true"
```

### Semantic Query
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is Gandalf?", "top_k": 5}'
```

### List Conflicts
```bash
curl http://localhost:8000/api/conflicts/
```

### Review Queue Stats
```bash
curl http://localhost:8000/api/review/queue/stats
```

### Export to Obsidian
```bash
curl -X POST "http://localhost:8000/api/export/obsidian" \
  -H "Content-Type: application/json" \
  -d '{"export_name": "my_world", "include_graph": true}'
```

---

## 🔍 Troubleshooting

### Docker Build Issues

**Problem:** Build fails with "No space left on device"
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

**Problem:** Build is very slow
```bash
# Check Docker resource allocation in Docker Desktop settings
# Recommended: 4 CPUs, 8GB RAM
```

### Application Issues

**Problem:** "Connection refused" errors
```bash
# Check if containers are running
docker ps

# Check logs
docker logs worldforge-app
docker logs worldforge-ollama

# Restart containers
docker-compose restart
```

**Problem:** Ollama model not found
```bash
# Pull the model
docker exec -it worldforge-ollama ollama pull mistral:7b-instruct

# List available models
docker exec -it worldforge-ollama ollama list
```

**Problem:** Entity extraction fails
```bash
# Check LLM provider in logs
docker logs worldforge-app | grep "LLM Provider"

# Should show: "LLM Provider: ollama"
# If using Claude, ensure CLAUDE_API_KEY is set in .env
```

### Performance Issues

**Problem:** Queries are slow (>10 seconds)
- Increase Docker memory allocation to 8GB+
- Consider using GPU for embeddings (modify docker-compose.yml)
- Reduce `top_k` in query settings

**Problem:** Upload processing is slow
- First upload downloads embedding model (~1.3GB)
- Subsequent uploads are faster
- Processing time depends on document size

---

## 🛑 Stopping the Application

```bash
# Stop containers (keep data)
docker-compose down

# Stop and remove volumes (delete all data)
docker-compose down -v

# Stop and remove everything
docker-compose down -v --rmi all
```

---

## 📊 Monitoring

### View Logs
```bash
# All logs
docker-compose logs -f

# Specific service
docker logs -f worldforge-app
docker logs -f worldforge-ollama
```

### Check Resource Usage
```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Database
```bash
# Access SQLite database
docker exec -it worldforge-app sqlite3 /data/worldforge.db

# List tables
.tables

# Count entities
SELECT COUNT(*) FROM entities;

# Exit
.quit
```

---

## 🎯 Next Steps

After testing the MVP:

1. **Upload your own worldbuilding documents**
2. **Build your canon** by approving entities
3. **Query your knowledge base**
4. **Export to Obsidian** for editing
5. **Iterate**: Upload more docs, resolve conflicts, expand your world

---

## 🐛 Reporting Issues

If you encounter bugs:
1. Check logs: `docker logs worldforge-app`
2. Note the error message
3. Document steps to reproduce
4. Check existing issues at the project repository

---

## ⚙️ Configuration

### Switch from Ollama to Claude

Edit `.env`:
```bash
# Change this line:
LLM_PROVIDER=ollama

# To this:
LLM_PROVIDER=claude

# Add your Claude API key:
CLAUDE_API_KEY=sk-ant-...
```

Restart containers:
```bash
docker-compose restart
```

### Adjust Similarity Threshold

Edit `.env`:
```bash
# Lower = more sensitive (more conflicts detected)
# Higher = less sensitive (fewer conflicts)
SIMILARITY_THRESHOLD=0.85  # Default

# Try 0.75 for more conflict detection
# Try 0.90 for fewer false positives
```

### Chunking Configuration

Edit `.env`:
```bash
CHUNK_SIZE=500        # Tokens per chunk
CHUNK_OVERLAP=50      # Overlap between chunks

# Larger chunks = more context, fewer chunks
# Smaller chunks = more precise, more chunks
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Test Specifications**: `docs/TEST_SPECIFICATIONS.md`
- **Requirements**: `docs/REQUIREMENTS.md`
- **Architecture**: `docs/CoreDesignDoc.md`

---

**Enjoy building your world! 🌍✨**
