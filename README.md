# AgentShield, Firewall for AI Agent Spending

Stop runaway AI agents before they burn your budget. 10 composable rules evaluated per-transaction in <1ms. Pure Python stdlib, zero dependencies.

> **Project consolidation:** AgentShield's spend-control work has been consolidated into [sipi.bot](https://sipi.bot/pilot?source=agentshield-github). The Python package and test fixtures remain available for existing users, but AgentShield no longer has a separate hosted offer, funnel, or distribution program. New implementation work runs through the single paid sipi.bot pilot.

## Install

```bash
pip install agentshield-spend
```

(The import name is `agentshield`, the PyPI name `agentshield` belongs to an unrelated project.)

## Quick Start

```python
from agentshield import SpendControlEngine

engine = SpendControlEngine()

# A transaction your agent wants to make
transaction = {
    "amount": 500.00,
    "merchant": "openai-api",
    "category": "llm_inference",
    "agent_id": "my-agent",
    "timestamp": "2026-08-10T10:00:00Z",
}

# Your spend-control rules
rules = [
    {"id": "r1", "type": "transaction_limit", "priority": 1,
     "params": {"max_amount": 250}, "action": "BLOCK"},
    {"id": "r2", "type": "daily_total", "priority": 2,
     "params": {"max_daily": 2000}, "action": "BLOCK"},
    {"id": "r3", "type": "velocity", "priority": 3,
     "params": {"window_minutes": 60, "max_count": 10}, "action": "FLAGGED"},
]

# Prior transactions today (for daily_total and velocity checks)
prior_transactions = []

# Evaluate, returns in <1ms
result = engine.evaluate(transaction, rules, prior_transactions)
print(result["decision"])  # BLOCKED
print(result["reason"])    # Transaction amount $500.00 exceeds limit of $250.00
```

## Rule Types (10)

| Rule | Description | Example Params |
|------|-------------|----------------|
| `transaction_limit` | Block single calls over $X | `{"max_amount": 500}` |
| `daily_total` | Cap cumulative daily spend | `{"max_daily": 2000}` |
| `velocity` | Detect burst patterns | `{"window_minutes": 60, "max_count": 10}` |
| `merchant_allowlist` | Only approved API providers | `{"allowed": ["openai-api", "anthropic-api"]}` |
| `category_block` | Block spend categories | `{"blocked": ["crypto_exchange"]}` |
| `session_budget` | Per-session spend cap with decay | `{"max_session": 100, "decay_factor": 0.3}` |
| `cascade_cost` | Expected value with retry cost | `{"max_cascade_cost": 100, "fail_probability": 0.3, "reversal_cost": 200}` |
| `hitl_threshold` | Escalate to human review past a spend threshold | `{"max_budget": 500, "mode": "on_threshold", "threshold": 0.15}` |
| `replay` | Block duplicate transactions by nonce | `{"field": "nonce"}` |
| `circuit` | Deny all calls while the circuit is tripped | `{"state_field": "circuit_tripped"}` |

## Eval Gym (74 scenarios)

```python
from agentshield import run_eval

results = run_eval()
print(f"{results['passed']}/{results['total']} passed")  # 74/74
```

All 74 test scenarios are MIT licensed. Use them as test fixtures for your own spend-control implementation.

## Key Design Decisions

- **Pure Python 3.11 stdlib**, no pip install required (except for the package wrapper itself)
- **Decimal for money**, never float, always `decimal.Decimal`
- **Stateless**, no file I/O, no network, no global state
- **Deterministic**, same inputs always produce the same output
- **<1ms per evaluation**

## Links

- [Canonical product](https://sipi.bot)
- [Paid implementation pilot](https://sipi.bot/pilot?source=agentshield-github)
- [sipi.bot public eval report](https://sipi.bot/eval-report/)
- [GitHub](https://github.com/kindrat86/agentshield)

## License

MIT
