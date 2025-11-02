# Local LLM Setup Guide

This guide shows how to use a **local LLM** instead of cloud APIs (DeepSeek/OpenAI/Anthropic).

## Benefits of Local LLM

✅ **Zero API costs** - No per-request charges
✅ **Data privacy** - All planning data stays on your server
✅ **No internet dependency** - Works offline
✅ **Full control** - No rate limits or service outages

## Recommended Setup: Ollama

[Ollama](https://ollama.ai) is the easiest way to run local LLMs. It handles model downloads, GPU acceleration, and provides an OpenAI-compatible API.

### 1. Install Ollama on Your Server

```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### 2. Download a Model

We recommend these models for constraint reasoning:

**Option A: Llama 3.1 8B (Best balance)** ⭐ RECOMMENDED
```bash
ollama pull llama3.1:8b
```
- Size: ~4.7GB
- RAM needed: 8GB
- Quality: Excellent reasoning
- Speed: Fast (~2-5 seconds per response)

**Option B: Qwen2.5 14B (Better reasoning)**
```bash
ollama pull qwen2.5:14b
```
- Size: ~9GB
- RAM needed: 16GB
- Quality: Superior reasoning for complex constraints
- Speed: Moderate (~5-10 seconds)

**Option C: Llama 3.1 70B (Best quality, requires GPU)**
```bash
ollama pull llama3.1:70b
```
- Size: ~40GB
- RAM needed: 64GB or GPU with 48GB VRAM
- Quality: Best possible reasoning
- Speed: Slow without GPU (~20-60 seconds)

### 3. Test Ollama

```bash
# Start Ollama server (usually auto-starts)
ollama serve

# Test the model
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Why is constraint programming difficult?",
  "stream": false
}'
```

### 4. Configure the AI Orchestrator

Edit `/Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning/.env`:

```bash
# Use local Ollama instead of cloud APIs
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b

# Ollama API endpoint (default when running on same machine)
OLLAMA_BASE_URL=http://localhost:11434

# For Docker deployment (Ollama on host, container needs to reach it)
# OLLAMA_BASE_URL=http://host.docker.internal:11434

# No API key needed for local LLM!
LLM_API_KEY=not_needed_for_ollama
```

### 5. Deploy with Docker Compose

The updated `docker-compose.yml` includes two deployment options:

**Option A: Ollama on Host Machine** (Recommended for existing Ollama installation)
```bash
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning
docker-compose up -d
```

The AI orchestrator will connect to Ollama running on your host via `http://host.docker.internal:11434`.

**Option B: Ollama in Docker** (All-in-one deployment)
```bash
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning
docker-compose -f docker-compose.ollama.yml up -d
```

This runs both the AI orchestrator AND Ollama in containers.

### 6. Verify It Works

```bash
# Check AI orchestrator status
curl http://localhost:8001/health

# Should return:
{
  "status": "healthy",
  "timestamp": "2025-11-02T...",
  "llm_configured": true,
  "llm_provider": "ollama",
  "llm_model": "llama3.1:8b"
}

# Test quick advice
curl -X POST http://localhost:8001/quick-advice \
  -H "Content-Type: application/json" \
  -d '{
    "failure_message": "No solution found (INFEASIBLE)",
    "strategies_attempted": ["Full constraints", "Relaxed weekends"]
  }'
```

## Performance Comparison

| Provider | Cost per Analysis | Latency | Reasoning Quality | Privacy |
|----------|------------------|---------|-------------------|---------|
| **Ollama (Llama 3.1 8B)** | $0 | 2-5s | ⭐⭐⭐⭐ | ✅ Local |
| **Ollama (Qwen2.5 14B)** | $0 | 5-10s | ⭐⭐⭐⭐⭐ | ✅ Local |
| DeepSeek Reasoner | $0.50-1.00 | 3-8s | ⭐⭐⭐⭐⭐ | ❌ Cloud |
| GPT-4 Turbo | $2.00-5.00 | 5-15s | ⭐⭐⭐⭐⭐ | ❌ Cloud |

