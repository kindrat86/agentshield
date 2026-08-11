# Show HN Draft — Ready for Manual Submission

**Status:** HN karma for SipitenoMK is **1** (checked 2026-08-11 via Firebase API). Show HN posts from ~0-karma accounts are typically dead-on-arrival or auto-flagged. Submit manually when karma has grown, or submit anyway accepting the risk — the previous link post (item 49250917) got no traction, and a *text* Show HN generally performs better.

**Submit at:** https://news.ycombinator.com/submit (leave URL blank, put body in the text field)

---

**Title:**

Show HN: AgentShield – A firewall for AI agent spending (56 eval scenarios, Python stdlib)

**Text:**

I built a per-transaction spend firewall for AI agents after one of my agents spent $2,800 in 60 seconds while I was asleep.

The problem: AI agents make autonomous API calls with zero budget awareness. A single infinite loop, retry storm, or context accumulation bug can drain your API budget before you wake up. Observability tools (Helicone, LangSmith) show you what happened AFTER the bill arrives. Nothing stops the transaction BEFORE it executes.

AgentShield sits between your agent and the API. Every transaction is evaluated against 7 composable rule types in under 1ms. First rule that matches wins.

Rule types:

- Transaction limits (block any single call over $X)
- Daily totals (cap cumulative spend per agent per day)
- Velocity detection (flag if N+ calls happen in a time window)
- Merchant allowlists (only allow approved API providers)
- Category blocks (block entire spending categories)
- Session budgets (session-scoped spend cap with decay tightening)
- Cascade cost estimation (pre-dispatch EV: call_cost + fail_probability × reversal_cost)

I wrote 56 labeled test scenarios for spend-control engines and open-sourced them (MIT). Eval gym: https://agentshield.fly.dev/eval

Pure Python 3.11 standard library. Zero dependencies. Runs on 256MB RAM. Self-hostable in 60 seconds. Also on PyPI once the upload lands: pip install agentshield-spend

GitHub: https://github.com/kindrat86/agentshield
Live demo + risk calculator: https://agentshield.fly.dev

The last two rule types (session_budget and cascade_cost) were suggested by an engineer at HeartFlow who's building production cost-gating. Happy to discuss the architecture or take feature requests.
