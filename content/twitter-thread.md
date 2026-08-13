# AgentShield Twitter Thread, The $2,800 Story

**Post 1/8:**
At 3 AM, an AI agent I built made 21 API calls to a premium LLM endpoint.

Each call cost $133.

That's $2,800 gone in 60 seconds while I was asleep.

The budget alert email arrived at 6:14 AM. Four hours too late.

So I built a firewall. 🧵

**Post 2/8:**
The problem: AI agents don't know they're spending money.

They make autonomous decisions about token consumption. Retry loops, context accumulation, tool call spirals, each one costs real dollars that the agent has zero awareness of.

**Post 3/8:**
Existing tools don't help:

❌ API rate limits protect the provider, not you
❌ Budget alerts arrive after the damage
❌ Cost dashboards show what happened, not what's about to happen
❌ Monitoring doesn't scale past 3 agents

All reactive. None preventive.

**Post 4/8:**
I built AgentShield, a per-transaction spend firewall.

Every API call is evaluated against rules YOU set before it executes:

• Transaction limits ($500 max per call)
• Daily caps ($2,000 max per day)
• Velocity detection (max 10 calls/hour)
• Merchant allowlists (only approved APIs)

**Post 5/8:**
The evaluation takes <1ms. Pure Python stdlib. Zero dependencies.

If a call violates a rule, it's BLOCKED before it reaches the API provider. The agent gets a structured error. Your wallet stays closed.

**Post 6/8:**
Two rules that came from production experience:

1️⃣ session_budget, Daily caps miss the "2 AM cron burst" where one session eats the whole day. Session-scoped budgets with decay tightening catch it.

2️⃣ cascade_cost, A $0.50 call with 30% failure rate and $5 retry = $2.00 expected cost. The rule blocks calls that look cheap but compound on failure.

**Post 7/8:**
56 labeled test scenarios. 7 composable rule types. MIT licensed.

The eval gym is a universal benchmark, use it to test YOUR spend-control implementation, not just ours.

Live eval: https://agentshield.fly.dev/eval

**Post 8/8:**
AgentShield is live now:
📦 pip install agentshield
🌐 https://agentshield.fly.dev
🔧 https://github.com/kindrat86/agentshield

Free to self-host. $19/mo managed. $299 professional audit (money-back guarantee if we don't find $299 in waste).

Built because budget alerts shouldn't arrive by email.
