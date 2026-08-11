# MISSION: Convert Technical Conversations Into Trial Signups

## ⚠️ YOUR ONLY KPI: Get ONE person to try AgentShield

Not more comments. Not more features. Not more conversations. **One person clicking the risk calculator or signing up for a trial.** Everything in this session serves that single outcome.

---

## THE STATE OF PLAY

### What's Real (verified)
- **Product:** https://agentshield.fly.dev — 56/56 eval gym, 9 rule types, 14/14 tests, health OK
- **Stripe:** Dev $19/mo, Team $99/mo, Managed $499/mo — checkout wired and tested
- **Email capture:** POST `/api/email-capture` → 5-day nurture sequence via Resend
- **Risk calculator:** `https://agentshield.fly.dev/tools/risk-calculator/` — no signup required
- **21 GitHub outreach posts** across 14 repos
- **5 active conversations** — real technical exchanges, not one-off comments

### The 5 Active Conversations

| # | Thread | Who | Status | Conversion Status |
|---|--------|-----|--------|-------------------|
| 1 | **OpenClaw #42475** | @yun520-1 (HeartFlow) | 2 exchanges deep — they suggested features, we built them | **HOTTEST — hasn't tried the product yet** |
| 2 | **ZeroClaw #2269** | @theonlyhennygod | They merged a pre-flight enforcement PR after our post | **STRONGEST validation — hasn't tried OUR product** |
| 3 | **LangChain #31647** | @sailikhithk | PR in progress, we suggested enforcement complement | **Active developer — direct adjacent need** |
| 4 | **RocketRide #1693** | @Zayed024 | Assigned, shared architecture | **Design phase — early enough to influence** |
| 5 | **Elitea #6010** | @epamLDadayan | Verified on stage, UX suggestions made | **Implementation phase — evaluating options** |

### The Gap
All 5 conversations are **technical** — people discussing architecture, code, and approaches. None have been asked: "Would you actually use this?"

---

## RULE ZERO: YOU CANNOT FABRICATE

Every claim backed by visible tool output. Comment posted → show URL. Trial signup happened → show the account. Never invent IDs, statuses, or replies. Never touch memory. Never mention cron.

---

## PHASE 1: CONVERT THE HOTTEST LEAD — @yun520-1 (20 min)

This person:
- Works at HeartFlow (production cost-gating system)
- Suggested two features you actually built (session_budget, cascade_cost)
- Had 2 technical exchanges with you
- Has NOT been asked to try AgentShield

### 1A. Read the full thread
```bash
gh issue view https://github.com/openclaw/openclaw/issues/42475 --comments 2>&1 | tail -100
```

Read EVERY comment carefully. Understand the full arc of the conversation.

### 1B. Craft the ask

This is the most important comment you'll write. It must:

1. **Acknowledge the relationship built so far:** "You've already shaped two of our rule types — session_budget and cascade_cost came directly from our last exchange."

2. **Make a specific, narrow ask — NOT "try our product":**
   - "Would you be willing to run our risk calculator with HeartFlow's numbers? No signup. Takes 30 seconds. I'd value your read on whether the risk score aligns with what you see in production."
   - Link: https://agentshield.fly.dev/tools/risk-calculator/

3. **Offer something in return:** "If the risk model seems useful, I can share the raw eval scenarios we use so you can adapt them for HeartFlow's cost-gating tests."

4. **No pressure:** "No pitch, no demo request — genuinely curious if the model holds up against a real production system."

Write the comment and post:
```bash
gh issue comment https://github.com/openclaw/openclaw/issues/42475 --body-file /tmp/yun-ask.md
```

### 1C. Set up monitoring
After posting, check back in 30 minutes:
```bash
gh issue view https://github.com/openclaw/openclaw/issues/42475 --comments 2>&1 | grep -A5 "@yun520-1"
```

---

## PHASE 2: CONVERT THE STRONGEST VALIDATION — @theonlyhennygod (15 min)

This person:
- Works on ZeroClaw (production agent framework)
- **Merged a pre-flight enforcement PR** after reading our argument
- You already asked 3 technical follow-up questions

### 2A. Read the thread
```bash
gh issue view https://github.com/zeroclaw-labs/zeroclaw/issues/2269 --comments 2>&1 | tail -80
```

### 2B. Craft a bridge from their PR to our product

They just shipped pre-flight enforcement. The bridge: "You built enforcement — you might want a benchmark to validate against."

```
The pre-flight enforcement PR is a strong signal — you're already thinking about this at the architecture level. One thing we found useful when building our enforcement engine: having a standardized eval gym to validate correctness.

Ours is 56 labeled scenarios across 9 rule types: https://agentshield.fly.dev/eval

If you're building similar enforcement logic, you might find the edge cases category useful — it covers boundary values, malformed inputs, and empty rulesets. All the scenarios are in tests/eval_gym.py (MIT licensed — steal anything useful).

Also — our risk calculator gives a rough baseline for what unprotected agent spend looks like at different scales. Feed it ZeroClaw's typical agent workloads? Curious how it maps to what you see.

Risk calc: https://agentshield.fly.dev/tools/risk-calculator/
```

