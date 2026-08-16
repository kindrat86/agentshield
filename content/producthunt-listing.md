# AgentShield, Product Hunt Listing

## Tagline (40 chars)
A firewall for AI agent spending

## Description (260 chars)
Stop runaway AI agents before they burn your budget. 10 composable rules evaluated per-transaction in <1ms. Pure Python stdlib, zero dependencies. Deploy in 60 seconds. 74/74 eval gym included. Open source + managed hosting ($19/mo).

## Media
- Logo: (needs 240x240 product icon, use the shield concept)
- Screenshot 1: Risk calculator (https://agentshield.fly.dev/tools/risk-calculator/)
- Screenshot 2: Eval gym results (https://agentshield.fly.dev/eval)
- Screenshot 3: Dashboard rules configuration

## Maker Comment (first comment, MOST IMPORTANT)

I built AgentShield after an AI agent I deployed spent $2,800 in 60 seconds while I was asleep. The budget alert arrived at 6:14 AM. By then the agent had moved on to its next task, oblivious to the damage.

The problem: AI agents make API calls autonomously. One infinite loop, one batch job bug, one misconfigured cron, and your API bill explodes. Tools like LangSmith and Helicone track costs AFTER they happen. Nothing stops them BEFORE they execute.

AgentShield sits between your agent and the API. Each transaction is evaluated against 10 composable rules in under 1 millisecond. The first rule that matches decides: ALLOW or BLOCK.

The rules engine:
- Transaction limits, block any call over $X
- Daily totals, cap spending per agent per day
- Velocity detection, flag if an agent fires too many calls too fast
- Merchant allowlists, only allow approved API providers
- Category blocks, block entire spending categories

Built in pure Python 3.11 standard library. Zero pip dependencies. Runs on Fly.io free tier (256MB RAM, 39MB Docker image). Multi-tenant with SQLite WAL and PBKDF2 auth.

The whole thing is open source. There's managed hosting on Stripe if you want it, but you can self-host in 60 seconds.

Risk calculator (no signup): https://agentshield.fly.dev/tools/risk-calculator/
Architecture deep-dive: https://dev.to/maryan_k_bef6cf83fa64e809/i-built-a-firewall-for-ai-agent-spending-here-is-the-architecture-2560
Eval gym (74/74 across 12 categories): https://agentshield.fly.dev/eval

I'll be here all day, fire away with questions.

## Competitor Context (from PH research)
- Paybond: Safe spend controls for AI agents (broader, less developer-focused)
- Orite: Give AI agent money, not a blank check (payment-focused, not rules engine)
- Latitude: Open source agent monitoring (observability, not enforcement)

AgentShield's differentiation: per-transaction enforcement (not monitoring), pure stdlib (no deps), self-hostable in 60 seconds, 50-scenario eval gym proving correctness.

## Launch Timing
Best time: Tuesday-Thursday at 00:01 PST (09:01 EEST)
Maryan should submit when ready.
