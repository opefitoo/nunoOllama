"""
LLM Orchestrator for Planning Optimization.

Uses LLM reasoning (DeepSeek, OpenAI, or Anthropic) to analyze constraint
programming failures and suggest strategic relaxations.
"""

import os
import json
from typing import Dict, List, Any, Optional
import httpx


class PlanningOrchestrator:
    """
    LLM-powered orchestrator that analyzes failed optimization runs
    and suggests constraint relaxation strategies.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "deepseek",
        model: Optional[str] = None
    ):
        """
        Initialize orchestrator with LLM provider.

        Args:
            api_key: API key for LLM provider
            provider: 'deepseek', 'openai', or 'anthropic'
            model: Specific model name (optional, uses defaults)
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.provider = provider.lower()
        self.model = model or self._get_default_model()

        # API key not required for local providers
        if self.provider not in ["ollama"] and not self.api_key:
            raise ValueError(f"API key required for {self.provider}")

        # Configure provider-specific settings
        self._configure_provider()

    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            "deepseek": "deepseek-reasoner",  # Best for constraint reasoning
            "openai": "gpt-4-turbo",
            "anthropic": "claude-3-opus-20240229",
            "ollama": "llama3.1:8b"  # Local LLM via Ollama
        }
        return defaults.get(self.provider, "deepseek-reasoner")

    def _configure_provider(self):
        """Configure provider-specific API settings"""
        if self.provider == "deepseek":
            self.api_base = "https://api.deepseek.com/v1"
        elif self.provider == "openai":
            self.api_base = "https://api.openai.com/v1"
        elif self.provider == "anthropic":
            self.api_base = "https://api.anthropic.com/v1"
        elif self.provider == "ollama":
            # Ollama uses OpenAI-compatible API
            self.api_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def is_configured(self) -> bool:
        """Check if orchestrator is properly configured"""
        return bool(self.api_key and self.provider and self.model)

    async def analyze_and_suggest(self, diagnostic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze failed optimization and suggest constraint relaxations.

        Args:
            diagnostic_data: Full diagnostic data from failed optimizer run

        Returns:
            Dict with root cause analysis and relaxation suggestions
        """
        # Build comprehensive prompt for LLM
        prompt = self._build_analysis_prompt(diagnostic_data)

        # Call LLM
        response = await self._call_llm(prompt)

        # Parse and structure response
        advice = self._parse_llm_response(response, diagnostic_data)

        return advice

    async def quick_advice(self, failure_message: str, strategies_attempted: List[str]) -> str:
        """
        Quick advice without full diagnostics.

        Args:
            failure_message: Error message from optimizer
            strategies_attempted: List of strategy names that failed

        Returns:
            Quick advice string
        """
        prompt = f"""You are an expert in constraint programming and shift scheduling optimization.

An optimization run failed with this message:
"{failure_message}"

Strategies already attempted:
{json.dumps(strategies_attempted, indent=2)}

Provide 2-3 quick suggestions for what to try next. Be specific and actionable.
"""

        response = await self._call_llm(prompt, max_tokens=500)
        return response.get("content", "No advice available")

    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for LLM"""

        # Extract key metrics
        employees = data.get("employees", [])
        daily_diagnostics = data.get("daily_diagnostics", [])
        constraint_violations = data.get("constraint_violations", [])

        # Calculate critical days (capacity gaps)
        critical_days = [
            d for d in daily_diagnostics
            if d["capacity_gap"] > 0
        ]

        # Weekend capacity
        weekend_days = [d for d in daily_diagnostics if d["is_weekend"]]

        prompt = f"""You are an expert in constraint programming and shift scheduling optimization using Google OR-Tools CP-SAT solver.

# CONTEXT: Failed Planning Optimization

## Planning Details
- Month: {data.get("month")}/{data.get("year")}
- Planning ID: {data.get("planning_id")}
- Time Limit: {data.get("time_limit_seconds")}s
- Failure Message: "{data.get("failure_message")}"

## Strategies Already Attempted
{json.dumps(data.get("strategies_attempted", []), indent=2)}

## Employee Pool
- Total Employees: {data.get("total_employees")}
- Interns: {data.get("intern_count")}
- Manual Shifts Already Set: {data.get("manual_shift_count", 0)}

## Coverage Requirements
- Minimum Daily Coverage: {data.get("min_daily_coverage")}
- Maximum Daily Coverage: {data.get("max_daily_coverage", "None")}

## Daily Capacity Analysis
Total days in month: {len(daily_diagnostics)}
Critical days (capacity gap > 0): {len(critical_days)}
Weekend days: {len(weekend_days)}

### Most Critical Days:
{self._format_critical_days(critical_days[:10])}

## Detected Constraint Violations
{self._format_violations(constraint_violations)}

## Key Constraints (Luxembourg Labor Law)
1. Maximum 5 consecutive work days
2. Minimum 2 consecutive OFF days (44h rest period)
3. No weekend work (all employees OFF on Sat/Sun)
4. Interns must have 'cours' shift on school days
5. Holiday requests must be honored
6. Contract hours must be respected (varying between 32-40h/week)

# YOUR TASK

Analyze this failed optimization and provide:

1. **Root Cause Analysis**: What is the fundamental reason this optimization is INFEASIBLE?

2. **Critical Issues**: List 3-5 critical issues (capacity gaps, conflicting constraints, etc.)

3. **Relaxation Strategy Ladder**: Suggest 4-6 constraint relaxations in priority order (1=try first):
   - What constraint to relax
   - How to relax it
   - Expected impact
   - Risk level (low/medium/high)
   - Specific implementation guidance

4. **Long-term Recommendations**: Suggest 2-3 structural improvements to prevent future failures

# OUTPUT FORMAT

Respond with valid JSON:

{{
  "root_cause_summary": "1-2 sentence summary of why this is INFEASIBLE",
  "critical_issues": [
    "Issue 1 description",
    "Issue 2 description",
    ...
  ],
  "relaxation_suggestions": [
    {{
      "priority": 1,
      "constraint_to_relax": "Name of constraint",
      "relaxation_strategy": "How to relax it",
      "description": "Detailed explanation",
      "expected_impact": "What this will achieve",
      "implementation_code": "Python code snippet if applicable",
      "risk_level": "low|medium|high"
    }},
    ...
  ],
  "long_term_recommendations": [
    "Recommendation 1",
    "Recommendation 2",
    ...
  ]
}}

Think step by step. Consider the capacity gaps, constraint interactions, and Luxembourg labor law requirements.
"""

        return prompt

    def _format_critical_days(self, critical_days: List[Dict]) -> str:
        """Format critical days for prompt"""
        if not critical_days:
            return "None"

        lines = []
        for day in critical_days:
            lines.append(
                f"Day {day['day']} ({day['weekday']}): "
                f"Need {day['required_coverage']}, "
                f"Available {day['effective_capacity']}, "
                f"GAP: {day['capacity_gap']}"
            )
        return "\n".join(lines)

    def _format_violations(self, violations: Optional[List[Dict]]) -> str:
        """Format constraint violations for prompt"""
        if not violations:
            return "None detected"

        lines = []
        for v in violations:
            lines.append(
                f"- [{v['severity'].upper()}] {v['constraint_type']}: {v['description']}"
            )
        return "\n".join(lines)

    async def _call_llm(self, prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Call LLM provider API.

        Args:
            prompt: Prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            LLM response dict
        """
        if self.provider == "deepseek":
            return await self._call_deepseek(prompt, max_tokens)
        elif self.provider == "openai":
            return await self._call_openai(prompt, max_tokens)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt, max_tokens)
        elif self.provider == "ollama":
            return await self._call_ollama(prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _call_deepseek(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Call DeepSeek API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert in constraint programming and optimization."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()

            # Extract content and reasoning if available
            message = data["choices"][0]["message"]
            return {
                "content": message.get("content", ""),
                "reasoning": message.get("reasoning_content", None)
            }

    async def _call_openai(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Call OpenAI API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert in constraint programming and optimization."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()

            message = data["choices"][0]["message"]
            return {
                "content": message.get("content", ""),
                "reasoning": None
            }

    async def _call_anthropic(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Call Anthropic API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()

            content = data["content"][0]["text"]
            return {
                "content": content,
                "reasoning": None
            }

    async def _call_ollama(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """
        Call Ollama API (OpenAI-compatible endpoint).

        Ollama provides a local LLM server with OpenAI-compatible API.
        No API key needed, runs entirely on your server.
        """
        async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for local inference
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Content-Type": "application/json"
                    # No Authorization header needed for Ollama
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert in constraint programming and optimization. Provide clear, structured analysis in JSON format when requested."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()

            message = data["choices"][0]["message"]
            return {
                "content": message.get("content", ""),
                "reasoning": None  # Ollama doesn't provide separate reasoning trace
            }

    def _parse_llm_response(self, response: Dict[str, Any], diagnostic_data: Dict) -> Dict[str, Any]:
        """
        Parse LLM response into structured advice.

        Args:
            response: Raw LLM response
            diagnostic_data: Original diagnostic data

        Returns:
            Structured advice dict
        """
        content = response.get("content", "")
        reasoning = response.get("reasoning", None)

        # Try to extract JSON from response
        try:
            # Find JSON block in response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                advice = json.loads(json_str)

                # Add reasoning trace if available
                if reasoning:
                    advice["reasoning_trace"] = reasoning

                return advice
            else:
                # No JSON found - structure response manually
                return self._fallback_parse(content, reasoning)

        except json.JSONDecodeError:
            return self._fallback_parse(content, reasoning)

    def _fallback_parse(self, content: str, reasoning: Optional[str]) -> Dict[str, Any]:
        """Fallback parser when JSON extraction fails"""
        return {
            "root_cause_summary": "Unable to parse structured response. See raw content below.",
            "critical_issues": [
                "LLM response could not be parsed into structured format"
            ],
            "relaxation_suggestions": [
                {
                    "priority": 1,
                    "constraint_to_relax": "Unknown",
                    "relaxation_strategy": content[:500],
                    "description": "Raw LLM response",
                    "expected_impact": "Unknown",
                    "risk_level": "unknown"
                }
            ],
            "long_term_recommendations": [],
            "reasoning_trace": reasoning,
            "raw_content": content
        }
