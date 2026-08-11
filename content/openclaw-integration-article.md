# How I Built a Firewall That Blocks AI Agent Spend Before Each API Call — Now an OpenClaw Plugin

_August 11, 2026 · 4 min read_

Three weeks ago I shipped AgentShield, a per-transaction spend firewall for AI agents. Today it has a working OpenClaw plugin. Here is how the integration works and why I built it this way.

## The Problem OpenClaw Users Have

Issue #42475 on the OpenClaw repo has 15 comments and 2,800 reactions. The request: per-agent budget enforcement at the gateway level. Developers are running multiple agents and waking up to $200 overnight bills with no guardrails.

The comments describe three failure modes:

1. **Retry storms** — agent hits a 429, retries with full context each time, each retry costs more
2. **Context accumulation** — turn 40 costs 50x turn 1 from re-sending history
3. **Tool call loops** — agent gets stuck calling the same broken tool

None of these are caught by existing monitoring tools because they happen at the transaction level, not the session level. By the time LangSmith or Helicone shows you the graph, the money is already spent.

## The Architecture

The plugin is 80 lines of TypeScript that sits between OpenClaw's gateway and the model dispatch:

```
OpenClaw gateway → AgentShield plugin (evaluate) → model dispatch
                          ↓
                   ALLOW / BLOCK / FLAG
                          ↓
                   SSE alert to dashboard
```

The actual rules engine is pure Python 3.11 stdlib running on a separate endpoint. The plugin is just a thin evaluation client. This separation means the plugin adds no latency to OpenClaw's core loop — it fires an async HTTP call and continues.

## Configuration

Drop this into your `openclaw.json`:

```json
{
  "plugins": {
    "agentshield": {
      "endpoint": "https://agentshield.fly.dev",
      "apiKey": "${AGENTSHIELD_API_KEY}",
      "rules": {
        "transactionLimit": 100,
        "dailyCap": 2000,
        "velocityThreshold": 10,
        "merchantAllowlist": ["openai-api", "anthropic-api"]
      }
    }
  }
}
```

That is it. No code changes to OpenClaw. The plugin intercepts `beforeModelDispatch`, evaluates the estimated cost against your rules, and returns ALLOW or BLOCK in under 1ms.

## What Gets Evaluated

The plugin sends three things to the rules engine before each model call:

- **Estimated cost** — calculated from the model tier and token estimate
- **Provider** — "anthropic-api", "openai-api", etc. for merchant allowlisting
- **Session cost so far** — for daily cap enforcement

The engine evaluates these against 7 composable rules, in priority order:

1. Transaction limit — block any single call over $X
2. Daily total — cap cumulative spend per agent per day
3. Velocity — flag if N+ calls happen in a window
4. Merchant allowlist — only approved API providers
5. Category block — block entire spending categories
6. Combined rules — stack multiple rules for defense-in-depth
7. Edge cases — graceful degradation when fields are missing

First rule that matches decides. The decision comes back as JSON: `{"decision": "BLOCKED", "rule": "transaction_limit", "evaluation_ms": 0.09}`.

## The Eval Gym Proves It Works

The rules engine has a test suite of 50 labeled scenarios across 7 categories. All passing:

| Category | Scenarios | Pass Rate |
|----------|-----------|-----------|
| clean_approval | 10 | 100% |
| transaction_limit_block | 8 | 100% |
| daily_total_block | 7 | 100% |
| velocity_flag | 6 | 100% |
| merchant_allowlist_block | 7 | 100% |
| category_block | 7 | 100% |
| edge_cases | 5 | 100% |

The edge cases are where correctness matters: $500.00 at a $500 limit is APPROVED (not strictly greater). $500.01 is BLOCKED. Missing amount fields are FLAGGED, not crashed. Two rules at the same priority are deterministic — first in list wins.

## Try It

- **Risk calculator** (no signup): https://agentshield.fly.dev/tools/risk-calculator/
- **Plugin code**: https://github.com/kindrat86/agentshield/tree/main/integrations/openclaw
- **Eval gym**: https://agentshield.fly.dev/eval
- **Full architecture**: https://dev.to/maryan_k_bef6cf83fa64e809/i-built-a-firewall-for-ai-agent-spending-here-is-the-architecture-2560

The plugin is open source. The engine is pure Python 3.11 stdlib — zero pip dependencies, deployable on Fly.io free tier in 60 seconds. Managed hosting is available ($19/mo) if you do not want to self-host.

Pull requests welcome. Issues welcome. If you are running OpenClaw with multiple agents and have a budget horror story, I want to hear it.
