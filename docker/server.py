"""
FastAPI server for LLM-based planning optimization orchestration.

This service acts as an AI coach/orchestrator that:
1. Analyzes diagnostic data from failed optimizer runs
2. Uses LLM reasoning to suggest constraint relaxations
3. Provides strategic guidance for resolving INFEASIBLE planning problems
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from orchestrator import PlanningOrchestrator

app = FastAPI(
    title="Nuno AI Planning Orchestrator",
    description="LLM-powered constraint relaxation advisor for shift planning optimization",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = PlanningOrchestrator(
    api_key=os.getenv("LLM_API_KEY"),
    provider=os.getenv("LLM_PROVIDER", "deepseek"),  # deepseek, openai, anthropic
    model=os.getenv("LLM_MODEL", "deepseek-reasoner")
)


# ============================================================================
# Request/Response Models
# ============================================================================

class EmployeeInfo(BaseModel):
    """Employee information for diagnostics"""
    id: int
    abbreviation: str
    contract_hours_per_week: float
    contract_hours_per_day: float
    is_intern: bool = False
    school_days: Optional[List[int]] = None  # Days with school (1-31)


class DayDiagnostic(BaseModel):
    """Daily capacity diagnostic"""
    day: int
    weekday: str
    required_coverage: int
    available_employees: int
    intern_school_count: int
    holiday_requests: int
    effective_capacity: int
    capacity_gap: int
    is_weekend: bool
    is_holiday: bool = False


class ConstraintViolation(BaseModel):
    """Detected constraint violation"""
    constraint_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    affected_employees: Optional[List[int]] = None
    affected_days: Optional[List[int]] = None


class OptimizerDiagnosticRequest(BaseModel):
    """Request for LLM analysis of failed optimization"""
    planning_id: int
    month: int
    year: int

    # Optimizer failure info
    failure_message: str
    time_limit_seconds: int
    strategies_attempted: List[str]

    # Employee context
    employees: List[EmployeeInfo]
    total_employees: int
    intern_count: int

    # Daily diagnostics
    daily_diagnostics: List[DayDiagnostic]

    # Coverage requirements
    min_daily_coverage: int
    max_daily_coverage: Optional[int] = None

    # Constraint violations (if detected)
    constraint_violations: Optional[List[ConstraintViolation]] = None

    # Manual/fixed shifts
    manual_shift_count: int = 0

    # Additional context
    notes: Optional[str] = None


class RelaxationSuggestion(BaseModel):
    """Suggested constraint relaxation"""
    priority: int  # 1=highest, lower numbers = try first
    constraint_to_relax: str
    relaxation_strategy: str
    description: str
    expected_impact: str
    implementation_code: Optional[str] = None
    risk_level: str  # 'low', 'medium', 'high'


class OptimizerAdviceResponse(BaseModel):
    """LLM-generated advice for optimization"""
    analysis_timestamp: str
    planning_id: int

    # Root cause analysis
    root_cause_summary: str
    critical_issues: List[str]

    # Suggested strategy ladder
    relaxation_suggestions: List[RelaxationSuggestion]

    # Additional recommendations
    long_term_recommendations: List[str]

    # LLM reasoning (if available)
    reasoning_trace: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Nuno AI Planning Orchestrator",
        "status": "running",
        "version": "1.0.0",
        "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
        "llm_model": os.getenv("LLM_MODEL", "deepseek-reasoner")
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_configured": orchestrator.is_configured(),
    }


@app.post("/analyze-planning", response_model=OptimizerAdviceResponse)
async def analyze_planning(request: OptimizerDiagnosticRequest):
    """
    Analyze failed planning optimization and suggest constraint relaxations.

    This endpoint receives diagnostic data from a failed optimizer run and uses
    LLM reasoning to suggest strategic constraint relaxations.
    """
    try:
        # Generate analysis
        advice = await orchestrator.analyze_and_suggest(request.dict())

        return OptimizerAdviceResponse(
            analysis_timestamp=datetime.utcnow().isoformat(),
            planning_id=request.planning_id,
            root_cause_summary=advice["root_cause_summary"],
            critical_issues=advice["critical_issues"],
            relaxation_suggestions=[
                RelaxationSuggestion(**suggestion)
                for suggestion in advice["relaxation_suggestions"]
            ],
            long_term_recommendations=advice.get("long_term_recommendations", []),
            reasoning_trace=advice.get("reasoning_trace")
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze planning: {str(e)}"
        )


@app.post("/quick-advice")
async def quick_advice(failure_message: str, strategies_attempted: List[str]):
    """
    Quick advice endpoint for immediate guidance without full diagnostics.

    Useful for fast feedback during development/debugging.
    """
    try:
        advice = await orchestrator.quick_advice(failure_message, strategies_attempted)
        return {
            "advice": advice,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate advice: {str(e)}"
        )


@app.get("/supported-providers")
async def get_supported_providers():
    """Get list of supported LLM providers"""
    return {
        "providers": [
            {
                "name": "ollama",
                "models": ["llama3.1:8b", "qwen2.5:14b", "llama3.1:70b"],
                "recommended": True,
                "type": "local",
                "cost": "$0",
                "description": "Local LLM running on your server - no API costs, full privacy"
            },
            {
                "name": "deepseek",
                "models": ["deepseek-reasoner", "deepseek-chat"],
                "recommended": False,
                "type": "cloud",
                "cost": "$0.50-1.00 per analysis",
                "description": "DeepSeek reasoning model with chain-of-thought"
            },
            {
                "name": "openai",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "recommended": False,
                "type": "cloud",
                "cost": "$2.00-5.00 per analysis",
                "description": "OpenAI GPT models"
            },
            {
                "name": "anthropic",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "recommended": False,
                "type": "cloud",
                "cost": "$1.00-3.00 per analysis",
                "description": "Anthropic Claude models"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
