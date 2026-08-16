---
title: 56 Test Scenarios for AI Agent Spend Control (MIT Licensed, Steal Them)
published: true
tags: ai, agents, testing, opensource
canonical_url: https://agentshield.fly.dev/eval-gym-spec
---

## The Problem With Testing Agent Spend Controls

You built a cost-gating layer for your AI agents. You set a daily limit, a per-call cap, and a velocity check. How do you know it actually works?

Most teams test their spend controls by... not testing them. They set the limits, deploy, and wait for a billing surprise to reveal the gaps. That's how one of my agents spent $2,800 in 60 seconds while I was asleep, the "controls" I had (a budget alert email) fired 40 minutes after the money was gone.

So we wrote **74 labeled test scenarios**, covering **10 spend-control rule types**, and open-sourced them. MIT licensed. You can copy them into your test suite today.

Each scenario specifies a transaction, a rule set, prior transactions, and the expected decision (`APPROVED`, `BLOCKED`, or `FLAGGED`). If your enforcement engine returns something else, you have a gap.

## The 9 Rule Types

### 1. Clean Approval (10 scenarios)

Not a rule type per se, these test that your engine doesn't produce **false positives** on legitimate activity. A $10 API call to an approved merchant with plenty of daily budget left must be APPROVED. An engine that blocks everything is trivially "safe" and completely useless.

### 2. Transaction Limit (8 scenarios)

Block any single call exceeding a max amount. The first line of defense against expensive model calls.

```json
{"type": "transaction_limit", "params": {"max_amount": 500.00}, "action": "BLOCK"}
```

The scenario that catches bugs: amount **exactly at** the limit. $500.00 against a $500 limit → APPROVED (not strictly greater). $500.01 → BLOCKED. Half the hand-rolled implementations we've seen get this boundary wrong.

### 3. Daily Total (7 scenarios)

Cap cumulative spend per agent per calendar day. Catches death-by-a-thousand-cuts patterns where no single call is alarming but the sum is.

### 4. Velocity / Burst Detection (6 scenarios)

Count transactions in a rolling window. This is the rule that catches retry storms and infinite loops, the $2,800-in-60-seconds pattern.

```json
{"type": "velocity", "params": {"window_minutes": 60, "max_count": 10}, "action": "FLAGGED"}
```

Note the action: velocity typically **FLAGS** rather than blocks, the call proceeds, but an alert fires. A burst can be legitimate (batch job) or catastrophic (loop). The scenarios test both directions.

### 5. Merchant Allowlist (7 scenarios)

Only allow calls to approved API providers. Blocks calls to unknown proxies, unauthorized endpoints, or silently-substituted model variants.

### 6. Category Block (7 scenarios)

Block entire categories of spend. Enterprise policy territory: no crypto exchanges, no gambling, no unapproved data vendors.

### 7. Session Budget (3 scenarios)

Session-scoped spend caps with optional **decay tightening**: when remaining session budget falls below `decay_factor × max_session`, the per-call threshold shrinks proportionally. This prevents a single expensive call from consuming the last of the budget. Addresses the "2 AM cron burst" pattern where one agent session eats a whole day's budget in one run.

### 8. Cascade Cost (3 scenarios)

Pre-dispatch expected-value estimation:

```
cascade_cost = call_cost + (fail_probability × reversal_cost)
```

A $50 call with 30% failure probability and $200 reversal cost has a cascade cost of $110. If your threshold is $100, block it, the *expected* cost of dispatching exceeds what the sticker price suggests. This rule type came directly from a conversation with an engineer building production cost-gating; it's the difference between gating on price and gating on risk.

### 9. Edge Cases (5 scenarios)

The category that will actually bite you:

- **Boundary values**, amount exactly at limit (covered above, but tested independently)
- **Missing fields**, transaction with no `amount` field → FLAGGED, never crash, never silently approve
- **Empty rulesets**, no rules configured → APPROVED (fail-open, documented and deliberate; you may want fail-closed, the point is the scenario forces you to *decide*)
- **Priority ties**, two rules with the same priority → first in list wins, deterministically
- **Malformed inputs**, garbage in the amount field → FLAGGED with a reason, not an unhandled exception

If your spend-control engine hasn't been tested against malformed input, it *has* been tested against malformed input, just in production, later, by an agent.

## How to Use These Scenarios

```bash
pip install agentshield-spend
```

```python
from agentshield import run_eval
results = run_eval()
print(f"{results['passed']}/{results['total']} passed")
# 74/74 passed
```

Or skip the package entirely and copy the scenarios from [`tests/eval_gym.py`](https://github.com/kindrat86/agentshield/blob/main/tests/eval_gym.py), they're plain Python dicts with no dependencies, easy to port to any language or test framework. MIT licensed.

The scenarios are engine-agnostic by design: transaction in, rules in, prior transactions in, decision out. If your enforcement layer can express that contract, the 74 scenarios can validate it.

## The Bigger Picture

Post-facto observability tools (LangSmith, Helicone) tell you what went wrong AFTER it happens. Pre-flight enforcement stops the transaction BEFORE the API call executes. Both have their place, but only one of them prevents the bill.

These 74 scenarios exist to answer one question: **does your enforcement layer actually enforce?** Most teams assume yes. The edge-cases category, in our experience, says otherwise about one time in two.

- Full spec (all 12 categories with JSON structures and formulas): https://agentshield.fly.dev/eval-gym-spec
- Live eval run: https://agentshield.fly.dev/eval
- GitHub (MIT): https://github.com/kindrat86/agentshield

If you find a failure mode these scenarios don't cover, open an issue, the benchmark gets better with every gap someone finds.
