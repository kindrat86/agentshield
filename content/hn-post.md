# Show HN: AgentShield, A firewall for AI agent spending (77/77 eval, stdlib only)

At 3 AM, an AI agent I built made 21 API calls in 60 seconds. $2,800 gone before I woke up.

Existing tools failed:
- API rate limits kicked in too late
- Budget alerts emailed me... while I was asleep
- Manual monitoring doesn't scale past 3 agents

So I built AgentShield: 10 composable rule types, evaluated per-transaction, in <1ms. No dependencies beyond Python 3 stdlib.

**Rule types:**
- transaction_limit, block single calls over a threshold
- daily_total, block when cumulative daily spend exceeds cap
- velocity, flag/block rapid-fire transaction bursts
- merchant_allowlist, only allow approved API providers
- category_block, block specific spending categories

Rules evaluate in priority order. First match wins. All monetary arithmetic uses Decimal (never float).

**The eval gym has 77 labeled scenarios. Currently at 77/77.**

Edge cases that prove correctness:
- Amount exactly at limit → APPROVED (not strictly greater)
- $0.01 over limit → BLOCKED
- Missing or malformed amount field → BLOCKED (fail-closed)
- Empty rules list → APPROVED

**Architecture:**
- Python 3.11 stdlib only (http.server, sqlite3, hmac, hashlib)
- SQLite in WAL mode with global write lock for multi-tenant isolation
- HMAC-SHA256 offline license validation (no server dependency)
- SSE for real-time blocked transaction alerts

**Try the risk calculator (no signup):** [URL]

**Source:** [GitHub URL]

I'd love feedback on:
1. The rule composition model, is first-match-wins the right semantics?
2. The eval gym approach, what scenarios would you add?
3. The offline licensing model, does HMAC validation make sense vs. server-side checks?
