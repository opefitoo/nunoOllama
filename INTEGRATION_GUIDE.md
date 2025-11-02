# nunoAIPlanning Integration Guide

Complete guide for integrating the AI orchestrator with your Django/FastAPI planning optimizer.

## Quick Start

### 1. Start the AI Orchestrator Service

```bash
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning

# Configure your API key
cp .env.example .env
# Edit .env and add your DeepSeek/OpenAI/Anthropic API key

# Build and start
docker-compose build
docker-compose up -d

# Verify it's running
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-02-10T14:30:00Z",
  "llm_configured": true
}
```

### 2. Test the Service

```bash
# Quick test
curl -X POST "http://localhost:8001/quick-advice" \
  -H "Content-Type: application/json" \
  -d '{
    "failure_message": "No solution found (INFEASIBLE)",
    "strategies_attempted": ["strategy_a_base", "strategy_b_relax_coverage"]
  }'
```

## Integration Methods

### Method 1: Automatic AI Fallback (Recommended)

Use the provided `optimize_with_ai_fallback()` function that automatically calls the orchestrator when optimization fails.

**Location**: `/fastapi_app/planning/ai_orchestrator_example.py`

```python
from fastapi_app.planning.ai_orchestrator_example import optimize_with_ai_fallback

async def run_planning():
    planning = MonthlyPlanning.objects.get(id=4)
    employees = list(Employee.objects.filter(...))
    shift_types = list(ShiftType.objects.all())

    # This will automatically call AI orchestrator if optimization fails
    success, solution, message = await optimize_with_ai_fallback(
        planning,
        employees,
        shift_types,
        min_daily_coverage=3,
        time_limit_seconds=30,
        orchestrator_url="http://localhost:8001"
    )

    if success:
        # Save solution...
        pass
    else:
        # AI suggestions are logged, you can parse message
        # or implement automated retry with suggested relaxations
        pass
```

### Method 2: Manual API Call

Call the orchestrator directly when needed:

```python
import httpx
from fastapi_app.planning.optimizer import PlanningOptimizer

async def manual_ai_analysis():
    # Run optimizer
    optimizer = PlanningOptimizer(planning, employees, shift_types, min_daily_coverage=3)
    success, solution, message = optimizer.optimize(time_limit_seconds=30)

    if not success:
        # Collect diagnostics
        diagnostics = optimizer.get_diagnostics()

        # Call AI orchestrator
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8001/analyze-planning",
                json={
                    "planning_id": planning.id,
                    "month": planning.month,
                    "year": planning.year,
                    "failure_message": message,
                    "time_limit_seconds": 30,
                    "strategies_attempted": [
                        "Full constraints (ideal)",
                        "Without minimum work days",
                        # ... list all strategies tried
                    ],
                    "min_daily_coverage": 3,
                    **diagnostics  # Add all diagnostic data
                }
            )

            if response.status_code == 200:
                advice = response.json()

                # Process advice
                print(f"Root cause: {advice['root_cause_summary']}")
                print(f"Critical issues: {advice['critical_issues']}")

                for suggestion in advice['relaxation_suggestions']:
                    print(f"Priority {suggestion['priority']}: {suggestion['constraint_to_relax']}")
                    print(f"  Strategy: {suggestion['relaxation_strategy']}")
                    print(f"  Risk: {suggestion['risk_level']}")
```

### Method 3: Integration into FastAPI Endpoint

Modify `/fastapi_app/routers/planning.py` to add AI orchestrator support:

```python
from fastapi import APIRouter, Depends
import httpx

router = APIRouter()

@router.post("/planning/{planning_id}/optimize-with-ai")
async def optimize_planning_with_ai(planning_id: int):
    """
    Run optimization with AI orchestrator fallback for guidance.
    """
    planning = MonthlyPlanning.objects.get(id=planning_id)
    employees = list(Employee.objects.filter(...))
    shift_types = list(ShiftType.objects.all())

    optimizer = PlanningOptimizer(planning, employees, shift_types, min_daily_coverage=3)
    success, solution, message = optimizer.optimize(time_limit_seconds=30)

    if success:
        # Save and return solution
        return {
            "success": True,
            "assignments": solution['assignments'],
            "message": message
        }
    else:
        # Get AI advice
        diagnostics = optimizer.get_diagnostics()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:8001/analyze-planning",
                    json={
                        "planning_id": planning_id,
                        "month": planning.month,
                        "year": planning.year,
                        "failure_message": message,
                        "time_limit_seconds": 30,
                        "strategies_attempted": ["Full constraints", "Relaxed"],
                        "min_daily_coverage": 3,
                        **diagnostics
                    }
                )

                if response.status_code == 200:
                    advice = response.json()

                    return {
                        "success": False,
                        "message": message,
                        "ai_analysis": {
                            "root_cause": advice['root_cause_summary'],
                            "critical_issues": advice['critical_issues'],
                            "suggestions": advice['relaxation_suggestions']
                        }
                    }
        except Exception as e:
            print(f"AI orchestrator unavailable: {e}")

        return {
            "success": False,
            "message": message
        }
```

## API Reference

### POST /analyze-planning

Full diagnostic analysis with constraint relaxation suggestions.