**Recommendation:** Use **Llama 3.1 8B** for production. It's free, fast, and provides excellent reasoning quality.

## Hardware Requirements

### Minimum (CPU only)
- CPU: 4 cores
- RAM: 8GB
- Storage: 10GB
- Model: llama3.1:8b
- Speed: 2-5 seconds per response

### Recommended (with GPU)
- CPU: 8 cores
- RAM: 16GB
- GPU: NVIDIA with 8GB VRAM (e.g., RTX 3060)
- Storage: 20GB
- Model: qwen2.5:14b or llama3.1:8b
- Speed: 1-2 seconds per response

### High Performance (production with GPU)
- CPU: 16 cores
- RAM: 32GB
- GPU: NVIDIA with 24GB VRAM (e.g., RTX 4090, A5000)
- Storage: 50GB
- Model: llama3.1:70b
- Speed: 2-3 seconds per response

## Docker Deployment Options

### Option 1: Ollama on Host + AI Orchestrator in Docker

**Best for:** Existing Ollama installation

```bash
# 1. Install Ollama on host
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b

# 2. Update .env
echo "LLM_PROVIDER=ollama" > .env
echo "LLM_MODEL=llama3.1:8b" >> .env
echo "OLLAMA_BASE_URL=http://host.docker.internal:11434" >> .env
echo "LLM_API_KEY=not_needed" >> .env

# 3. Start AI orchestrator
docker-compose up -d
```

### Option 2: Everything in Docker

**Best for:** Clean deployment, GPU acceleration

```bash
# Use the Ollama-specific compose file
docker-compose -f docker-compose.ollama.yml up -d

# Check logs
docker-compose -f docker-compose.ollama.yml logs -f ollama
docker-compose -f docker-compose.ollama.yml logs -f ai-planning
```

## Troubleshooting

### Issue: "Cannot connect to Ollama"

**Solution 1:** Check Ollama is running
```bash
curl http://localhost:11434/api/tags
```

**Solution 2:** Check Docker can reach host
```bash
docker run --rm alpine ping -c 3 host.docker.internal
```

**Solution 3:** Update OLLAMA_BASE_URL in .env
```bash
# For Docker on Linux (use actual host IP)
OLLAMA_BASE_URL=http://192.168.1.100:11434

# For Docker Desktop (macOS/Windows)
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Issue: "Model not found"

```bash
# List available models
ollama list

# Pull the model
ollama pull llama3.1:8b
```

### Issue: Slow responses (>10 seconds)

**Solution:** Use GPU acceleration

```bash
# Check if Ollama is using GPU
ollama ps

# If not, ensure NVIDIA drivers and Docker GPU support are installed
# See: https://docs.docker.com/config/containers/resource_constraints/#gpu
```

## Migration from Cloud to Local

If you're currently using DeepSeek/OpenAI/Anthropic:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Download model
ollama pull llama3.1:8b

# 3. Update .env (in nunoAIPlanning directory)
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning
cp .env .env.backup  # Backup old config

cat > .env << 'EOF'
# Local LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
LLM_API_KEY=not_needed
EOF

# 4. Restart AI orchestrator
docker-compose down
docker-compose up -d

# 5. Test
curl http://localhost:8001/health
```

## Cost Savings

With 100 planning optimizations per month:

| Provider | Monthly Cost |
|----------|-------------|
| Ollama (Local) | **$0** |
| DeepSeek | $50-100 |
| OpenAI GPT-4 | $200-500 |

**Annual savings with Ollama: $600-6,000** 💰

## Next Steps

1. ✅ Install Ollama on your server
2. ✅ Pull llama3.1:8b model
3. ✅ Update .env configuration
4. ✅ Deploy with docker-compose
5. ✅ Test with real planning failures
6. ✅ Monitor performance and adjust model if needed
