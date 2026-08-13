# At 3 AM, My AI Agent Spent $2,800 in 60 Seconds. Here's What I Built to Stop It.

*August 11, 2026*

At 3 AM last Tuesday, an AI agent I built made 21 API calls to a premium LLM endpoint. Each call cost $133. That's $2,800 gone in 60 seconds, while I was asleep.

The budget alert email arrived at 6:14 AM. By then, the agent had already moved on to its next task, oblivious to the damage.

This is the dark side of autonomous AI agents. They're powerful, fast, and relentless, and they can drain your budget before you even wake up.

## Why Existing Tools Fail for Autonomous Agents

I tried everything before building my own solution:

**API rate limits** kicked in too late. By the time the provider's rate limiter engaged, 18 of the 21 calls had already gone through. Rate limits are designed to protect the provider's infrastructure, not your wallet.

**Budget alert emails** arrived hours after the damage was done. Email is asynchronous by design, it's the wrong medium for real-time cost control.

**Manual monitoring** doesn't scale. I was running 7 agents across 3 projects. Checking dashboards every hour isn't a system; it's a job.

The fundamental problem: none of these tools evaluate **each individual transaction** before it executes. They're reactive, not preventive.

## The 7-Rule Framework

I built AgentShield around 5 composable rule types (the engine supports 7 total, including the 2 most common aliases). Each rule is evaluated per-transaction, in priority order. First match wins.

### 1. Transaction Limit

Blocks any single transaction that exceeds a maximum amount.

```json
{
  "type": "transaction_limit",
  "params": {"max_amount": 500.00},
  "action": "BLOCK"
}
```

This is your first line of defense against runaway spending. If a single API call costs more than $500, it's blocked before it executes.

### 2. Daily Total

Tracks cumulative spend per agent per day. When the daily total exceeds the cap, all further transactions are blocked.

```json
{
  "type": "daily_total",
  "params": {"max_daily": 2000.00},
  "action": "BLOCK"
}
```

This prevents death-by-a-thousand-cuts, the scenario where individual transactions are small but the cumulative spend is massive.

### 3. Velocity

Counts transactions in a rolling time window. If an agent fires too many calls too quickly, it gets flagged.

```json
{
  "type": "velocity",
  "params": {"window_minutes": 60, "max_count": 10},
  "action": "FLAGGED"
}
```

Velocity catches the $2,800-in-60-seconds scenario. Instead of blocking, you can set it to FLAG, letting the transaction through but alerting you to investigate.

### 4. Merchant Allowlist

Only allows transactions to approved merchants. Everything else is blocked.

```json
{
  "type": "merchant_allowlist",
  "params": {"allowed": ["openai-api", "anthropic-api", "stripe-api"]},
  "action": "BLOCK"
}
```

If your agent is only supposed to talk to OpenAI and Anthropic, any call to `unknown-proxy.com` is blocked instantly.

### 5. Category Block

Blocks specific categories of spending entirely.

```json
{
  "type": "category_block",
  "params": {"blocked": ["crypto_exchange", "adult_content", "gambling"]},
  "action": "BLOCK"
}
```

### How They Compose

Rules are evaluated in priority order. Lower number = higher priority. First match wins. This means you can layer defenses:

- Priority 1: Transaction limit ($500 max per call)
- Priority 2: Daily total ($2,000 max per day)
- Priority 3: Velocity (max 10 calls per hour)
- Priority 4: Merchant allowlist (only approved APIs)
- Priority 5: Category block (no crypto/gambling)

If a transaction violates multiple rules, the highest-priority rule fires first. This gives you predictable, debuggable behavior.

## The Eval Gym: 50 Labeled Scenarios

To prove the engine works, I built a test suite of 50 scenarios covering real-world agent behaviors:

| Category | Scenarios | Pass Rate |
|----------|-----------|-----------|
| clean_approval | 10 | 100% |
| transaction_limit_block | 8 | 100% |
| daily_total_block | 7 | 100% |
| velocity_flag | 6 | 100% |
| merchant_allowlist_block | 7 | 100% |
| category_block | 7 | 100% |
| edge_cases | 5 | 100% |
| **Overall** | **50** | **100%** |

The edge cases are where the engine proves its correctness:

- **Amount exactly at limit** ($500.00 vs $500 limit) → APPROVED (not strictly greater)
- **Amount $0.01 over limit** ($500.01 vs $500 limit) → BLOCKED
- **Missing amount field** → FLAGGED (graceful degradation)
- **Empty rules list** → APPROVED (fail-open for legitimate use)
- **Two rules at same priority** → First in list wins (deterministic)

## The Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  AI Agent    │────▶│  AgentShield │────▶│  API Provider │
│              │     │   Engine     │     │  (OpenAI etc) │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │  Rule Store  │
                     │  (SQLite WAL)│
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │  Dashboard   │
                     │  (SSE feed)  │
                     └──────────────┘
```

Every transaction flows through the engine before reaching the provider. The engine evaluates it against the account's rules in under 1ms, records the decision, and broadcasts blocked/flagged events via Server-Sent Events to the dashboard.

### Key design decisions:

- **Python 3.11 stdlib only**, no pip install required on the server. The entire engine, storage, auth, and API run on the standard library.
- **SQLite in WAL mode**, thread-safe, zero-config storage. Multi-tenant isolation enforced at the query level (every query scopes by `account_id`).
- **Decimal for money**, never use float for monetary arithmetic. The engine uses `decimal.Decimal` throughout.
- **Offline licensing**, HMAC-SHA256 signed license keys validated locally. No server dependency for license checks.

## Try It Yourself

**[Risk Calculator →](/tools/risk-calculator/)**, See your agent spend risk profile in 30 seconds. No signup required.

**[Dashboard →](/dashboard)**, Register for a free account and configure your own rules.

The core engine is open-source and runs on Python 3.11 stdlib. No dependencies. No frameworks. Just 7 composable rules, evaluated fast. **[56/56 eval gym results →](/eval)**

---

*AgentShield: A firewall for AI agent spending. Built because budget alerts shouldn't arrive by email.*
