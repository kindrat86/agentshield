# AgentShield — Firewall for AI Agent Spending

Stop runaway AI agents before they burn your budget. 7 composable rules evaluated per-transaction in under 1 millisecond. Pure Python 3.11 stdlib — zero dependencies.

[![Health](https://img.shields.io/badge/health-ok-brightgreen)](https://agentshield.fly.dev/health)
[![Eval](https://img.shields.io/badge/eval-50%2F50-brightgreen)](https://agentshield.fly.dev/eval)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## The $2,800 Wake-Up Call

At 3 AM, an AI agent made 21 API calls to a premium endpoint. Each cost $133. $2,800 gone in 60 seconds — while the developer slept.

AgentShield sits between your agent and the API. Every transaction is evaluated against 7 composable rules BEFORE it executes. First rule that matches wins. All in under 1ms.

## Quick Start

```bash
curl -s https://agentshield.fly.dev/health
# {"status": "ok", "version": "1.0.0"}
```

See your risk profile in 30 seconds — no signup required: [Risk Calculator](https://agentshield.fly.dev/tools/risk-calculator/)

## Eval Gym

50 labeled scenarios across 7 categories. All passing → [https://agentshield.fly.dev/eval](https://agentshield.fly.dev/eval)

| Category | Scenarios | Pass Rate |
|----------|-----------|-----------|
| clean_approval | 10 | 100% |
| transaction_limit_block | 8 | 100% |
| daily_total_block | 7 | 100% |
| velocity_flag | 6 | 100% |
| merchant_allowlist_block | 7 | 100% |
| category_block | 7 | 100% |
| edge_cases | 5 | 100% |

## Rules Engine

7 composable rules, evaluated in priority order:

| Rule | What it does |
|------|-------------|
| **Transaction Limit** | Block any single call over $X |
| **Daily Total** | Cap cumulative spend per agent per day |
| **Velocity** | Flag if N+ calls happen in a time window |
| **Merchant Allowlist** | Only allow approved API providers |
| **Category Block** | Block entire spending categories |
| **Combined Rules** | Layer rules for defense-in-depth |
| **Edge Cases** | Graceful degradation for missing fields |

## Architecture Deep-Dive

[Read on Dev.to →](https://dev.to/maryan_k_bef6cf83fa64e809/i-built-a-firewall-for-ai-agent-spending-here-is-the-architecture-2560)

## Tech Stack

- **Language:** Python 3.11 (stdlib only — zero pip installs)
- **Storage:** SQLite WAL (multi-tenant isolation)
- **Auth:** PBKDF2-HMAC-SHA256 (200K iterations)
- **Licensing:** HMAC-SHA256 offline signed keys
- **Deployment:** Fly.io, 256MB RAM, 39MB Docker image
- **API:** 18 routes, CORS, SSE

## Pricing

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 1 agent, 100 evals/day |
| **Dev** | $19/mo | 5 agents, 10 custom rules, 1K evals/day |
| **Team** | $99/mo | 20 agents, 50 custom rules, SSE alerts |
| **Managed** | $499/mo | 100 agents, 200 custom rules, dedicated support |

## Quick Deploy

```bash
git clone https://github.com/kindrat86/agentshield.git
cd agentshield
python3.11 -m http.server 8080 --directory public
# Or: fly deploy
```

## Community

- [Dev.to Article](https://dev.to/maryan_k_bef6cf83fa64e809)
- [GitHub Issues](https://github.com/kindrat86/agentshield/issues)
- [Risk Calculator](https://agentshield.fly.dev/tools/risk-calculator/)

Built because budget alerts shouldn't arrive by email.
