# Soap Opera Nurture Email Sequence, AgentShield

## Day 1: The Hook (Open Loop)
**Subject:** I lost $2,800 while I was sleeping

At 3:14 AM, my phone buzzed. An email from my API provider.

$2,793.00. In one hour. While I was asleep.

An AI agent I'd deployed had entered a retry loop. Each retry cost $133. It retried 21 times before the budget alert even arrived.

The alert came at 3:14 AM. I read it at 6:17 AM. Three hours too late.

Every tool I had was reactive. Rate limits protect the provider. Budget alerts arrive by email. Dashboards show you what happened, after the money is gone.

Tomorrow I'll show you what I built to stop this from ever happening again.

- Maryan K.
AgentShield

---

## Day 2: The Solution (Tension + Relief)
**Subject:** What if your agent asked permission before spending?

Yesterday I told you about losing $2,800 in 60 seconds.

Here's what I built: a per-transaction firewall that sits between your agent and the API. Every call is evaluated against rules you set, BEFORE it executes.

- Transaction over $500? Blocked.
- Daily spend over $2,000? Blocked.
- More than 10 calls in an hour? Flagged.

The evaluation takes less than 1ms. Pure Python stdlib. Zero dependencies.

If I'd had this running that night, the second call would have been blocked at $266. Not $2,793.

But here's the thing, the basic rules aren't enough. Tomorrow I'll show you the two rules that came from production feedback at HeartFlow.

- Maryan K.
AgentShield · https://agentshield.fly.dev

---

## Day 3: The Deepening (Expert Authority)
**Subject:** The rule that catches what daily budgets miss

Yesterday's email got a lot of replies. Most people asked the same question:

"What about agents that run for hours? A daily cap doesn't help if one session eats the whole budget at 2 AM."

Exactly. That's why I built session_budget, a rule that tracks spend per session, not just per day. It uses decay tightening: as the session accumulates spend, the per-call limit shrinks. The more an agent spends, the tighter the leash.

And there's one more rule that most people never think about: cascade_cost.

A $0.50 API call with a 30% failure rate and a $5 retry cost has an expected value of $2.00. The cascade_cost rule blocks calls that look cheap but compound on failure.

These two rules came directly from an engineer at HeartFlow who's building production cost-gating. Real-world rules from real-world pain.

Tomorrow: the 74-scenario eval gym that tests all of this.

- Maryan K.
AgentShield

---

## Day 4: The Proof (Social Validation)
**Subject:** 74 test scenarios that prove your spend control works

You can't claim "spend control" without test cases. So I wrote 74 of them.

The Eval Gym covers:
- Clean approvals (transactions that should pass)
- Transaction limits, daily totals, velocity detection
- Merchant allowlists, category blocks
- Session budgets with decay
- Cascade cost estimation
- Edge cases (precision, timing, concurrent transactions)

All MIT licensed. You can steal them and use them to test YOUR spend-control implementation.

A team called ZeroClaw actually implemented pre-flight budget enforcement after seeing this work. They merged a PR. That's the strongest validation possible.

Live eval gym: https://agentshield.fly.dev/eval
Spec page: https://agentshield.fly.dev/eval-gym-spec

Tomorrow: how to get started in 60 seconds.

- Maryan K.
AgentShield

---

## Day 5: The Close (Action + Urgency)
**Subject:** Your agents are running right now. Do they have a firewall?

This is the last email in the series. Let me make it simple.

**Free options:**
- pip install agentshield (self-host, MIT)
- Risk calculator: https://agentshield.fly.dev/tools/risk-calculator/ (30 seconds, no signup)
- Eval gym: https://agentshield.fly.dev/eval (74 scenarios)

**Paid options:**
- $299 Professional Spend Audit (I analyze your API bills and find waste, money-back guarantee if I don't find $299)
- $19/mo Managed AgentShield (14-day free trial)

The question isn't whether you need spend control. It's whether you set it up before or after your first incident.

I wish I'd done it before.

- Maryan K.
AgentShield · https://agentshield.fly.dev

P.S. The free audit has 1 spot remaining: https://agentshield.fly.dev/free-audit
