FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for unstructured and document processing
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY backend/requirements.txt ./backend/
COPY frontend/requirements.txt ./frontend/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt && \
    pip install --no-cache-dir -r frontend/requirements.txt

# Download embedding model during build (caching for faster startup)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create data directories
RUN mkdir -p /data/documents /data/chromadb /data/exports

# Expose ports
EXPOSE 8000 8501

# Set Python path to find the app module
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Default command runs both FastAPI and Streamlit
# For production, use a process manager like supervisord
CMD sh -c "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 & wait"
