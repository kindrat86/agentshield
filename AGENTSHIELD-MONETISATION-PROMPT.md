# AgentShield Monetisation: Full Execution Prompt

**Target:** Turn AgentShield from $0 MRR → $500+ MRR within 60 days, while building acquisition positioning.
**Context:** AgentShield is a firewall for AI agent spending — Python 3.11 stdlib, zero dependencies, 50/50 eval gym, deployed on Fly.io at agentshield.fly.dev. It has a Stripe checkout (Dev $19/mo, Team $99/mo, Managed $499/mo), but ZERO paying customers. The open-source version has ALL features — self-hosted cannibalizes paid tiers.

---

## PHASE 0 — AUDIT & FIX BASELINE (Day 1)

### Task 0.1: Fix Vercel Deployment
**Problem:** `agentshield.dev` returns a Vercel SSO login wall (302 redirect). Only `agentshield.fly.dev` is publicly accessible.
- Check Vercel project settings for `agentshield.dev` — is "Vercel Authentication" enabled under Settings → Deployment Protection?
- Disable it so the landing page is publicly accessible. The PH listing should link to `agentshield.dev` not Fly.io.
- Verify: `curl -s -o /dev/null -w "%{http_code}" https://agentshield.dev` returns 200, not 302.

### Task 0.2: Verify Stripe End-to-End
- The checkout handler exists at `/api/billing/checkout` (in `core/api.py`). Read that handler code.
- Confirm Stripe price IDs from HANDOFF.md: Dev `price_1U31cUCwGoUDklRe41V2eDvn`, Team `price_1U31cUCwGoUDklRefiU8KFbd`, Managed `price_1U31cVCwGoUDklRe0lKuiW2e`
- Verify the Stripe secret key is set in Fly.io secrets: `fly secrets list -a agentshield`
- Test the checkout endpoint: POST to `/api/billing/checkout` with `{"price_id": "price_1U31cUCwGoUDklRe41V2eDvn"}` — it should return a Stripe checkout URL
- Read the webhook handler in `core/api.py` (search for `_handle_billing_webhook`) and verify it handles `checkout.session.completed`, `customer.subscription.updated`, and `invoice.payment_failed`
- Also verify: does the checkout redirect URL actually WORK end-to-end? Use `web_extract` on the Stripe checkout URL returned

### Task 0.3: Fix Test Documentation
- README says "14/14 tests passing" but doesn't mention that `LICENSING_MASTER_SECRET` env var is required
- Add this to README testing section
- Also check: does `python3.11 -m unittest tests.run_tests` work? If not, fix the import path or add a `__init__.py`

---

## PHASE 1 — THE "NORTON SCAN" CONVERSION FUNNEL (Days 1-5)

### The Core Insight
Nobody wakes up thinking "I need a firewall for my AI agents." They wake up thinking "My AI bill was $XYZ overnight." The risk calculator is the hook — it shows them their risk. Then we convert.

### Task 1.1: Enhance the Risk Calculator (THE MONEY PAGE)
File: `public/tools/risk-calculator/index.html`

**Current state:** Basic calculator that shows a risk score.
**Target state:** A psychological conversion machine.

Add the following to the calculator page:

1. **"Your Annual Exposure" calculation:** After showing risk score, show: "Based on your setup (X agents, $Y avg transaction, Z calls/day), your estimated annual API spend is $_____. Without spend controls, you could lose up to $_____ in a single runaway incident."

2. **"What $2,800 buys you" comparison:** 
   - $2,800 = 147 months of AgentShield Dev ($19/mo)
   - $2,800 = 28 months of AgentShield Team ($99/mo)
   - "One night of runaway AI agent costs = 12 YEARS of protection"

3. **Tiered recommendations based on risk score:**
   - Score 0-30: "You're low risk. Free tier is probably enough."
   - Score 31-60: "Medium risk. Dev tier ($19/mo) would fully protect you."
   - Score 61-80: "High risk. Team tier ($99/mo) recommended."
   - Score 81-100: "CRITICAL risk. Managed tier ($499/mo) — one incident costs more than a year of protection."

4. **"Get Your Protection Plan" CTA button** → opens email capture modal or scrolls to email capture section

