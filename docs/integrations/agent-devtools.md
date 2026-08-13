# AgentShield → Agent-Devtools integration schema (draft v1)

Goal: emit one structured event per spend evaluation so Agent-Devtools can render
AgentShield decisions as a first-class trace source — *"what did the firewall
block"* alongside *"what did the agent actually do."*

## What the engine produces today

`SpendControlEngine.evaluate(transaction, rules, prior_transactions)` returns a
single summary dict:

```json
{ "decision": "BLOCKED", "reason": "...", "rule_triggered": "r1", "severity": "high" }
```

- `decision` ∈ `APPROVED | BLOCKED | FLAGGED`
- `severity` ∈ `high | medium | none`

This is the **winning** decision only — the first rule to trigger (lowest
`priority` number) wins, and the per-rule reasoning that led there is not exposed.
That's the gap this schema fills for a visual tracer.

## Rule types (all live on `main`)

| `type` | fires when | key params |
|---|---|---|
| `transaction_limit` | single amount > cap | `max_amount` |
| `daily_total` | same-day cumulative spend > cap | `max_daily` |
| `velocity` | call count in rolling window > cap | `window_minutes`, `max_count` |
| `merchant_allowlist` | merchant NOT in allowlist | `allowed[]` |
| `category_block` | category in blocklist | `blocked[]` |
| `session_budget` | session cumulative spend > cap | `max_session`, `session_id`, `decay_factor`, `require_session_id` |
| `cascade_cost` | call + fail_prob × reversal > cap | `max_cascade_cost`, `fail_probability`, `reversal_cost` |

## Proposed event envelope (v1)

```json
{
  "schema_version": "1.0",
  "event_type": "agentshield.spend.evaluation",
  "event_id": "01J5XK2VZ...",
  "timestamp": "2026-08-13T10:30:00Z",
  "trace_id": "trace_42",
  "agent_id": "agent_7",
  "session_id": "sess_9",
  "transaction": {
    "id": "txn_1001",
    "amount": "500.00",
    "merchant": "openai-api",
    "category": "llm_inference",
    "timestamp": "2026-08-13T10:29:59Z"
  },
  "decision": {
    "decision": "BLOCKED",
    "reason": "Transaction amount $500.00 exceeds limit of $250.00",
    "rule_triggered": "r1",
    "severity": "high"
  },
  "evaluation": [
    { "rule_id": "r1", "type": "transaction_limit", "priority": 1, "outcome": "triggered", "detail": { "actual": "500.00", "limit": "250.00" } },
    { "rule_id": "r2", "type": "velocity", "priority": 2, "outcome": "not_reached", "detail": null }
  ]
}
```

Notes:

- `amount` and all money values are **strings** (Decimal-safe — the engine never
  uses float; keep that guarantee across the wire).
- `trace_id` is the join key into Agent-Devtools. `agent_id` / `session_id` /
  `transaction.id` are secondary correlation fields.
- `transaction` echoes the exact input; `decision` echoes the exact output.
- `session_budget` treats a `None` (or absent) `session_id` as a real "default"
  session: prior transactions with `session_id == None` are summed into the same
  bucket, so the cap cannot be bypassed by omitting the id. Setting the rule
  param `require_session_id: true` flips on a strict guardrail that blocks (or
  flags, per the rule `action`) any transaction whose `session_id` is missing.

## Pydantic model

```python
from pydantic import BaseModel
from typing import Literal, Optional

class TransactionEvent(BaseModel):
    id: Optional[str] = None
    amount: str                       # Decimal-safe string
    merchant: str
    category: str
    timestamp: Optional[str] = None
    metadata: dict = {}

class Decision(BaseModel):
    decision: Literal["APPROVED", "BLOCKED", "FLAGGED"]
    reason: str
    rule_triggered: Optional[str] = None
    severity: Literal["high", "medium", "none"]

class RuleEvaluation(BaseModel):
    rule_id: str
    type: str
    priority: int
    outcome: Literal["triggered", "passed", "skipped", "not_reached"]
    detail: Optional[dict] = None

class SpendEvaluationEvent(BaseModel):
    schema_version: str
    event_type: str
    event_id: str
    timestamp: str
    trace_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    transaction: TransactionEvent
    decision: Decision
    evaluation: list[RuleEvaluation]
```

## Per-rule evaluation trace (the value-add)

`evaluate()` returns only the winning rule. For a tracer to show *why* a run was
blocked — and what was **close** to blocking — we add an `evaluation` array that
records every rule's outcome:

- `triggered` — rule fired and produced the decision
- `passed` — rule evaluated, did not fire
- `skipped` — rule had absent/invalid params and was ignored
- `not_reached` — lower priority than the winning rule, never evaluated

`detail` is rule-type-specific (actual vs. threshold):

| `type` | `detail` fields |
|---|---|
| `transaction_limit` | `actual`, `limit` |
| `daily_total` | `daily_total`, `max_daily`, `date` |
| `velocity` | `count_in_window`, `window_minutes`, `max_count` |
| `merchant_allowlist` | `merchant`, `allowed` |
| `category_block` | `category`, `blocked` |
| `session_budget` | `session_total`, `max_session`, `session_id` |
| `cascade_cost` | `cascade_cost`, `max_cascade_cost`, `fail_probability`, `reversal_cost` |

> This per-rule trace is a **proposal** — the engine currently returns the winning
> decision only, so exposing it needs a thin emitter wrapper that re-runs each
> rule's check and records its outcome (the rule checks are already pure functions,
> so this is mechanical).

## Open questions for the integration

1. **Delivery** — ndjson stream (stdout/file) fits AgentShield's stdlib, zero-dependency
   ethos; a webhook push is possible but adds a dependency. Which does Agent-Devtools
   prefer to consume?
2. **`trace_id` join** — what correlation id does Agent-Devtools already use for its
   traces? Align the naming so a blocked AgentShield event links straight to the replay.
