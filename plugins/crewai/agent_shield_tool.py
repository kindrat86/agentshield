"""
AgentShield CrewAI Tool Wrapper
================================
Wraps CrewAI agent tool execution to validate expected API spend
before the tool is allowed to fire.

Usage:
    from agent_shield_tool import AgentShieldGuard, shield_tool

    guard = AgentShieldGuard(
        endpoint="https://agentshield.fly.dev",
        api_key="your-agent-api-key",
    )

    # Decorate any tool:
    @shield_tool(guard, estimated_cost=0.05)
    def search_api(query: str) -> dict:
        return {"results": [...]}

    # Or use as a context manager:
    with guard.spend_limit(estimated_cost=0.10):
        result = my_expensive_api_call()
"""

import json
import urllib.request
from functools import wraps
from typing import Any, Callable, Optional


class AgentShieldBlockException(Exception):
    """Raised when AgentShield blocks a tool execution based on spend rules."""
    pass


class AgentShieldGuard:
    """
    Guards CrewAI tool execution by checking spend rules before each call.

    Args:
        endpoint: AgentShield API endpoint
        api_key: AgentShield agent API key
        agent_id: Identifier for this agent
    """

    def __init__(
        self,
        endpoint: str = "https://agentshield.fly.dev",
        api_key: str = "",
        agent_id: str = "crewai-agent",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id

    def check_spend(self, estimated_cost: float, merchant: str = "unknown") -> bool:
        """
        Evaluate a planned spend against AgentShield rules.
        Returns True if allowed, raises AgentShieldBlockException if blocked.
        """
        decision = self._evaluate(estimated_cost, merchant)

        if decision.get("decision") == "BLOCK":
            raise AgentShieldBlockException(
                f"Tool blocked by AgentShield: {decision.get('rule', 'unknown')} "
                f"(cost: ${estimated_cost:.4f}, eval: {decision.get('evaluation_ms', 0)}ms)"
            )
        return True

    def spend_limit(self, estimated_cost: float, merchant: str = "unknown"):
        """Context manager for guarding a block of code."""
        return _SpendLimitContext(self, estimated_cost, merchant)

    def _evaluate(self, amount: float, merchant: str) -> dict:
        """Call AgentShield evaluation endpoint."""
        payload = json.dumps({
            "amount": amount,
            "merchant": merchant,
            "agent_id": self.agent_id,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.endpoint}/v1/transactions/evaluate",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return {"decision": "ALLOWED", "rule": None, "evaluation_ms": 0}


class _SpendLimitContext:
    def __init__(self, guard: AgentShieldGuard, cost: float, merchant: str):
        self.guard = guard
        self.cost = cost
        self.merchant = merchant

    def __enter__(self):
        self.guard.check_spend(self.cost, self.merchant)
        return self

    def __exit__(self, *args):
        pass


def shield_tool(guard: AgentShieldGuard, estimated_cost: float = 0.01, merchant: str = "api"):
    """
    Decorator that wraps a CrewAI tool function with AgentShield spend checking.

    Args:
        guard: An AgentShieldGuard instance
        estimated_cost: Estimated cost per tool invocation
        merchant: Merchant identifier for the API being called

    Example:
        @shield_tool(guard, estimated_cost=0.05, merchant="openai-api")
        def call_llm(prompt: str) -> str:
            return openai_client.chat.completions.create(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            guard.check_spend(estimated_cost, merchant)
            return func(*args, **kwargs)
        return wrapper
    return decorator