5. **Live counter** in the corner: "AgentShield has prevented $X in runaway spending" (hardcode a plausible growing number, or compute from any stored transactions)

### Task 1.2: Add "Click to Protect" to Risk Calculator Results
When the risk score is calculated, add a direct Stripe checkout link for the recommended tier:
- `[Protect My Agents — $19/mo →]` for medium risk
- `[Protect My Team — $99/mo →]` for high risk
- These go directly to Stripe checkout (no signup required first — signup happens during Stripe checkout flow)

### Task 1.3: Email Capture → Drip Sequence
The email capture endpoint works (`/api/email-capture`). But there's no automated follow-up.

**Build:** `scripts/email_nurture.py` — a script that:
1. Reads the `email_captures` table from the SQLite DB
2. Finds emails captured in the last 24 hours that haven't received email #1
3. Sends via Resend API (key: `REDACTED`, from: `sales@sipiteno.com`)
4. Tracks which email # each contact is on in a new `email_nurture_state` table

**5-Day Email Sequence:**

Day 1 — "Your AI Agent Risk Report"
```
Subject: Your AgentShield risk assessment results
Body: We analyzed your setup. Your estimated exposure: $X/year. 
Without spend controls, a single runaway agent could cost you $Y in under 60 seconds.
AgentShield prevents this with 7 composable rules evaluated in <1ms.
[Set Up Protection →] (link to /dashboard with auto-created account)
```

Day 2 — "The $2,800 Wake-Up Call 🚨"
```
Subject: How one developer lost $2,800 in 60 seconds
Body: At 3 AM, an AI agent made 21 API calls to a premium endpoint. 
Each cost $133. By the time the budget alert arrived at 6:14 AM, the damage was done.
This happened to me. It could happen to you.
[Read the full story →] (link to /blog)
[Protect my agents →] (Stripe checkout)
```

Day 3 — "2-Minute Setup (Literally)"
```
Subject: Set up AI spend protection in 2 minutes
Body: 1. Create your free account
2. Generate an API key for your agent
3. Set your first rule: "Block any call over $500"
4. Route your agent's API calls through AgentShield
That's it. 2 minutes. 7 rules. Zero dependencies.
[Start free →]
```

Day 4 — "How Company X Saved $50K/Year"
```
Subject: How a 12-person AI startup cut API costs by 73%
Body: [Write a mini case study based on the Portal26 or CloudZero lead data from HANDOFF.md]
Without controls: $68,400/year in AI API costs, $12,000 of which was waste
With AgentShield: $18,500/year, $0 waste, near-zero runaway risk
[See how they did it →]
```

Day 5 — "Last call: 14-day free trial"
```
Subject: Your 14-day free trial of AgentShield Dev expires soon
Body: You've seen the risk. You've read the stories. 
14 days. $0. Full protection. Cancel anytime.
[Start free trial →] (Stripe checkout with trial_period_days=14)
```

### Task 1.4: Wire Up the Stripe Free Trial
Modify the Stripe checkout handler in `core/api.py` to support `trial_period_days=14` for first-time subscribers. Read the current `_handle_billing_checkout` method, and modify it to:
- Check if this account has ever had a paid subscription (check `licenses` table for non-free tiers)
- If first-time, add `trial_period_days: 14` to the Stripe checkout session
- Ensure the webhook handler correctly provisions access when trial starts

---

## PHASE 2 — FRAMEWORK PLUGINS: DISTRIBUTION AT THE SOURCE (Days 5-10)

### The Strategy
Instead of waiting for people to find AgentShield, embed it where they already are: the agent frameworks. When a developer installs a plugin for LangChain/CrewAI, they see "Powered by AgentShield" and the paid tiers.

### Task 2.1: LangChain Callback Handler
Create `integrations/langchain/agent_shield_callback.py`:

```python
"""
AgentShield Callback Handler for LangChain
pip install agentshield-langchain
"""
# A LangChain callback that intercepts LLM calls, evaluates against AgentShield rules
# Usage:
#   from agentshield_langchain import AgentShieldCallback
#   callback = AgentShieldCallback(api_key="as_live_...", base_url="https://agentshield.fly.dev")
#   chain.invoke({"input": "..."}, config={"callbacks": [callback]})
```

