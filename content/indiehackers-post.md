# Indie Hackers Post, AgentShield

## Title
I built a firewall for AI agent spending after an agent burned $2,800 in 60 seconds while I slept

## Body

At 3 AM, an AI agent I deployed made 21 API calls to a premium endpoint. Each call cost $133. That's $2,800 gone before I woke up.

The budget alert email arrived three hours after the damage was done. The agent had already moved on, oblivious to what it had cost.

So I built AgentShield. It's a per-transaction firewall that sits between your agent and the API. Every call is evaluated against 10 composable rules in under 1ms:

- Transaction limits (block any call over $500)
- Daily caps ($2,000 max per agent per day)
- Velocity detection (flag if an agent fires 10+ calls in an hour)
- Merchant allowlists (only approved providers)
- Category blocks (no crypto exchanges, no gambling APIs)

The whole thing is Python 3.11 standard library, zero pip dependencies. Multi-tenant, offline licensing, SQLite WAL storage. Runs on Fly.io's free tier (256MB RAM).

**Stats:**
- Evaluation: 74/74 scenarios passing across 12 categories
- Performance: 0.09ms average per transaction
- Image size: 39MB Docker container
- E2E tests: 14/14 including multi-tenant isolation

**Links:**
- Risk calculator (no signup): https://agentshield.fly.dev/tools/risk-calculator/
- Live eval gym: https://agentshield.fly.dev/eval
- Architecture: https://dev.to/maryan_k_bef6cf83fa64e809

**Question for the community:** What rules would you add? I'm thinking about time-based rules (no spending between 2-6 AM). What patterns have you seen in your own agent deployments?

## Tags
#python #devtools #ai #automation #opensource
