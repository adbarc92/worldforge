# Canon Builder - Detailed Setup Guide

This guide provides step-by-step instructions for setting up Canon Builder.

## Prerequisites

### Required
- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- 100GB+ free disk space
- 16GB+ RAM (64GB recommended)

### Optional but Recommended
- NVIDIA GPU with 12GB+ VRAM
- NVIDIA Container Toolkit (for GPU support)

## Installation Steps

### 1. Install Docker

#### Windows/Mac
1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Install and start Docker Desktop
3. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

#### Linux (Ubuntu/Debian)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### 2. GPU Support (Optional)

#### NVIDIA Container Toolkit (Linux)
```bash
# Add NVIDIA repo
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Test GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

#### Windows/Mac with Docker Desktop
- GPU passthrough is automatically configured
- Ensure NVIDIA drivers are up to date

### 3. Clone Repository

```bash
git clone https://github.com/yourusername/canon-builder.git
cd canon-builder
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferred editor
nano .env  # or vim, code, etc.
```

**Important**: Change these values in `.env`:
- `WEBUI_SECRET_KEY` - Random string for web UI security
- `JWT_SECRET` - Random string for JWT tokens
- `GRAFANA_PASSWORD` - Admin password for Grafana (if using monitoring)

Generate secure secrets:
```bash
# Linux/Mac
openssl rand -hex 32

# Windows (PowerShell)
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

### 5. Start Services

```bash
# Start all core services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Neo4j Browser**: http://localhost:7474
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### 6. Download LLM Models

This is the longest step (~40GB download for the 70B model).

```bash
# Pull the main LLM (this will take 30-60 minutes)
docker exec -it canon_ollama ollama pull llama3.1:70b

# Pull the embedding model (faster, ~1GB)
docker exec -it canon_ollama ollama pull bge-large-en-v1.5

# Verify models are installed
docker exec -it canon_ollama ollama list
```

**Alternative: Smaller Models**

If you have limited resources, use smaller models:

```bash
# 8B model (much faster, less capable)
docker exec -it canon_ollama ollama pull llama3.1:8b

# Update .env to use the smaller model
# LLM_MODEL=llama3.1:8b
```

### 7. Initialize Database

The database will be automatically initialized on first startup using the migration script in `backend/migrations/001_initial_schema.sql`.

Verify database:
```bash
# Connect to PostgreSQL
docker exec -it canon_postgres psql -U canon -d canon_metadata

# List tables
\dt

# Exit
\q
```

### 8. Test the Installation

```bash
# Check health
curl http://localhost:8080/health

# Login (demo user)
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'

# Save the token from response for later use
```

### 9. Set Up Obsidian Vault

```bash
# Copy vault template
cp -r obsidian-vault-template ~/my-first-canon

# Open in Obsidian
# 1. Launch Obsidian
# 2. Click "Open folder as vault"
# 3. Select ~/my-first-canon
```

## Troubleshooting

### Services Won't Start

```bash
# Check for port conflicts
netstat -an | grep -E "3000|8080|7474|6333|11434"

# Check Docker logs
docker-compose logs

# Restart specific service
docker-compose restart canon_api
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Reduce Neo4j memory in docker-compose.yml:
# NEO4J_dbms_memory_heap_max__size=1G  # was 2G
# NEO4J_dbms_memory_pagecache_size=512M  # was 1G

# Restart
docker-compose down
docker-compose up -d
```

### Ollama Model Download Fails

```bash
# Check available space
df -h

# Clear Docker cache if needed
docker system prune -a

# Try downloading again
docker exec -it canon_ollama ollama pull llama3.1:70b
```

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If GPU not working, edit docker-compose.yml:
# Comment out the deploy.resources section for ollama service
```

### API Returns 404 or 500 Errors

```bash
# Check backend logs
docker-compose logs canon_api

# Restart backend
docker-compose restart canon_api

# Check if migrations ran
docker exec -it canon_postgres psql -U canon -d canon_metadata -c "\dt"
```

## Performance Tuning

### For Limited RAM (16GB)

1. Use smaller LLM: `llama3.1:8b` or `llama3.1:7b`
2. Reduce Neo4j memory (see above)
3. Reduce Qdrant collection size
4. Disable monitoring services

```bash
# Don't start monitoring
docker-compose up -d --scale prometheus=0 --scale grafana=0
```

### For Better Performance

1. Use SSD storage
2. Allocate more RAM to Docker Desktop (Settings → Resources)
3. Use GPU for Ollama
4. Consider using quantized models (Q4_K_M variants)

## Updating

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Update models if needed
docker exec -it canon_ollama ollama pull llama3.1:70b
```

## Backup

### Backup All Data

```bash
# Stop services
docker-compose down

# Backup volumes
docker run --rm -v canon_qdrant_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/qdrant-backup.tar.gz /data

docker run --rm -v canon_neo4j_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/neo4j-backup.tar.gz /data

docker run --rm -v canon_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Start services
docker-compose up -d
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore volumes
docker run --rm -v canon_qdrant_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/qdrant-backup.tar.gz -C /

docker run --rm -v canon_neo4j_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/neo4j-backup.tar.gz -C /

docker run --rm -v canon_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /

# Start services
docker-compose up -d
```

## Next Steps

1. Read the [main README](README.md) for usage examples
2. Check out the [Core Design Document](docs/CoreDesignDoc.md) for architecture details
3. Start building your first canon!
4. Join the community (Discord link TBD)

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/canon-builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/canon-builder/discussions)
- **Documentation**: [docs/](docs/)
