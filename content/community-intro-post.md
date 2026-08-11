# Community Intro Post Template

## For: CrewAI Discord, LangChain Discord, AutoGPT Discord, Indie Hackers

---

**Title:** I built a spend firewall for AI agents after losing $2,800 in 60 seconds

Hey everyone,

I've been building AI agents for about a year now, and last week I had a wake-up call that pushed me to build something I want to share.

At 3 AM, an agent I deployed entered a retry loop. It was calling a premium LLM endpoint at $133 per call. It retried 21 times before the budget alert email arrived. By the time I saw it at 6 AM, I'd lost $2,800.

The worst part? Every tool I had was working correctly:
- Rate limits were fine (they protect the provider, not me)
- Budget alerts triggered at the right threshold (I just wasn't awake to see the email)
- My dashboard showed exactly what happened (beautiful graphs, zero prevention)

So I built AgentShield — an open-source per-transaction spend firewall. Every API call is evaluated against configurable rules BEFORE it executes. Less than 1ms per evaluation. Pure Python stdlib. MIT licensed.

The two rules I'm most proud of came from community feedback:
1. **session_budget** — catches the "2 AM cron burst" where one session eats the whole daily budget. As spend accumulates, the per-call limit tightens.
2. **cascade_cost** — a $0.50 call with 30% failure rate and $5 retry = $2 expected cost. Blocks calls that look cheap but compound on failure.

I also wrote 56 labeled test scenarios for spend-control engines and open-sourced them as a universal benchmark. You can use them to test YOUR cost-control implementation, not just mine.

**Links:**
- GitHub (MIT): https://github.com/kindrat86/agentshield
- Live eval (56 scenarios): https://agentshield.fly.dev/eval
- Risk calculator (no signup): https://agentshield.fly.dev/tools/risk-calculator/

I'm not here to sell anything — the engine and eval gym are free and open source. I'm genuinely curious what cost-control patterns other people here are using, and whether the rule types I chose cover real-world use cases I haven't thought of.

Would love feedback from anyone deploying agents in production. What's your spend control story?

— Maryan K.