Post:
```bash
gh issue comment https://github.com/zeroclaw-labs/zeroclaw/issues/2269 --body-file /tmp/zeroclaw-bridge.md
```

---

## PHASE 3: CONVERT THE ACTIVE DEVELOPERS (15 min — @sailikhithk, @Zayed024, @epamLDadayan)

For each of the remaining 3 active conversations, the pattern is: **acknowledge their specific work → offer a specific resource → soft CTL to risk calculator.**

### 3A. @sailikhithk — LangChain #31647 (cost tracking PR in progress)

```bash
gh issue view https://github.com/langchain-ai/langchain/issues/31647 --comments 2>&1 | tail -40
```

Draft: They're building cost tracking. Bridge: "You're building observability — here's what enforcement looks like as the complement."
Link to: https://agentshield.fly.dev/comparisons/langsmith (enforcement vs observability comparison page)

### 3B. @Zayed024 — RocketRide #1693 (design phase)

```bash
gh issue view https://github.com/rocketride-ai/rocketride/issues/1693 --comments 2>&1 | tail -40
```

Draft: They're in design phase — early enough to influence architecture. Bridge: "Before you finalize the cost estimation approach, here's a reference model."
Link to: https://agentshield.fly.dev/eval (show the rule types as a design reference)

### 3C. @epamLDadayan — Elitea #6010 (implementation phase)

```bash
gh issue view https://github.com/elitea-ai/elitea/issues/6010 --comments 2>&1 | tail -40
```

Draft: They're implementing. Bridge: "You mentioned UX improvements — here's what a live dashboard looks like for comparison."
Link to: https://agentshield.fly.dev/dashboard

Post all three:
```bash
gh issue comment <url> --body-file /tmp/langchain-bridge.md
gh issue comment <url> --body-file /tmp/rocketride-bridge.md
gh issue comment <url> --body-file /tmp/elitea-bridge.md
```

---

## PHASE 4: FRESH OUTREACH — CONVERSION-ORIENTED (15 min)

Unlike Phase 10-11 (volume play), this session's new outreach targets **people who are actively building or fixing something** — not just complaining.

### 4A. Search for builders, not complainers

```bash
# People actively working on cost-related PRs
gh search issues "cost" OR "budget" OR "spend" "agent" label:enhancement --limit 10 --state open --sort updated

# People discussing cost architecture
gh search issues "cost estimation" OR "budget enforcement" OR "spend control" "agent" --limit 10 --state open --sort updated

# Maintainers asking for cost features
gh search issues "feature request" "cost" OR "budget" "agent" label:"feature request" --limit 10 --state open --sort updated
```

### 4B. For each qualifying thread

Follow the conversion pattern:
1. **Acknowledge their work:** "Nice approach on [specific detail from their PR/issue]."
2. **Offer a specific resource:** Link to the relevant comparison page, eval gym, or risk calculator — not a generic "check us out."
3. **Soft CTL:** "Curious if [specific AgentShield feature] would complement what you're building."
4. **Disclosure + link.**

---

## PHASE 5: CHECK CONVERSION FALLBACK PATHS (10 min)

### 5A. Check if anyone used the risk calculator

```bash
# If analytics are captured:
curl -s https://agentshield.fly.dev/api/track -X POST -H 'Content-Type: application/json' -d '{"e":"check_risk_calc_usage","p":"/tools/risk-calculator/","t":'"$(date +%s)"'}' 2>&1

# The analytics endpoint returns {"ok": true} — but we can't count usage. 
# Instead, check if any email captures happened recently:
sqlite3 /Users/sipi/agentshield/agentshield.db "SELECT email, source, created_at FROM email_captures ORDER BY created_at DESC LIMIT 10;" 2>/dev/null || echo "DB not accessible locally — Fly.io only"
```

### 5B. Check trial signups
```bash
sqlite3 /Users/sipi/agentshield/agentshield.db "SELECT email, tier, created_at FROM accounts WHERE tier != 'free' ORDER BY created_at DESC LIMIT 10;" 2>/dev/null || echo "DB not accessible locally"
```

### 5C. Check Stripe for any activity
```bash
# Check if Stripe CLI is available:
which stripe 2>/dev/null && stripe customers list --limit 5 2>&1 || echo "Stripe CLI not available"
```

---

## PHASE 6: ADD A DIRECT TRIAL CTA TO THE RISK CALCULATOR (20 min)

If nobody has signed up, the funnel might have a leak. The risk calculator shows a score but doesn't have a strong enough call-to-action.

