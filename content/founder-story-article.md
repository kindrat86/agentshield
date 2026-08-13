---
title: I Lost $2,800 in 60 Seconds to an AI Agent. Here's What I Built to Stop It.
published: true
tags: aiagents, costcontrol, python, opensource
description: After an AI agent drained my API budget while I slept, I built a per-transaction spend firewall. Here's the full story, the architecture, and 56 open-source test scenarios.
---

# I Lost $2,800 in 60 Seconds to an AI Agent

At 3:14 AM on a Tuesday, my phone buzzed. Not a notification I'd asked for, a billing alert from my API provider.

> Your API usage has reached $2,793.00 in the last hour.

I read that email at 6:17 AM. Three hours too late.

## What Happened

An AI agent I'd deployed that afternoon had entered a retry loop. It was calling a premium LLM endpoint that cost **$133 per call**. Each retry consumed the same 200K-token context window. And it retried **21 times** before the budget alert email even left the server.

The total damage: **$2,793.00** in 63 minutes.

Here's the thing that bothered me most: every system I had was working correctly.

- **API rate limits**: Fine. The provider was happy to take 21 calls at $133 each. Rate limits protect the provider, not me.
- **Budget alerts**: Set to trigger at $2,000. They triggered at 3:14 AM. The email arrived in my inbox. I just didn't see it until morning.
- **Observability dashboard**: Showed me exactly what happened, 21 calls, $133 each, starting at 3:01 AM. Beautiful graphs. Clear breakdown. Zero prevention.

Every tool was reactive. None of them could stop the transaction before it executed.

## The Problem With Observability

Tools like Helicone, LangSmith, and AgentOps are excellent at what they do: showing you what happened. Token counts, cost breakdowns, latency metrics. They're diagnostic tools.

But when an agent enters an infinite loop at 3 AM, diagnostics tell you **how** you lost $2,800. They don't stop the transaction.

The gap: nothing evaluates whether a transaction **should be allowed to execute** based on budget rules.

## What I Built

I built [AgentShield](https://github.com/kindrat86/agentshield), a per-transaction spend firewall that sits between your agent and the API.

Every API call is evaluated against configurable rules in under 1 millisecond. If a rule matches and the action is "block," the call never reaches the API provider. The agent gets a structured error. Your wallet stays closed.

### The Architecture

```
Agent → AgentShield → Rules Engine → API Provider
                ↓
         (evaluated in <1ms)
         BLOCK or ALLOW
```

The engine is pure Python 3.11 standard library. Zero dependencies. Runs on 256MB RAM. You can self-host it in 60 seconds.

### 9 Rule Types

1. **transaction_limit**, block any single call over $X
2. **daily_total**, cap cumulative spend per agent per day
3. **velocity**, flag if N+ calls happen in a time window
4. **merchant_allowlist**, only allow approved API providers
5. **category_block**, block entire spending categories
6. **session_budget**, session-scoped spend cap with decay tightening
7. **cascade_cost**, pre-dispatch EV: call_cost + fail_probability × reversal_cost
8. **clean_approval**, explicit allow for known-good patterns
9. **edge_cases**, precision handling for Decimal arithmetic edge cases

The last two rules, **session_budget** and **cascade_cost**, came from an engineer at HeartFlow who's building production cost-gating. Real-world rules from real-world pain.

### session_budget

Daily caps miss the "2 AM cron burst" pattern where one session eats the entire daily budget in minutes. Session-scoped budgets fix this by tracking spend per session. The decay tightening feature means the more an agent spends within a session, the lower the per-call threshold gets. The agent effectively gets a tighter leash as it spends more.

### cascade_cost

A $0.50 API call with a 30% failure rate and a $5 retry cost has an expected value of $2.00, not $0.50. The cascade_cost rule blocks calls that look cheap but compound on failure. The formula:

```
expected_cost = call_cost + (fail_probability × reversal_cost)
```

If expected_cost exceeds the threshold, the call is blocked.

## The Eval Gym: 56 Open-Source Test Scenarios

You can't claim "spend control" without test cases. So I wrote 56 of them.

The [Eval Gym](https://agentshield.fly.dev/eval) covers:

- **Clean approvals** (10 scenarios): transactions that should pass
- **Transaction limits** (8): edge cases around max amount
- **Daily totals** (8): cumulative spend tracking
- **Velocity** (8): burst detection
- **Merchant allowlists** (6): provider filtering
- **Category blocks** (6): category-level enforcement
- **Edge cases** (10): precision, timing, concurrent transactions
- **Session budgets** (6): session-scoped enforcement
- **Cascade cost** (4): expected value calculations

All MIT licensed. You can grab the raw test definitions from [tests/eval_gym.py](https://github.com/kindrat86/agentshield/blob/main/tests/eval_gym.py) and use them to test YOUR spend-control implementation.

A team called ZeroClaw actually implemented pre-flight budget enforcement after seeing this work. They merged a PR. That's the strongest validation possible, a team read the argument, agreed, and shipped code.

## Quick Start

```bash
pip install agentshield
```

```python
from agentshield import SpendControlEngine, run_eval

# Run all 56 eval scenarios
results = run_eval()
print(f"{results['passed']}/{results['total']} scenarios passed")

# Create your own engine
engine = SpendControlEngine()
engine.add_rule("limit", {
    "type": "transaction_limit",
    "params": {"max_amount": "500"},
    "action": "block"
})
```

## Links

- **GitHub (MIT)**: https://github.com/kindrat86/agentshield
- **Live demo + risk calculator**: https://agentshield.fly.dev
- **Eval gym (56 scenarios)**: https://agentshield.fly.dev/eval
- **Eval gym spec page**: https://agentshield.fly.dev/eval-gym-spec

## The Lesson

Observability is not enforcement. Dashboards are not firewalls. Alerts that arrive by email are not protection.

If you're running AI agents in production, you need something that evaluates each transaction **before** it executes. Not after.

I wish I'd built it before the $2,800 incident. But at least it's open source now, so you don't have to learn this lesson the expensive way.

---

*AgentShield is MIT licensed and built with pure Python 3.11 stdlib. The eval gym is a universal benchmark, steal whatever test cases help you. Feedback on the rule types is welcome.*