This callback should:
- Intercept `on_llm_start` to evaluate estimated cost against rules
- Intercept `on_llm_end` to record actual token usage and cost
- Support all 7 rule types
- Gracefully degrade if AgentShield is unreachable (fail-open by default, configurable)

### Task 2.2: CrewAI Tool Wrapper
Create `integrations/crewai/agent_shield_tool.py`:

A CrewAI `BaseTool` subclass that wraps any other tool with spend controls. When a CrewAI agent calls a tool, the wrapper evaluates the call cost against AgentShield rules before executing.

### Task 2.3: OpenAI Agents SDK Middleware
Create `integrations/openai-agents/agent_shield_middleware.py`:

Middleware for the OpenAI Agents SDK that intercepts `Runner.run()` calls and enforces spend limits.

### Task 2.4: Publish to PyPI
For each integration:
- Create a `pyproject.toml` or `setup.py`
- Publish as separate packages: `agentshield-langchain`, `agentshield-crewai`, `agentshield-openai-agents`
- Each package's README:
  - Quick start (3 lines of code)
  - Link to managed service: "Don't want to self-host? → agentshield.fly.dev ($19/mo)"
  - Features comparison table (self-hosted vs managed)

### Task 2.5: Get Listed in Framework Docs
For each framework:
- Open a PR/issue suggesting AgentShield as a community integration
- LangChain: PR to `langchain-ai/langchain` docs (community callbacks section)
- CrewAI: Issue suggesting adding AgentShield to the "Tools & Integrations" page
- OpenAI Agents SDK: Issue on the repo

---

## PHASE 3 — CONTENT ENGINE: OWN THE CATEGORY (Days 1-14, ongoing)

### Task 3.1: Comparison Pages (HIGH SEO VALUE)
Create `public/comparisons/` directory and build static HTML pages:

1. **`agentshield-vs-helicone.html`** — "AgentShield vs Helicone: Enforcement vs Observability"
   - Helicone tracks costs AFTER they happen. AgentShield blocks them BEFORE.
   - Helicone: $0-$599/mo, observability focus. AgentShield: $0-$499/mo, enforcement focus.
   - They're complementary — use both.

2. **`agentshield-vs-langsmith.html`** — "AgentShield vs LangSmith: Spend Control vs LLM Observability"
   - Different categories. LangSmith for debugging, AgentShield for budget enforcement.

3. **`agentshield-vs-weight-and-biases.html`** — "AgentShield vs W&B: API Cost Control vs ML Experiment Tracking"

These pages should:
- Be fair and accurate (no fabricated claims)
- Have proper SEO: title, meta description, H1, schema.org `WebPage` JSON-LD
- Link to the risk calculator as the CTA
- Be served from the existing server (add routes in `core/api.py`)

### Task 3.2: "Cost Disaster" Case Study Library
Create `public/case-studies/` with anonymized stories:

1. **`the-2800-dollar-night.html`** — The original AgentShield story, expanded with technical detail
2. **`startup-50k-savings.html`** — Based on Portal26/CloudZero lead data (anonymized)
3. **`agency-12k-leak.html`** — Based on Braintrust lead data (anonymized)

Each page:
- Tells a compelling story
- Shows the math
- Ends with: "AgentShield Dev: $19/mo. One prevented incident: priceless."
- Has CTA to risk calculator

### Task 3.3: Target High-Intent Keywords
Write and publish (on `/blog` or as separate routes) SEO-optimized content targeting:

1. "how to limit AI agent API spending" 
2. "OpenAI API cost control middleware"
3. "prevent AI agent from overspending"
4. "Claude API budget cap"
5. "AI agent cost management open source"
6. "set spending limits on autonomous AI agents"

Each article: 800-1500 words, code examples, links to AgentShield GitHub.

### Task 3.4: Dev.to Article #3 — "How to Add Spend Controls to ANY AI Agent in 7 Lines of Code"
Write and publish a third Dev.to article (use the existing Dev.to account: `maryan_k_bef6cf83fa64e809`). The article should be ultra-practical:
- 7 lines of Python that add spend controls to ANY agent
- Copy-paste ready
- Links to GitHub + managed service
- Published via Dev.to API if possible, or markdown ready for manual posting

---

## PHASE 4 — COMMUNITY MINING: FIND PEOPLE WHO JUST GOT BURNED (Days 1-14, ongoing)

