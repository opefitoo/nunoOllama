#!/bin/bash
# Setup script for Ollama local LLM

set -e

echo "========================================"
echo "Nuno AI Planning - Ollama Setup"
echo "========================================"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Installing Ollama..."

    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Please download Ollama from: https://ollama.ai/download"
        echo "Or install via Homebrew: brew install ollama"
        exit 1
    else
        echo "Please install Ollama from: https://ollama.ai/download"
        exit 1
    fi
else
    echo "✅ Ollama is installed"
    ollama --version
fi

echo ""
echo "========================================"
echo "Downloading LLM Model"
echo "========================================"
echo ""

# Check which model to download
MODEL=${1:-llama3.1:8b}

echo "Downloading model: $MODEL"
echo "This may take several minutes (model size: ~4-10GB)..."
echo ""

ollama pull $MODEL

echo ""
echo "✅ Model downloaded successfully!"
echo ""

# Test the model
echo "========================================"
echo "Testing Model"
echo "========================================"
echo ""

ollama run $MODEL "What is constraint programming? Answer in one sentence." --verbose=false

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "✅ Ollama is running on: http://localhost:11434"
echo "✅ Model ready: $MODEL"
echo ""
echo "Next steps:"
echo "1. Update .env file:"
echo "   LLM_PROVIDER=ollama"
echo "   LLM_MODEL=$MODEL"
echo "   OLLAMA_BASE_URL=http://localhost:11434/v1"
echo ""
echo "2. Start the AI orchestrator:"
echo "   docker-compose up -d"
echo ""
echo "3. Test the service:"
echo "   curl http://localhost:8001/health"
echo ""
