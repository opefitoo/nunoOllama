# Nuno AI Planning Orchestrator

LLM-powered orchestrator for shift planning optimization. Uses AI reasoning (local Ollama or cloud APIs) to analyze constraint programming failures and suggest strategic relaxations.

**🆕 Now supports local LLM via Ollama - no API costs, full privacy!**

## Overview

This microservice acts as an **AI coach** around the Google OR-Tools CP-SAT solver, helping diagnose and resolve INFEASIBLE planning scenarios by:

1. Analyzing diagnostic data from failed optimizer runs
2. Using LLM reasoning to understand constraint conflicts
3. Suggesting prioritized constraint relaxation strategies
4. Providing implementation guidance

**Important**: This is NOT a replacement for CP-SAT. LLMs are used for high-level reasoning and guidance, while OR-Tools handles the actual optimization.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Django/FastAPI Backend (inur.django)               │
│  ├─ PlanningOptimizer (OR-Tools CP-SAT)            │
│  ├─ Diagnostic data collection                      │
│  └─ API endpoint: /planning/analyze-failure         │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP POST
                   │ (diagnostic data)
                   ▼
┌─────────────────────────────────────────────────────┐
│  nunoAIPlanning (This Service)                      │
│  ├─ FastAPI server on port 8001                     │
│  ├─ LLM orchestrator (DeepSeek/OpenAI/Anthropic)   │
│  └─ Response: Relaxation suggestions                │
└─────────────────────────────────────────────────────┘
```

## Features

- **Root Cause Analysis**: Identifies why optimization is INFEASIBLE
- **Constraint Reasoning**: Analyzes capacity gaps, conflicts, and interactions
- **Strategy Ladder**: Provides prioritized relaxation suggestions
- **Multi-Provider Support**:
  - **Ollama** (local, recommended) - $0 cost, full privacy
  - DeepSeek - $0.50-1.00 per analysis
  - OpenAI - $2.00-5.00 per analysis
  - Anthropic - $1.00-3.00 per analysis
- **Reasoning Trace**: Transparent reasoning steps (where supported)

## Quick Start

### Option A: Local LLM with Ollama (Recommended - $0 cost)

#### 1. Install Ollama

```bash
# Run the automated setup script
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning
./setup-ollama.sh llama3.1:8b
```

Or manually:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download model (choose one)
ollama pull llama3.1:8b        # Recommended: 4.7GB, fast, excellent quality
ollama pull qwen2.5:14b        # Better reasoning: 9GB, moderate speed
ollama pull llama3.1:70b       # Best quality: 40GB, requires GPU
```

#### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env (already configured for Ollama by default)
cat .env
# LLM_PROVIDER=ollama
# LLM_MODEL=llama3.1:8b
# OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
# LLM_API_KEY=not_needed_for_ollama
```

#### 3. Start Service

```bash
# Start AI orchestrator (connects to Ollama on host)
docker-compose up -d

# Or run everything in Docker (includes Ollama)
docker-compose -f docker-compose.ollama.yml up -d
```

#### 4. Verify

```bash
curl http://localhost:8001/health
# Should show: "llm_provider": "ollama", "llm_configured": true
```

See [LOCAL_LLM_SETUP.md](./LOCAL_LLM_SETUP.md) for detailed guide.

### Option B: Cloud LLM (DeepSeek/OpenAI/Anthropic)

#### 1. Prerequisites

- Docker and Docker Compose
- LLM API key (DeepSeek, OpenAI, or Anthropic)

### 2. Configuration

Create `.env` file in project root:

```bash
# LLM Provider (deepseek, openai, or anthropic)
LLM_PROVIDER=deepseek

# Model selection
LLM_MODEL=deepseek-reasoner

# API Key (choose one based on provider)
LLM_API_KEY=your_deepseek_api_key_here
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f

# Health check
curl http://localhost:8001/health
```

### 4. Verify Service

```bash
# Root endpoint
curl http://localhost:8001/