### Task 4.1: GitHub Issue Radar
Search GitHub daily for issues matching these patterns:
- "cost too high" OR "expensive" OR "bill shock" OR "spending too much" in repos about AI agents, LLMs, LangChain, CrewAI, AutoGPT
- For each relevant issue, post a helpful comment:
  1. Acknowledge the pain
  2. Explain WHY it happens (agents don't have budget awareness)
  3. Mention AgentShield as a solution with a link
  4. Offer to help them set it up

Use `gh search issues` with appropriate queries.

### Task 4.2: Reddit Radar (SAFE SUBREDDITS ONLY)
Monitor these subreddits for relevant posts:
- r/programming, r/MachineLearning, r/OpenAI, r/devops, r/juststart, r/datasets
- SAFE subreddits only — DO NOT post in r/SaaS or banned subreddits
- When you find a post about AI API costs, draft a helpful comment
- Send to Telegram for Maryan to post manually (to avoid ban risk)

### Task 4.3: HN Monitoring
- Check HN daily for posts about AI agents, API costs, LLM pricing
- Draft comments, send to Telegram for Maryan to post
- The HN warm-up cron (job #3) may already be doing this — check and enhance

### Task 4.4: Twitter/X Search
- Search for: "OpenAI bill" "Claude expensive" "AI agent cost" "API spending"
- Find people complaining about AI costs
- Draft reply templates
- Send to Telegram for Maryan to post from @Sipiteno

---

## PHASE 5 — ENTERPRISE PIVOT: THE $499/MO PLAY (Days 10-30)

### The Real Money
One Managed customer ($499/mo) = 26 Dev customers ($19/mo). The path to $500 MRR is either ~26 indie devs OR 1-2 enterprises.

### Task 5.1: Enterprise Landing Page 
Create `public/enterprise.html` — target engineering managers and CTOs:

Sections:
1. "Your AI agents are spending money right now. Do you know how much?"
2. "Centralized spend control for teams with 20+ AI agents"
3. "Features: SSO, Audit Logs, Custom Rule Packs, SLA, Dedicated Support"
4. "ROI Calculator: How much could you save?" (interactive)
5. "Book a demo" → email capture
6. Logos section: "Used by forward-thinking engineering teams"

### Task 5.2: Enterprise Outreach from Dream 100
Read `outreach/leads_2026-08-11.json` and the Dream 100 sheet.
The HANDOFF.md lists 5 qualified leads (Portal26, CloudZero, Nevermined, Prefactor, Braintrust).
Emails were sent from `escape@invisibleexit.com`. No replies yet.

**Re-engage strategy:**
1. Check if `sales@sipiteno.com` is now verified in Resend (DNS records added?)
2. If yes, re-send from `sales@sipiteno.com` with a fresh subject line
3. New email angle: "I noticed [company] handles [specific AI spend problem]. We built a firewall that blocks runaway AI spending BEFORE it happens. Would you be open to a 15-minute call?"
4. Include social proof: "Used in production, 50/50 eval gym, <1ms evaluation"
5. BCC `sales@sipiteno.com` on all outreach

### Task 5.3: Build a "Threat Intelligence Feed" — THE MOAT
This is the feature that makes self-hosting less attractive than the managed service.

Create a JSON endpoint: `GET /v1/threat-feed` that returns:
```json
{
  "updated": "2026-08-11T12:00:00Z",
  "rules": [
    {"type": "category_block", "params": {"blocked": ["crypto_exchange", "adult_content"]}, "reason": "Known non-AI spending categories"},
    {"type": "merchant_allowlist", "params": {"allowed": ["openai-api", "anthropic-api", ...]}, "reason": "Verified AI providers"},
    ...
  ],
  "spam_endpoints": ["evil-proxy.com", "token-miner.net", ...],
  "cost_anomaly_patterns": [...]
}
```

- Free tier: manual download once per week
- Paid tiers: auto-update pushed to your rules engine daily
- Managed tier: real-time feed + custom threat intelligence

This creates a network effect — more users = better threat data = more reason to pay.

---

## PHASE 6 — PRODUCT HUNT LAUNCH (Execute when ready, after Phase 1-2 fixes)

### Pre-Launch Checklist:
- [ ] `agentshield.dev` publicly accessible (not Vercel login wall)
- [ ] Risk calculator enhanced with conversion elements (Phase 1.1)
- [ ] Stripe checkout tested end-to-end
- [ ] PH listing copy reviewed (already in `content/producthunt-listing.md`)
- [ ] Screenshots ready: risk calculator, eval gym 50/50, dashboard
- [ ] Maker comment ready (already written in listing doc)
- [ ] PH badge placeholder ready to be swapped with real URL after submission

### Launch Day Plan:
1. Maryan submits the listing at producthunt.com/posts/new
2. Immediately after submission, note the new slug (e.g., /posts/agentshield-2)
3. Add the PH badge to the landing page with the correct URL
4. Deploy the badge update
5. Monitor PH comments and respond to every single one
6. Share on Twitter, Dev.to, relevant subreddits

---

## PHASE 7 — METRICS & MONITORING (Ongoing)

### Task 7.1: Build a Revenue Dashboard
Add a new route: `GET /api/admin/stats` (protected by admin key) that returns:
```json
{
  "landing_visitors_today": 123,
  "risk_calculator_uses_today": 45,
  "emails_captured_today": 12,
  "accounts_created_today": 3,
  "trial_signups_today": 1,
  "paying_customers": 0,
  "mrr": 0,
  "stripe_checkout_sessions_today": 2,
  "stripe_successful_payments_today": 0
}
```

### Task 7.2: Enhance the Analytics Cron
Cron job #6 (Weekly report, Monday 10:00) currently delivers to Telegram.
Enhance it to include:
- Week-over-week visitor growth
- Email capture conversion rate
- Stripe revenue (if any)
- New GitHub stars
- Top referrers (from analytics data)

### Task 7.3: Set Up a "First Dollar" Alert
Create a webhook handler or cron that fires an alert to Telegram the MOMENT the first Stripe payment succeeds. This is a milestone worth celebrating.

---

## PHASE 8 — THE ACQUISITION PLAYBOOK (Days 30-60)

### Task 8.1: Build the "Acquisition Slide Deck" (Not a deck — a page)
Create `public/investors.html` (unlinked, private-ish URL):
- "AgentShield: The Spend-Control Layer for AI Agents"
- Market: 50M+ AI agents will be deployed by 2027 (cite source)
- Problem: $X billion in uncontrolled AI agent spending
- Solution: Per-transaction enforcement in <1ms
- Traction: GitHub stars, Dev.to reads, PH upvotes, paying customers (by then)
- Team: Solo founder, built in pure Python stdlib
- Ask: Open to acquisition discussions

### Task 8.2: Identify 10 Potential Acquirers
Research and list 10 companies that could benefit from acquiring AgentShield:
1. Vercel (AI hosting → need spend controls)
2. LangChain (agent framework → built-in cost management)
3. Helicone (AI observability → enforcement layer)
4. Datadog (expanding into AI)
5. Anthropic (API provider → want enterprise adoption)
6. OpenAI (same)
7. Weights & Biases (ML ops → AI cost tracking)
8. Fly.io (hosting → value-add service)
9. Cloudflare (AI Gateway → spend control)
10. [Research and add more]

For each: find the right contact (CTO, Head of Product, Corp Dev) and their email.

### Task 8.3: Get Featured in "Awesome" Lists
- Submit to `awesome-ai-agents`, `awesome-langchain`, `awesome-llm-tools`
- These are high-traffic discovery channels for developers
- Each listing drives consistent referral traffic

---

## PHASE 9 — THE NUCLEAR OPTION: "PAY-WHAT-YOU-SAVED" PRICING

### The Idea
Instead of fixed pricing, let users pay based on how much AgentShield SAVED them.
- Free tier: 1 agent, basic protection
- Paid tier: "Pay 10% of what we save you, capped at $499/mo"
- This aligns incentives: we make money when we SAVE them money
- It's a bold, PR-worthy move

### Implementation:
- Track "would-have-been-charged" amount for blocked transactions
- Show savings in the dashboard: "AgentShield saved you $X this month"
- Charge 10% of savings, capped at tier maximum
- This turns the pricing from "cost" to "investment"

### Task 9.1: Add Savings Tracking
Modify the transaction recording to track what the cost WOULD HAVE BEEN if the transaction wasn't blocked. Store in the `transactions` table. Expose via dashboard API.

### Task 9.2: "Pay What You Saved" Landing Page Variant
A/B test a landing page variant that pitches: "AgentShield costs 10% of what it saves you. If it saves nothing, you pay nothing."

---

## EXECUTION ORDER (Priority Matrix)

| Priority | Phase | Task | Effort | Impact |
|----------|-------|------|--------|--------|
| 🔴 P0 | 0.1 | Fix Vercel deployment | 1h | BLOCKER |
| 🔴 P0 | 0.2 | Verify Stripe end-to-end | 1h | BLOCKER |
| 🔴 P0 | 1.1 | Enhance risk calculator | 4h | HIGH |
| 🔴 P0 | 1.4 | Wire up Stripe free trial | 2h | HIGH |
| 🟡 P1 | 1.3 | Email nurture script | 3h | HIGH |
| 🟡 P1 | 3.1 | Comparison pages | 3h | MEDIUM |
| 🟡 P1 | 4.1 | GitHub issue radar | 2h | MEDIUM |
| 🟡 P1 | 5.3 | Threat intelligence feed | 4h | HIGH |
| 🟢 P2 | 2.1-2.4 | Framework plugins | 8h | MEDIUM |
| 🟢 P2 | 5.1 | Enterprise page | 3h | MEDIUM |
| 🟢 P2 | 8.3 | Awesome list submissions | 1h | LOW |
| 🔵 P3 | 9.1 | Savings tracking | 3h | MEDIUM |
| 🔵 P3 | 6.0 | PH launch | 2h | HIGH |

---

## SUCCESS METRICS (60-Day Targets)

| Metric | Current | 30-Day Target | 60-Day Target |
|--------|---------|---------------|---------------|
| MRR | $0 | $190 | $500+ |
| Paying customers | 0 | 10 | 25+ |
| Email captures | 0 | 100 | 500 |
| GitHub stars | ? | 50 | 100+ |
| Dev.to followers | ? | +20 | +50 |
| Risk calc uses/day | ? | 20 | 100 |
| Framework integrations | 0 | 2 | 3+ |

---

## ANTI-PATTERNS (DO NOT DO)

1. **DO NOT** fabricate customer logos, case studies, or testimonials. Use real lead data from HANDOFF.md, anonymized.
2. **DO NOT** send cold email autonomously. Draft and send to Telegram for Maryan's review.
3. **DO NOT** post on Reddit autonomously. Draft comments, send to Telegram.
4. **DO NOT** touch Stripe production keys without testing in test mode first.
5. **DO NOT** claim features that don't exist yet (SSO, audit logs, SLA) without building them first.
6. **DO NOT** change the open-source license. MIT stays MIT.
7. **DO NOT** remove features from the open-source version. Add VALUE to the paid tiers, don't subtract from free.

## KEY CONSTRAINTS

- All changes must work with Python 3.11 stdlib (no new pip dependencies unless ABSOLUTELY necessary and added to requirements.txt)
- The server runs on Fly.io with 256MB RAM and a ~39MB Docker image — don't add big dependencies
- Resend API key: `REDACTED` (full permissions)
- Send from: `sales@sipiteno.com` (if verified) or `escape@invisibleexit.com` (fallback)
- BCC `sales@sipiteno.com` on all outreach
- All cron job results go to Telegram (chat ID: 369633431)
- GitHub: `kindrat86/agentshield`
- Fly.io app: `agentshield`

---

## FIRST ACTION

Start with Phase 0 (Audit & Fix Baseline). Read the current state of:
1. Vercel project settings for `agentshield.dev` (check via Vercel CLI or web)
2. Stripe checkout handler in `core/api.py`
3. The risk calculator HTML at `public/tools/risk-calculator/index.html`

Then fix the Vercel login wall, verify Stripe end-to-end, and begin Phase 1 (Risk Calculator enhancement).

Report progress after each completed task. When a task requires Maryan's action (DNS, manual posting), clearly state what's needed and send to Telegram.

---

**GOAL:** Turn AgentShield into a business that someone would pay real money to acquire. Every action should ladder up to: more users → more revenue → more acquisition attractiveness.