**Request Body:**
```json
{
  "planning_id": 4,
  "month": 12,
  "year": 2025,
  "failure_message": "No solution found (INFEASIBLE)",
  "time_limit_seconds": 30,
  "strategies_attempted": ["strategy_a_base", "strategy_b_relax"],
  "employees": [...],
  "total_employees": 18,
  "intern_count": 2,
  "daily_diagnostics": [...],
  "min_daily_coverage": 3
}
```

**Response:**
```json
{
  "analysis_timestamp": "2025-02-10T14:30:00Z",
  "planning_id": 4,
  "root_cause_summary": "Insufficient employee capacity combined with strict consecutive days constraint",
  "critical_issues": [
    "Capacity gap of 1-2 employees on 5 critical days",
    "2 interns at school reducing available pool",
    "Max 5 consecutive work days limits scheduling flexibility"
  ],
  "relaxation_suggestions": [
    {
      "priority": 1,
      "constraint_to_relax": "Minimum Daily Coverage",
      "relaxation_strategy": "Reduce min_daily_coverage from 3 to 2 for capacity gap days",
      "description": "Temporarily allow 2 staff on days with insufficient capacity",
      "expected_impact": "Will eliminate capacity gaps and allow feasible solution",
      "implementation_code": "optimizer.min_daily_coverage = 2",
      "risk_level": "low"
    }
  ],
  "long_term_recommendations": [
    "Consider hiring additional part-time staff to improve capacity margins",
    "Review intern school schedules for better coverage alignment"
  ],
  "reasoning_trace": "Step 1: Analyzed capacity diagnostics..."
}
```

### POST /quick-advice

Fast advice without full diagnostics (for development/testing).

**Query Parameters:**
- `failure_message` (string): Error message from optimizer
- `strategies_attempted` (array): List of strategy names tried

**Response:**
```json
{
  "advice": "Try relaxing the minimum coverage constraint or allowing 4 consecutive work days on weekends.",
  "timestamp": "2025-02-10T14:30:00Z"
}
```

## Example: Running the Integration

```bash
# Terminal 1: Start AI orchestrator
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning
docker-compose up

# Terminal 2: Run Django with AI integration
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/inur.django
source venv/bin/activate
python fastapi_app/planning/ai_orchestrator_example.py
```

Expected output:
```
================================================================================
EXAMPLE: Optimizer with AI Orchestrator Fallback
================================================================================

🤖 Running optimizer for planning 4 (12/2025)...
❌ Optimization failed: No solution found (INFEASIBLE)
🧠 Consulting AI orchestrator for guidance...

================================================================================
🧠 AI ORCHESTRATOR ANALYSIS
================================================================================

📊 Root Cause:
   Insufficient employee capacity on 5 critical days combined with strict
   weekend OFF policy

⚠️  Critical Issues:
   • Capacity gap of 1-2 employees on days 1, 5, 12, 20, 28
   • 2 interns at school reducing available pool
   • Weekend constraint removes 8 days from optimization space

💡 Suggested Relaxation Strategy Ladder:
   (Try in order of priority)

   1. Minimum Daily Coverage
      Strategy: Allow 2 employees instead of 3 on low-demand days
      Impact: Will allow optimizer to find feasible solution
      Risk: low

   2. Consecutive Work Days
      Strategy: Allow 6 consecutive work days instead of 5
      Impact: Increases scheduling flexibility by 20%
      Risk: medium

================================================================================
```

## Production Deployment

### Docker Compose Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  ai-planning:
    image: nuno-ai-planning:latest
    restart: always
    environment:
      - LLM_PROVIDER=deepseek
      - LLM_MODEL=deepseek-reasoner
      - LLM_API_KEY=${LLM_API_KEY}
    networks:
      - nuno-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  django-backend:
    # Your existing Django service
    environment:
      - AI_ORCHESTRATOR_URL=http://ai-planning:8001
    depends_on:
      - ai-planning

networks:
  nuno-network:
    external: true
```

### Environment Variables

```bash
# Add to your Django .env
AI_ORCHESTRATOR_URL=http://localhost:8001  # or http://ai-planning:8001 in Docker
AI_ORCHESTRATOR_ENABLED=true
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs -f ai-planning

# Common issues:
# 1. Missing API key
echo "LLM_API_KEY=your_key_here" >> .env

# 2. Port conflict
# Edit docker-compose.yml and change port 8001 to another port
```

### Can't connect from Django

```bash
# Test connectivity
curl http://localhost:8001/health

# If using Docker network
docker exec -it <django-container> curl http://ai-planning:8001/health
```

### LLM API errors

```bash
# Test API key
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-reasoner", "messages": [{"role": "user", "content": "test"}]}'
```

## Cost Optimization

### DeepSeek Pricing (Recommended)
- **Cost**: ~$0.50-1.00 per analysis
- **Speed**: 5-10 seconds per request
- **Quality**: Excellent for constraint reasoning

### Usage Tips
1. Cache analyses for similar failure patterns
2. Use `/quick-advice` endpoint for development ($0.05 per call)
3. Only call orchestrator for persistent failures (not first-attempt INFEASIBLE)
4. Batch multiple planning analyses when possible

## Next Steps

1. **Start simple**: Use `/quick-advice` endpoint first to test
2. **Add logging**: Log all AI suggestions for future analysis
3. **Implement auto-retry**: Automatically apply suggested relaxations
4. **Monitor effectiveness**: Track which suggestions resolve INFEASIBLE issues
5. **Fine-tune prompts**: Adjust orchestrator prompts based on your domain

For more details, see the full README at `/Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning/README.md`