# Expected response:
{
  "service": "Nuno AI Planning Orchestrator",
  "status": "running",
  "version": "1.0.0",
  "llm_provider": "deepseek",
  "llm_model": "deepseek-reasoner"
}
```

## API Endpoints

### `POST /analyze-planning`

Analyze failed optimization and get constraint relaxation suggestions.

**Request Body:**

```json
{
  "planning_id": 4,
  "month": 12,
  "year": 2025,
  "failure_message": "No solution found (INFEASIBLE)",
  "time_limit_seconds": 30,
  "strategies_attempted": [
    "strategy_a_base",
    "strategy_b_relax_min_coverage",
    "strategy_c_relax_weekly_hours"
  ],
  "employees": [
    {
      "id": 1,
      "abbreviation": "JD",
      "contract_hours_per_week": 40.0,
      "contract_hours_per_day": 8.0,
      "is_intern": false
    }
  ],
  "total_employees": 10,
  "intern_count": 2,
  "daily_diagnostics": [
    {
      "day": 1,
      "weekday": "Monday",
      "required_coverage": 3,
      "available_employees": 2,
      "intern_school_count": 1,
      "holiday_requests": 0,
      "effective_capacity": 2,
      "capacity_gap": 1,
      "is_weekend": false
    }
  ],
  "min_daily_coverage": 3,
  "constraint_violations": [
    {
      "constraint_type": "capacity",
      "severity": "critical",
      "description": "Insufficient capacity on 5 days",
      "affected_days": [1, 5, 12, 20, 28]
    }
  ],
  "manual_shift_count": 0
}
```

**Response:**

```json
{
  "analysis_timestamp": "2025-02-10T14:30:00Z",
  "planning_id": 4,
  "root_cause_summary": "Insufficient employee capacity on 5 critical days combined with strict weekend OFF policy",
  "critical_issues": [
    "Capacity gap of 1-2 employees on days 1, 5, 12, 20, 28",
    "2 interns at school reducing available pool",
    "Weekend constraint removes 8 days from optimization space"
  ],
  "relaxation_suggestions": [
    {
      "priority": 1,
      "constraint_to_relax": "Minimum Daily Coverage",
      "relaxation_strategy": "Allow 2 employees instead of 3 on low-demand days",
      "description": "Temporarily reduce min_daily_coverage from 3 to 2 for specific days with capacity gaps",
      "expected_impact": "Will allow optimizer to find feasible solution while maintaining safety with 2 staff",
      "implementation_code": "optimizer.min_daily_coverage = 2  # or per-day override",
      "risk_level": "low"
    }
  ],
  "long_term_recommendations": [
    "Consider hiring additional staff to improve capacity margins",
    "Review intern school schedules for better coverage alignment"
  ],
  "reasoning_trace": "Step 1: Analyzed capacity diagnostics...\nStep 2: Identified constraint conflicts..."
}
```

### `POST /quick-advice`

Get quick advice without full diagnostics (useful for development).

**Parameters:**
- `failure_message` (string): Error message from optimizer
- `strategies_attempted` (array): List of strategy names already tried

**Response:**

```json
{
  "advice": "Try relaxing minimum coverage constraint or allowing partial weekend work on Saturdays only.",
  "timestamp": "2025-02-10T14:30:00Z"
}
```

### `GET /supported-providers`

Get list of supported LLM providers and models.

## Integration with inur.django

### Step 1: Add Diagnostic Collection

In `fastapi_app/planning/optimizer.py`, add method to collect diagnostics:

```python
def get_diagnostics(self) -> Dict[str, Any]:
    """Collect diagnostic data for LLM analysis"""
    daily_diagnostics = []

    for day in self.days:
        current_date = date(self.planning.year, self.planning.month, day)

        # Calculate capacity
        available = len([e for e in self.employees if self._is_available(e.id, day)])
        intern_school = len([e for e in self.employees
                            if e.id in self.intern_schedules
                            and not self._is_intern_available(e.id, day)])

        daily_diagnostics.append({
            "day": day,
            "weekday": current_date.strftime("%A"),
            "required_coverage": self.min_daily_coverage,
            "available_employees": available,
            "intern_school_count": intern_school,
            "effective_capacity": available,
            "capacity_gap": max(0, self.min_daily_coverage - available),
            "is_weekend": current_date.weekday() >= 5
        })

    return {
        "daily_diagnostics": daily_diagnostics,
        "employees": [
            {
                "id": e.id,
                "abbreviation": e.abbreviation,
                "contract_hours_per_week": e.occupation.hours_per_week,
                "contract_hours_per_day": e.occupation.hours_per_week / 5,
                "is_intern": e.id in self.intern_schedules
            }
            for e in self.employees
        ]
    }