### 6A. Read the current risk calculator
```bash
read_file path="/Users/sipi/agentshield/public/tools/risk-calculator/index.html"
```

### 6B. Add a post-score CTA

After the risk score calculation, add a visible section:

```html
<div id="trial-cta" style="display:none;margin-top:24px;padding:20px;background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.3);border-radius:8px;text-align:center">
  <h3 style="color:#00d4aa;margin-bottom:8px">Protect Your Agents in 60 Seconds</h3>
  <p style="color:#888;margin-bottom:16px">Your risk score: <strong id="risk-score-display" style="color:#ff4757">—</strong>. 
  AgentShield Dev prevents this for $19/month. 14-day free trial. No credit card drama.</p>
  <a href="/dashboard" style="display:inline-block;padding:14px 32px;background:#00d4aa;color:#000;border-radius:8px;font-weight:700;text-decoration:none">Start 14-Day Free Trial →</a>
  <p style="color:#666;font-size:12px;margin-top:8px">Or <a href="https://github.com/kindrat86/agentshield" style="color:#00d4aa">self-host for free</a> (MIT license, 60-second deploy)</p>
</div>
```

Add JavaScript to show this div after score calculation and populate `#risk-score-display` with the computed score.

### 6C. Deploy
```bash
cd /Users/sipi/agentshield && fly deploy
```

Verify:
```bash
curl -s https://agentshield.fly.dev/tools/risk-calculator/ | grep -c "trial-cta"
```
Should return > 0.

---

## PHASE 7: VERIFY & COMMIT (5 min)

```bash
# Product health
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# Tests
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1 | tail -3

# Risk calc CTA
curl -s https://agentshield.fly.dev/tools/risk-calculator/ | grep -c "trial-cta"

# Email captures (if DB accessible)
sqlite3 /Users/sipi/agentshield/agentshield.db "SELECT COUNT(*) FROM email_captures;" 2>/dev/null

# Commit
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 12: Conversion push — trial CTAs, direct asks, risk calc upgrade"
git log --oneline -3
```

---

## REPORT FORMAT

```
## Phase 12 — Conversion Report

### Direct Asks Made
| # | Thread | Person | Ask | Response |
|---|--------|--------|-----|----------|
| 1 | OpenClaw #42475 | @yun520-1 | Run risk calculator with HeartFlow's numbers | [Pending/Replied/No response] |
| 2 | ZeroClaw #2269 | @theonlyhennygod | Use eval gym as benchmark for their PR | [Pending/Replied/No response] |
| 3 | LangChain #31647 | @sailikhithk | See enforcement comparison page | [Pending/Replied] |
| 4 | RocketRide #1693 | @Zayed024 | Use eval as reference architecture | [Pending/Replied] |
| 5 | Elitea #6010 | @epamLDadayan | Review live dashboard | [Pending/Replied] |

### Action Achieved
| Goal | Status | Evidence |
|------|--------|----------|
| Risk calculator used by a lead | [YES / NO] | [Evidence or "no way to verify"] |
| Trial signup | [YES / NO] | [SQLite query result] |
| Email captured | [YES / NO] | [SQLite query result] |
| Design partnership ask accepted | [YES / NO] | [Quote from reply] |

### Product Changes
- Risk calc CTA added: [YES / NO]
- Deployed: [YES / NO]

### Quality
- Health: [ok/error]
- Eval: [N]/56
- Tests: [N]/14
- Git: [hash]

### Conversion Funnel Health
- Total outreach posts: [count]
- Active conversations: [count]
- Direct "try it" asks: [count]
- Historical ask acceptance rate: [calculate from Phase 11-12]
- Estimated funnel: [21 posts → 5 conversations → 5 direct asks → ? trials]

### Next Session Priorities
1. [Immediate action based on who replied]
2. [Backup if nobody replied]
3. [Product improvement from feedback]
```

---

## HARD RULES

1. **KPI: Get ONE person to try the risk calculator or sign up.** Not "start 3 conversations." Not "post 10 comments." One measurable action from a real person.

2. **Every Phase 1-3 comment must include a specific, low-friction ask.** Not "check out our project." Not "let us know what you think." A concrete, 30-second action with no signup required.

3. **The risk calculator is the primary conversion tool.** It requires no signup, no commitment, no credit card. It's the easiest ask. Link to it in every conversation.

4. **@yun520-1 is priority #1.** They've already invested in the relationship (2 exchanges, feature suggestions). The ask must honor that investment.

5. **Never fabricate.** Show URLs. Show query results. Show eval numbers. If nobody replied, say "no replies yet."

6. **Never mention cron.**

7. **Never touch memory.**

8. **If nobody replies to the direct asks**, that's data, not failure. Report it honestly and note: "The outreach is generating technical conversations but not conversion. The problem may be the ask, the timing, or the audience. Consider: what would make a developer currently building cost features actually sign up for a cost product?"
