"""
AgentShield LangChain Callback Handler
=======================================
Intercepts LLM calls in LangChain/LangGraph pipelines and evaluates
each transaction against AgentShield spend rules BEFORE execution.

Usage:
    from agent_shield_callback import AgentShieldCallback

    callback = AgentShieldCallback(
        endpoint="https://agentshield.fly.dev",
        api_key="your-agent-api-key",
    )

    llm = ChatOpenAI(callbacks=[callback])

If a transaction is blocked by a spend rule, the callback raises
AgentShieldBlockException, preventing the API call from executing.
"""

import json
import urllib.request
from typing import Any, Dict, Optional, Union
from langchain_core.callbacks import BaseCallbackHandler


class AgentShieldBlockException(Exception):
    """Raised when AgentShield blocks a transaction based on spend rules."""
    pass


# Cost estimates per 1M tokens (input + output combined estimate)
MODEL_RATES = {
    "gpt-4o": 5.0,
    "gpt-4o-mini": 0.30,
    "gpt-4": 30.0,
    "gpt-3.5-turbo": 0.50,
    "claude-opus": 35.0,
    "claude-sonnet": 9.0,
    "claude-haiku": 0.50,
    "claude-3-5-sonnet": 9.0,
    "claude-3-opus": 35.0,
    "claude-3-haiku": 0.50,
}


class AgentShieldCallback(BaseCallbackHandler):
    """
    LangChain callback that evaluates each LLM call against AgentShield rules.

    Args:
        endpoint: AgentShield API endpoint (default: https://agentshield.fly.dev)
        api_key: AgentShield agent API key
        agent_id: Identifier for this agent (default: "langchain-agent")
    """

    def __init__(
        self,
        endpoint: str = "https://agentshield.fly.dev",
        api_key: str = "",
        agent_id: str = "langchain-agent",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id
        self._call_count = 0

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: list,
        *,
        run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Evaluate the upcoming LLM call against AgentShield rules."""
        # Extract model name
        model_name = self._extract_model_name(serialized, kwargs)

        # Estimate cost
        estimated_tokens = sum(len(p) // 4 for p in prompts)  # ~4 chars per token
        estimated_cost = self._estimate_cost(model_name, estimated_tokens)

        # Evaluate against rules
        decision = self._evaluate(estimated_cost, model_name)

        if decision.get("decision") == "BLOCK":
            raise AgentShieldBlockException(
                f"Transaction blocked by AgentShield: {decision.get('rule', 'unknown rule')} "
                f"(estimated cost: ${estimated_cost:.4f}, eval: {decision.get('evaluation_ms', 0)}ms)"
            )

        self._call_count += 1

    def _extract_model_name(self, serialized: Dict, kwargs: Dict) -> str:
        """Extract the model name from serialized LLM info."""
        # Try kwargs first (invocation params)
        model = kwargs.get("invocation_params", {}).get("model", "")
        if not model:
            model = kwargs.get("invocation_params", {}).get("model_name", "")
        if not model:
            # Try serialized
            model = serialized.get("name", "")
        return model.lower()

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost based on model and token count."""
        rate = MODEL_RATES.get(model, 5.0)  # Default to $5/M for unknown models
        return (tokens / 1_000_000) * rate

    def _evaluate(self, amount: float, merchant: str) -> Dict:
        """Call the AgentShield evaluation endpoint."""
        payload = json.dumps({
            "amount": amount,
            "merchant": merchant or "unknown",
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
            # Fail open: if AgentShield is unreachable, allow the transaction
            return {"decision": "ALLOWED", "rule": None, "evaluation_ms": 0}