```

### Step 2: Call AI Orchestrator on Failure

In `fastapi_app/routers/planning.py`:

```python
import httpx

async def optimize_planning_with_ai_fallback(planning_id: int):
    optimizer = PlanningOptimizer(planning, employees, shift_types)
    success, solution, message = optimizer.optimize(time_limit_seconds=30)

    if not success:
        # Call AI orchestrator for advice
        diagnostics = optimizer.get_diagnostics()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/analyze-planning",
                json={
                    "planning_id": planning_id,
                    "month": planning.month,
                    "year": planning.year,
                    "failure_message": message,
                    "strategies_attempted": optimizer.strategies_attempted,
                    **diagnostics
                }
            )

            if response.status_code == 200:
                advice = response.json()
                # Log or return advice to user
                print(f"AI Suggestion: {advice['root_cause_summary']}")
                print(f"Try: {advice['relaxation_suggestions'][0]['relaxation_strategy']}")
```

## LLM Provider Comparison

| Provider | Model | Strengths | Cost | Recommendation |
|----------|-------|-----------|------|----------------|
| **DeepSeek** | deepseek-reasoner | Best for constraint reasoning, transparent thinking, low cost | $ | ⭐ **Recommended** |
| OpenAI | gpt-4-turbo | Strong general reasoning | $$$ | Good alternative |
| Anthropic | claude-3-opus | Excellent analysis depth | $$$$ | Premium option |

## Development

### Run Locally (without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LLM_PROVIDER=deepseek
export LLM_MODEL=deepseek-reasoner
export LLM_API_KEY=your_key_here

# Run server
cd docker
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### Testing

```bash
# Test health endpoint
curl http://localhost:8001/health

# Test quick advice
curl -X POST "http://localhost:8001/quick-advice" \
  -H "Content-Type: application/json" \
  -d '{
    "failure_message": "No solution found (INFEASIBLE)",
    "strategies_attempted": ["strategy_a_base"]
  }'
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs -f

# Common issues:
# 1. Missing API key - check .env file
# 2. Port 8001 already in use - change in docker-compose.yml
# 3. Build failed - try: docker-compose build --no-cache
```

### LLM API errors

```bash
# Test API key manually
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-reasoner", "messages": [{"role": "user", "content": "test"}]}'
```

### Integration not working

- Verify both services are running: `docker ps`
- Check network connectivity: `docker network inspect nuno-network`
- Ensure Django backend can reach `http://localhost:8001`

## Production Deployment

### Security Considerations

1. **API Keys**: Use secrets management (AWS Secrets Manager, HashiCorp Vault)
2. **CORS**: Restrict `allow_origins` in `server.py` to your domain
3. **Rate Limiting**: Add rate limiting middleware for production
4. **HTTPS**: Use reverse proxy (nginx) with SSL certificates

### Docker Compose Production

```yaml
# docker-compose.prod.yml
services:
  ai-planning:
    image: nuno-ai-planning:latest
    restart: always
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## License

Internal project for Inur S.à.r.l.

## Support

For issues or questions, contact the development team.

---

**Version**: 1.0.0
**Last Updated**: February 2025
