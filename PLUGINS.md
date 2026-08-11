# AgentShield SDK Plugins

Drop-in integrations for popular AI agent frameworks. Each plugin evaluates transactions against AgentShield spend rules **before** API calls execute.

## Quick Start

1. Deploy AgentShield (or use the managed instance at `https://agentshield.fly.dev`)
2. Register an account and create an agent API key
3. Configure spend rules (transaction limits, daily caps, velocity detection)
4. Install the plugin for your framework

## LangChain Callback Handler

**File:** `plugins/langchain/agent_shield_callback.py`

Intercepts every `on_llm_start` event in LangChain/LangGraph pipelines, estimates the cost based on the model and prompt length, and checks it against your AgentShield rules.

```python
from agent_shield_callback import AgentShieldCallback

callback = AgentShieldCallback(
    endpoint="https://agentshield.fly.dev",
    api_key="as_your_agent_api_key",
    agent_id="my-langchain-agent",
)

# Attach to any LLM
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o", callbacks=[callback])

# Or attach to a chain
chain = prompt | llm | output_parser
result = chain.invoke({"input": "Hello"})  # Each call is evaluated
```

If a transaction violates a rule (e.g., exceeds the $500 transaction limit), the callback raises `AgentShieldBlockException`, preventing the API call.

### Supported Models

Cost estimation is built in for: GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5-turbo, Claude Opus/Sonnet/Haiku. Unknown models default to $5/1M tokens.

## CrewAI Tool Wrapper

**File:** `plugins/crewai/agent_shield_tool.py`

Wraps CrewAI tool execution with spend checking. Use as a decorator or context manager.

### As a decorator:

```python
from agent_shield_tool import AgentShieldGuard, shield_tool

guard = AgentShieldGuard(
    endpoint="https://agentshield.fly.dev",
    api_key="as_your_agent_api_key",
)

@shield_tool(guard, estimated_cost=0.05, merchant="openai-api")
def expensive_search(query: str) -> dict:
    return search_client.search(query)
```

### As a context manager:

```python
with guard.spend_limit(estimated_cost=0.10, merchant="anthropic-api"):
    result = anthropic_client.messages.create(...)
```

## OpenClaw Plugin

**File:** `integrations/openclaw/agentshield-plugin.ts`

TypeScript plugin for OpenClaw's gateway. Intercepts model dispatch and evaluates estimated cost against rules.

Config in `openclaw.json`:
```json
{
  "plugins": {
    "agentshield": {
      "endpoint": "https://agentshield.fly.dev",
      "apiKey": "${AGENTSHIELD_API_KEY}",
      "rules": {
        "transactionLimit": 100,
        "dailyCap": 2000,
        "velocityThreshold": 10
      }
    }
  }
}
```

## Architecture

All plugins follow the same pattern:

```
Your Agent → Plugin intercepts call → AgentShield evaluates (<1ms) → ALLOW or BLOCK
```

The evaluation is synchronous and adds <1ms latency. If AgentShield is unreachable, plugins fail open (allow the transaction) to prevent downtime.

## Configuration

Spend rules are configured in the AgentShield dashboard or via API:

| Rule | Description | Example |
|------|-------------|---------|
| Transaction Limit | Block any single call over $X | `$500 max per call` |
| Daily Total | Cap cumulative spend per agent per day | `$2,000 max per day` |
| Velocity | Flag if N+ calls in a window | `10 calls per hour` |
| Merchant Allowlist | Only allow approved API providers | `openai-api, anthropic-api` |
| Category Block | Block entire categories | `crypto, gambling` |

## Installation

### From source:
```bash
git clone https://github.com/kindrat86/agentshield.git
cd agentshield
```

### Python (pip install coming soon):
```bash
pip install agentshield-langchain  # Coming soon
pip install agentshield-crewai     # Coming soon
```

## Links

- [Risk Calculator](https://agentshield.fly.dev/tools/risk-calculator/)
- [Eval Gym (50/50)](https://agentshield.fly.dev/eval)
- [GitHub](https://github.com/kindrat86/agentshield)
- [Architecture Article](https://dev.to/maryan_k_bef6cf83fa64e809)
