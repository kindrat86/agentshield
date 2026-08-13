# BRUNSON MAXIMUM CONVERSION IMPLEMENTATION PROMPT
## AgentShield Landing Page, Russell Brunson Secrets Trilogy Overhaul

**Project:** agentshield.fly.dev
**Repo:** ~/agentshield
**Stack:** Python 3.11 stdlib http.server → Fly.io (single VM, ams region, 256MB)
**Deploy:** `cd ~/agentshield && flyctl deploy --app agentshield`
**Live URL:** https://agentshield.fly.dev

---

## PROJECT CONTEXT

AgentShield is a per-transaction spend firewall for autonomous AI agents. It evaluates every API call against configurable budget rules in under 1ms, BEFORE the call executes. Pure Python stdlib, zero dependencies. 56/56 eval gym scenarios pass.

The founder (Maryan K.) lost $2,800 in 60 seconds when an AI agent entered a retry loop at 3 AM, making 21 calls at $133 each to a premium LLM endpoint. He built AgentShield to prevent this.

**Current pricing:** Free ($0), Dev ($19/mo), Team ($99/mo), Managed ($499/mo). Stripe wired and live.
**Current pages:** Landing (`/`), Audit (`/audit`), Story (`/the-2800-story`), Auth (`/auth`), Dashboard (`/dashboard`), Eval Gym (`/eval`), Eval Gym Spec (`/eval-gym-spec`), Bounty (`/bounty`), Challenge (`/challenge`), Free Audit (`/free-audit`), Risk Calculator (`/tools/risk-calculator/`), Blog (`/blog/zeroclaw-preflight-enforcement`), Comparisons (`/comparisons/helicone`, `/comparisons/langsmith`).

**File structure:**
- `public/index.html`, main landing page (static HTML, dark theme, ~428 lines)
- `public/*.html`, other static pages
- `core/api.py`, Python stdlib HTTP handler (~980 lines), routes via `if path == '/...'`
- `core/store.py`, SQLite data layer (~433 lines)
- `core/engine.py`, SpendControlEngine (~372 lines)
- `content/soap-opera-emails.md`, 5-day Soap Opera sequence ALREADY WRITTEN but NOT wired to send
- `fly.toml`, Fly.io config

---

## WHAT'S WRONG (Brunson Diagnostic)

The page has a **strong Hook + Story** (the $2,800 narrative is excellent) but is missing almost all **conversion machinery**. This is the classic "Ferrari Stories, Bicycle Funnels" pattern.

### Critical Gaps (in priority order):

1. **NO EMAIL SEQUENCE FIRES**, `/api/email-capture` stores the email in SQLite but sends NOTHING. The 5-day Soap Opera sequence exists in `content/soap-opera-emails.md` but is NOT wired to any email-sending code. `RESEND_API_KEY` is in `.env.example` but never used anywhere in the codebase. Every captured email goes into a black hole.

2. **NO TRIPWIRE**, There is no $7 impulse offer between Free and $19/mo. The jump from $0 to $228/year with no micro-commitment is a Brunson Ch 5 violation. The subscriber→buyer identity shift never happens.

3. **NO VALUE STACK**, The Dev tier ($19/mo) lists features but never shows the STACK: individual item values, strikethrough total, actual price. The visitor has no anchor for "this is a deal." (Brunson Ch 18 / DotCom Ch 8)

4. **NO FALSE BELIEF CRUSHER**, The page never names and destroys the 3 lies that hold the dream customer back: (a) "Rate limits already protect me," (b) "Budget alerts are enough," (c) "I'd notice if spending spiked." (Expert Secrets Ch 6)

5. **NO NAMED FRAMEWORK**, There's no proprietary methodology name. "AgentShield" is a product name, not a framework. Competitors can copy "9 rules." They can't copy a trademarked system. (Expert Secrets Ch 10-11)

6. **NO EXIT-INTENT POPUP**, Visitors who bounce are gone forever. No recovery mechanism. (DotCom Ch 16)

7. **FOUNDER IS INVISIBLE ON LANDING**, Maryan K. appears only on `/the-2800-story`. The landing page has no human face, no Attractive Character. (Expert Secrets Ch 2)

8. **NO ORDER BUMP**, No impulse add-on at checkout. "Add rule-config templates for $7?" (DotCom Ch 7 / Profit Maximizer)

9. **NO URGENCY/SCARCITY ON PRICING**, "7 spots left" is mentioned once in a banner but not integrated into the pricing section or checkout flow.

10. **RISK CALCULATOR BURIED**, The lead magnet (Risk Calculator) sits BELOW pricing. It should be the FIRST thing visitors interact with, capturing email BEFORE showing prices. The squeeze page purity rule is violated: pricing is visible before opt-in.

11. **NO DREAM CUSTOMER SPECIFICITY**, "Developers building AI agents" is a category, not a person. The page doesn't speak to ONE person with a name, a fear, and a Sunday-night feeling.

---

## IMPLEMENTATION: 14 CHANGES, ORDERED BY IMPACT

### CHANGE 1: Wire the Email Sequence (CRITICAL, fixes the black hole)

**Problem:** `/api/email-capture` captures emails but sends nothing. The Soap Opera sequence is written but dead.

**What to build:**

1. **Add a Resend email sender** to `core/api.py` using stdlib `urllib.request` (NO `requests` dependency, the Docker image is `python:3.11-slim` with no pip installs):

```python
def _send_resend_email(self, to_email: str, subject: str, html_body: str):
    """Send email via Resend API using stdlib urllib."""
    api_key = os.getenv('RESEND_API_KEY')
    if not api_key:
        return False
    import urllib.request, urllib.error, json
    data = json.dumps({
        "from": "AgentShield <noreply@sipiteno.com>",
        "to": [to_email],
        "subject": subject,
        "html": html_body
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False
```

2. **Modify `_handle_email_capture`** (line 737 of `core/api.py`) to send Soap Opera Day 1 email immediately on capture:

```python
def _handle_email_capture(self):
    body = self._read_body()
    email = body.get('email', '').strip()
    source = body.get('source', 'landing')
    if not email or '@' not in email:
        self._send_json({"error": "Valid email required"}, 400)
        return
    capture_id = self.store.capture_email(email, source)
    
    # Send Soap Opera Day 1 immediately
    day1_html = """<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a">
<h1 style="color:#ff4757">I lost $2,800 while I was sleeping</h1>
<p>At 3:14 AM, my phone buzzed. An email from my API provider.</p>
<p><strong>$2,793.00. In one hour. While I was asleep.</strong></p>
<p>An AI agent I'd deployed had entered a retry loop. Each retry cost $133. It retried 21 times before the budget alert even arrived.</p>
<p>The alert came at 3:14 AM. I read it at 6:17 AM. Three hours too late.</p>
<p>Every tool I had was reactive. Rate limits protect the provider. Budget alerts arrive by email. Dashboards show you what happened, after the money is gone.</p>
<p>Tomorrow I'll show you what I built to stop this from ever happening again.</p>
<p>, Maryan K.<br>AgentShield<br><a href="https://agentshield.fly.dev">https://agentshield.fly.dev</a></p>
</body></html>"""
    sent = self._send_resend_email(email, "I lost $2,800 while I was sleeping", day1_html)
    
    # Schedule remaining 4 emails by storing send dates
    # Days 2-5 are sent by a daily cron check (see CHANGE 1b below)
    self.store.schedule_email_sequence(email, capture_id)
    
    self._send_json({"success": True, "id": capture_id, "email_sent": sent}, 201)
```

3. **Add `schedule_email_sequence` to `core/store.py`**, create a new table `email_sequence`:

```python
def schedule_email_sequence(self, email: str, capture_id: str):
    """Schedule Soap Opera Days 2-5 and Seinfeld emails."""
    import time
    now = time.time()
    day = 86400  # 24 hours
    emails = [
        (email, capture_id, 'soap_day2', 'What if your agent asked permission before spending?', now + day),
        (email, capture_id, 'soap_day3', 'The rule that catches what daily budgets miss', now + day*2),
        (email, capture_id, 'soap_day4', '56 test scenarios that prove your spend control works', now + day*3),
        (email, capture_id, 'soap_day5', 'Your agents are running right now. Do they have a firewall?', now + day*4),
        (email, capture_id, 'seinfeld_1', 'The cheapest API call that cost $2,800', now + day*7),
        (email, capture_id, 'seinfeld_2', 'Why your rate limit is a speed bump, not a firewall', now + day*10),
        (email, capture_id, 'seinfeld_3', 'The 3 AM test: would your agent survive it?', now + day*14),
    ]
    self.conn.executemany(
        "INSERT OR IGNORE INTO email_sequence (email, capture_id, step, subject, send_at, sent) VALUES (?,?,?,?,?,0)",
        emails
    )
    self.conn.commit()
```

Add the table creation to `core/store.py` `__init__`:
```python
self.conn.execute("""
    CREATE TABLE IF NOT EXISTS email_sequence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        capture_id TEXT,
        step TEXT,
        subject TEXT,
        send_at REAL,
        sent INTEGER DEFAULT 0
    )""")
```

4. **Add a daily email-sending endpoint** `/api/email-cron` (protected by a secret header) that a Fly.io cron or external scheduler calls daily:

```python
elif path == '/api/email-cron':
    self._handle_email_cron()
```

```python
def _handle_email_cron(self):
    """Daily email sequence sender. Protected by CRON_SECRET."""
    cron_secret = os.getenv('CRON_SECRET', 'changeme')
    auth = self.headers.get('X-Cron-Secret', '')
    if auth != cron_secret:
        self._send_json({"error": "Unauthorized"}, 403)
        return
    import time, json
    now = time.time()
    rows = self.conn.execute(
        "SELECT id, email, step, subject FROM email_sequence WHERE sent = 0 AND send_at <= ? ORDER BY send_at LIMIT 50",
        (now,)
    ).fetchall()
    
    # Email content mapping (store as dict or load from file)
    email_bodies = self._get_email_bodies()  # Returns dict of step -> html
    
    sent_count = 0
    for row in rows:
        eid, email, step, subject = row
        body = email_bodies.get(step, '')
        if body:
            ok = self._send_resend_email(email, subject, body)
            if ok:
                self.conn.execute("UPDATE email_sequence SET sent = 1 WHERE id = ?", (eid,))
                sent_count += 1
    self.conn.commit()
    self._send_json({"sent": sent_count, "checked": len(rows)}, 200)
```

5. **Add `_get_email_bodies()`**, a method returning a dict mapping step keys to HTML email bodies. Parse the content from `content/soap-opera-emails.md` (already written) and add 3 Seinfeld follow-up emails.

**Verification:**
- `curl -s -X POST https://agentshield.fly.dev/api/email-capture -H 'Content-Type: application/json' -d '{"email":"test@sipiteno.com","source":"test"}'` must return `"email_sent": true`
- Check Resend dashboard for the sent email
- `curl -s https://agentshield.fly.dev/api/email-cron -H 'X-Cron-Secret: ...'` must return `{"sent": N}` 

---

### CHANGE 2: Add the Tripwire Page ($7 Spend-Control Starter Kit)

**Problem:** No impulse offer between Free and $19/mo. The subscriber→buyer identity shift never happens.

**What to build:**

Create `public/tripwire.html`, a standalone Brunson tripwire page:

**Offer:** "The AgentShield Spend-Control Starter Kit", $7 one-time
**Contents:**
- Pre-configured rule templates for OpenAI, Anthropic, and common agent patterns (JSON, ready to import)
- A copy of the $2,800 post-mortem playbook (the exact rules that would have prevented it)
- Rule-tuning checklist (what to set for different agent types)
- 30-min setup walkthrough (text-based, no video needed yet)

**Page structure (Brunson Tripwire Formula):**
1. **Headline:** "Get the Complete AgentShield Starter Kit for $7 (Normally $97, Today Only)"
2. **Value stack with strikethroughs:**
   - Rule Template Pack (OpenAI + Anthropic + LangChain configs), ~~$47~~
   - The $2,800 Post-Mortem Playbook, ~~$27~~
   - Rule-Tuning Checklist by Agent Type, ~~$17~~
   - 30-Min Setup Walkthrough, ~~$6~~
   - **Total value: $97 → Your price today: $7**
3. **Urgency:** "This price is only available right now. Leave this page and it's $97."
4. **Guarantee:** "If the starter kit doesn't save you $7 in the first week, email me and I'll refund you. Keep the kit."
5. **CTA:** "Get the Starter Kit for $7 →" (links to Stripe payment link or `/api/billing/checkout` with `tier: tripwire`)
6. **Decline link at bottom:** "No thanks, I'll pay full price later →" (links back to `/#pricing`)

**Stripe:** Create a $7 one-time payment link in Stripe. Store as `STRIPE_PRICE_TRIPWIRE` env var. Add checkout handler in `core/api.py`:
```python
'tripwire': os.getenv('STRIPE_PRICE_TRIPWIRE'),
```
Add to the `price_map` dict in `_handle_billing_checkout`. Use `'mode': 'payment'` (not subscription) for tripwire.

**Routing:** Add to `core/api.py` `do_GET`:
```python
elif path == '/tripwire':
    self._serve_public('tripwire.html')
```

**When to show it:** After email capture, redirect to `/tripwire`. Modify the email capture success flow in `public/index.html`:
```javascript
if (resp.ok) {
    window.location.href = '/tripwire';
}
```

**Design:** Match the dark theme (--bg #0a0a0a, --accent #00d4aa). Use the same CSS variables from index.html.

**Verification:**
- `curl -s https://agentshield.fly.dev/tripwire` returns 200 and contains the value stack
- The Stripe checkout link works (test in browser)
- The decline link goes back to `/#pricing`

---

### CHANGE 3: Rebuild the Landing Page Section Order (Squeeze Purity)

**Problem:** The landing page shows pricing BEFORE capturing email. This violates the squeeze page purity rule, every price anchor before opt-in reduces email capture conversion.

**New section order for `public/index.html`:**

1. **Hero** (existing, minor edits, see CHANGE 4)
2. **Stats bar** (existing, keep)
3. **3 False Beliefs Crusher** (NEW, see CHANGE 5)
4. **The $2,800 Story** (existing, keep but add Epiphany Bridge depth, see CHANGE 6)
5. **Risk Calculator / Lead Magnet** (MOVE THIS UP, before pricing, add email gate, see CHANGE 7)
6. **Named Framework** (NEW, see CHANGE 8)
7. **How It Works** (existing, keep)
8. **Value Stack for Dev Tier** (NEW, see CHANGE 9)
9. **Pricing** (existing, but now the visitor has already opted in via Risk Calculator)
10. **Founder / Attractive Character** (NEW, see CHANGE 10)
11. **Email Capture** (existing, keep as bottom-of-page secondary capture)
12. **FAQ** (NEW, see CHANGE 11)
13. **Footer** (existing, keep)

**Implementation:** This is a reordering + addition task in `public/index.html`. The file is static HTML, move `<section>` blocks, add new sections.

---

### CHANGE 4: Hero Section Edits

**Current hero:**
```
The Safety Layer for Autonomous AI Agents
[CTA: Check Your Risk Score] [CTA: Get $299 Audit]
```

**New hero copy (Brunson Hook/Story/Offer):**

**Eyebrow** (above headline): "As featured on: Dev.to · OpenClaw #42475 · GitHub" (keep)

**Headline:** "Stop AI Agents From Burning Your Budget"

**Subheadline (the Story bridge in one sentence):**
"Last month, an autonomous agent spent $2,800 in 60 seconds, while its developer slept. AgentShield evaluates every API call against your rules in under 1ms, BEFORE it executes. 9 composable rules. Zero dependencies. One kill switch."

**Primary CTA:** "Calculate Your Risk Score (30 sec, no signup) →" → links to `#risk-calculator`

**Secondary CTA:** "Read the $2,800 Story →" → links to `/the-2800-story`

**Remove the $299 Audit CTA from the hero**, too many CTAs dilute. The audit is offered AFTER the risk calculator and email capture.

**Add an urgency micro-line below CTAs:**
"⚡ 56/56 eval scenarios passing · <1ms per transaction · 0 pip dependencies · MIT licensed"

---

### CHANGE 5: The 3 False Beliefs Crusher (NEW SECTION)

**Insert after stats bar, before the $2,800 story.**

**Brunson framework:** Name the 3 lies your dream customer believes, then crush each with truth.

**Section structure:**

```html
<section class="false-beliefs" style="padding:60px 0">
  <div class="container">
    <h2 style="text-align:center;font-size:2em;margin-bottom:16px">The 3 Dangerous Lies About AI Agent Spending</h2>
    <p style="text-align:center;color:var(--muted);margin-bottom:40px;max-width:600px;margin-left:auto;margin-right:auto">
      Most developers believe at least one of these. Each one can cost you thousands.
    </p>
    
    <!-- Lie 1: The Vehicle -->
    <div class="belief-card" style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:32px;margin-bottom:24px">
      <div style="display:flex;align-items:start;gap:16px">
        <div style="font-size:2em;color:var(--danger)">❌</div>
        <div>
          <h3 style="color:var(--danger);margin-bottom:8px">Lie #1: "API rate limits already protect me."</h3>
          <p style="color:var(--muted);margin-bottom:12px">Rate limits protect the API <em>provider</em>, not you. Your provider is happy to let your agent make 21 calls at $133 each, they get paid either way. A rate limit caps requests per second. It does not cap dollars per transaction, dollars per day, or dollars per session.</p>
          <div style="padding:16px;background:rgba(0,212,170,0.08);border-radius:8px;border-left:3px solid var(--accent)">
            <strong style="color:var(--accent)">Truth:</strong> AgentShield evaluates the <em>dollar amount</em> of each transaction before it executes. $133 call when your limit is $50? Blocked. Instantly.
          </div>
        </div>
      </div>
    </div>
    
    <!-- Lie 2: Internal Belief -->
    <div class="belief-card" style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:32px;margin-bottom:24px">
      <div style="display:flex;align-items:start;gap:16px">
        <div style="font-size:2em;color:var(--danger)">❌</div>
        <div>
          <h3 style="color:var(--danger);margin-bottom:8px">Lie #2: "I set up budget alerts. I'd notice."</h3>
          <p style="color:var(--muted);margin-bottom:12px">Budget alerts arrive by email. If your agent runs at 3 AM, the alert fires at 3:14 AM. You read it at 6:17 AM. By then, the damage is done. Alerts tell you what <em>happened</em>. They cannot prevent what's <em>about to happen</em>.</p>
          <div style="padding:16px;background:rgba(0,212,170,0.08);border-radius:8px;border-left:3px solid var(--accent)">
            <strong style="color:var(--accent)">Truth:</strong> AgentShield blocks the transaction <em>before</em> it hits the API. No alert needed. The call never happens. Your wallet stays closed.
          </div>
        </div>
      </div>
    </div>
    
    <!-- Lie 3: External -->
    <div class="belief-card" style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:32px">
      <div style="display:flex;align-items:start;gap:16px">
        <div style="font-size:2em;color:var(--danger)">❌</div>
        <div>
          <h3 style="color:var(--danger);margin-bottom:8px">Lie #3: "I only run a few agents. I can monitor manually."</h3>
          <p style="color:var(--muted);margin-bottom:12px">Manual monitoring doesn't scale past 3 agents. And even with 1 agent, you'd have to watch it 24/7. Agents don't sleep. They don't take weekends off. They don't hesitate before retrying a failed call that costs $133.</p>
          <div style="padding:16px;background:rgba(0,212,170,0.08);border-radius:8px;border-left:3px solid var(--accent)">
            <strong style="color:var(--accent)">Truth:</strong> AgentShield runs 24/7, evaluates in under 1ms, and works across unlimited agents with multi-tenant isolation. It never sleeps, never blinks, never misses.
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
```

---

### CHANGE 6: Deepen the $2,800 Story (Epiphany Bridge Enhancement)

**The story section already exists. Add the Epiphany Bridge arc to the landing page version** (the full version is on `/the-2800-story`):

**Add after the existing problem-card compare section, before "How It Works":**

```html
<section class="epiphany" style="padding:60px 0;background:var(--surface)">
  <div class="container" style="max-width:700px">
    <h2 style="text-align:center;font-size:2em;margin-bottom:32px">The Moment Everything Changed</h2>
    <div style="font-size:1.1em;line-height:1.8;color:#ccc">
      <p style="margin-bottom:16px">I sat in bed at 6:17 AM, staring at the email. <strong style="color:var(--danger)">$2,793.00.</strong></p>
      <p style="margin-bottom:16px">I checked my rate limits, fine. The provider was happy to take 21 calls at $133 each.</p>
      <p style="margin-bottom:16px">I checked my budget alerts, they triggered at 3:14 AM, right on schedule. I just didn't see them until morning.</p>
      <p style="margin-bottom:16px">I checked my observability dashboard, beautiful graphs. Clear breakdowns. <em style="color:var(--muted)">Zero prevention.</em></p>
      <p style="margin-bottom:16px;font-size:1.2em;color:var(--accent)">And then I realized: every tool I had was reactive. They told me what happened <em>after</em> the money was spent. None of them could stop the transaction <em>before</em> it executed.</p>
      <p style="margin-bottom:16px">So I built one that could.</p>
      <p style="margin-bottom:24px">If that agent had been running AgentShield, the second call, the first retry, would have been blocked at <strong>$266</strong>. Not $2,793.</p>
    </div>
    <div style="text-align:center">
      <a href="/the-2800-story" style="display:inline-block;padding:14px 32px;background:transparent;border:1px solid var(--accent);color:var(--accent);border-radius:8px;font-weight:700;text-decoration:none">Read the Full Story →</a>
    </div>
  </div>
</section>
```

---

### CHANGE 7: Upgrade the Risk Calculator (Lead Magnet + Email Gate)

**Problem:** The Risk Calculator is good but buried below pricing. It needs to be the PRIMARY interaction and capture email BEFORE showing results.

**Changes to the risk calculator section:**

1. **Move the `<section class="risk-calc">` block** ABOVE the pricing section (should already be repositioned by CHANGE 3).

2. **Add an email gate:** Before showing the risk score, ask for email. The flow:
   - User fills in 4 inputs (agents, amount, frequency, budget)
   - Clicks "Calculate My Risk"
   - A small inline form appears: "Enter your email to see your full risk report + recommended firewall rules"
   - User enters email → POST to `/api/email-capture` → email stored + Soap Opera Day 1 sent → risk score + recommendations revealed
   - Below the score: CTA to `/tripwire` ("Get the Starter Kit that fixes this for $7 →")

3. **Enhance the risk calculator output:**
   After showing the score, add a "What This Means" section with specific scenarios:
   ```
   Your Risk Score: 72/100, HIGH RISK
   
   At your current setup:
   - Monthly projected spend: $X
   - Worst-case runaway (1 hour): $Y
   - Time to detect with alerts alone: 3+ hours
   
   AgentShield would cap this at: $[budget], guaranteed.
   
   Recommended rules:
   - Set transaction_limit to $[amount*3]
   - Set velocity rule: max [freq*2] per hour
   - Set daily_total cap to $[budget/agents*0.8]
   - Enable SSE real-time alerts
   ```

4. **Add a CTA below the results:**
   "Want these rules pre-configured? Get the $7 Starter Kit with ready-to-import templates →" → links to `/tripwire`

---

### CHANGE 8: Named Framework (Proprietary Methodology)

**Problem:** No trademarked methodology. "9 rules" is a feature list, not IP.

**Framework name:** "The Pre-Flight Enforcement Protocol™"

**3-step methodology:**
1. **SCREEN**, Every transaction is intercepted before it reaches the API
2. **EVALUATE**, 9 composable rules check the transaction against your budget in under 1ms
3. **ENFORCE**, Approved calls pass through. Blocked calls return a structured error. Kill switch stops everything.

**Add this section** between "How It Works" and the Value Stack:

```html
<section class="framework" style="padding:60px 0">
  <div class="container">
    <h2 style="text-align:center;font-size:2em;margin-bottom:16px">The Pre-Flight Enforcement Protocol™</h2>
    <p style="text-align:center;color:var(--muted);margin-bottom:40px;max-width:600px;margin-left:auto;margin-right:auto">
      Not monitoring. Not alerts. Not dashboards. <strong style="color:var(--accent)">Enforcement.</strong>
    </p>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px">
      <div style="text-align:center;padding:32px;background:var(--surface);border-radius:12px;border:1px solid var(--border)">
        <div style="font-size:2em;margin-bottom:12px">🔍</div>
        <h3 style="color:var(--accent);margin-bottom:8px;font-size:1.1em">1. SCREEN</h3>
        <p style="color:var(--muted);font-size:0.95em">Every API call is intercepted and routed through the evaluation engine before it reaches your provider. The agent never knows it's being checked.</p>
      </div>
      <div style="text-align:center;padding:32px;background:var(--surface);border-radius:12px;border:1px solid var(--border)">
        <div style="font-size:2em;margin-bottom:12px">⚡</div>
        <h3 style="color:var(--accent);margin-bottom:8px;font-size:1.1em">2. EVALUATE</h3>
        <p style="color:var(--muted);font-size:0.95em">9 composable rule types, transaction limits, daily caps, velocity, allowlists, category blocks, session budgets, cascade costs, evaluated in priority order. Under 1ms per call.</p>
      </div>
      <div style="text-align:center;padding:32px;background:var(--surface);border-radius:12px;border:1px solid var(--border)">
        <div style="font-size:2em;margin-bottom:12px">🛡️</div>
        <h3 style="color:var(--accent);margin-bottom:8px;font-size:1.1em">3. ENFORCE</h3>
        <p style="color:var(--muted);font-size:0.95em">Approved calls pass through to the API. Blocked calls return a structured JSON error the agent can handle. Emergency kill switch stops everything, instantly.</p>
      </div>
    </div>
    <p style="text-align:center;margin-top:24px;color:var(--muted);font-size:0.9em">
      Monitor = watch it burn. Alert = email about the fire. Enforce = stop the match before it strikes.
    </p>
  </div>
</section>
```

**Also add the framework name to:**
- The hero subheadline (mention "Pre-Flight Enforcement Protocol")
- The `/the-2800-story` page
- The `/audit` page
- The JSON-LD structured data in `<head>`
- The meta description

---

### CHANGE 9: Value Stack for the Dev Tier (Brunson "The Stack")

**Problem:** $19/mo is presented as a feature list. No value anchoring.

**Add BEFORE the pricing grid** (or replace the Dev card's feature list):

```html
<section class="value-stack" style="padding:60px 0;background:var(--surface)">
  <div class="container" style="max-width:600px">
    <h2 style="text-align:center;font-size:2em;margin-bottom:16px">What You Actually Get (Dev Tier)</h2>
    <p style="text-align:center;color:var(--muted);margin-bottom:32px">This isn't software. It's an insurance policy that works in 1ms.</p>
    <div style="background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:32px">
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)">
        <span>5 AI agents with API keys</span>
        <span style="text-decoration:line-through;color:var(--muted)">$95/mo value</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)">
        <span>10 custom enforcement rules</span>
        <span style="text-decoration:line-through;color:var(--muted)">$50/mo value</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)">
        <span>1,000 daily evaluations (<1ms each)</span>
        <span style="text-decoration:line-through;color:var(--muted)">$29/mo value</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)">
        <span>Email + SSE real-time alerts</span>
        <span style="text-decoration:line-through;color:var(--muted)">$19/mo value</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)">
        <span>Full API access + dashboard</span>
        <span style="text-decoration:line-through;color:var(--muted)">$15/mo value</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)">
        <span>One prevented $2,800 incident</span>
        <span style="text-decoration:line-through;color:var(--muted)">$2,800 value</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:16px 0 8px;font-size:1.1em;font-weight:700">
        <span>Total real-world value</span>
        <span style="text-decoration:line-through;color:var(--danger)">$3,008/mo</span>
      </div>
      <div style="text-align:center;padding:24px 0">
        <div style="font-size:3em;font-weight:800;color:var(--accent)">$19<span style="font-size:0.4em;color:var(--muted)">/mo</span></div>
        <div style="color:var(--muted);font-size:0.9em;margin-bottom:16px">14-day free trial. No credit card required.</div>
        <a href="/auth" class="cta-btn" style="background:var(--accent);color:#000;padding:16px 40px;border-radius:8px;font-weight:700;text-decoration:none;display:inline-block">Start Free Trial →</a>
      </div>
    </div>
    <p style="text-align:center;margin-top:16px;color:var(--accent);font-size:0.9em">
      💰 An unprotected runaway agent: <strong>$2,800</strong>. A whole year of AgentShield: <strong>$228</strong>.
    </p>
  </div>
</section>
```

**IMPORTANT:** The $3,008/mo strikethrough is anchored on the real $2,800 incident + actual service values. Do NOT inflate or invent. If the math doesn't add up honestly, use lower anchors. The honesty brand is non-negotiable, never use fabricated value anchors.

---

### CHANGE 10: Attractive Character / Founder Section

**Problem:** No human on the landing page. People follow people.

**Add before the footer / email capture:**

```html
<section class="founder" style="padding:60px 0">
  <div class="container" style="max-width:700px">
    <div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap">
      <div style="flex:1;min-width:300px">
        <h2 style="font-size:1.8em;margin-bottom:16px">Hi, I'm Maryan.</h2>
        <div style="color:#ccc;font-size:1.05em;line-height:1.7">
          <p style="margin-bottom:12px">I'm a developer who lost $2,800 in 60 seconds because my AI agent didn't know when to stop.</p>
          <p style="margin-bottom:12px">I checked my rate limits, my budget alerts, my dashboards. They all worked perfectly. They just couldn't <em>prevent</em> anything, only report on what already happened.</p>
          <p style="margin-bottom:12px">So I built the thing I wished existed: a firewall that evaluates every transaction <em>before</em> it executes. In under 1ms. With zero dependencies. Open source under MIT.</p>
          <p style="margin-bottom:12px">I'm not a security company. I'm a developer who got a $2,800 bill at 3 AM and decided it would never happen again.</p>
          <p style="margin-top:16px;font-size:0.9em;color:var(--muted)">
            <a href="https://github.com/kindrat86" style="color:var(--accent)">GitHub</a> ·
            <a href="/the-2800-story" style="color:var(--accent)">My $2,800 Story</a> ·
            <a href="https://agentshield.fly.dev/eval" style="color:var(--accent)">56-Scenario Eval Gym</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</section>
```

**NOTE:** Do NOT invent a photo. The founder hasn't provided one. Use a text-only section with the dark theme. If the founder later provides a headshot, it can be added with `<img>` in the left column.

---

### CHANGE 11: FAQ Section (4-Question Close Framework)

**Add before the email capture section:**

```html
<section class="faq" style="padding:60px 0;background:var(--surface)">
  <div class="container" style="max-width:700px">
    <h2 style="text-align:center;font-size:2em;margin-bottom:32px">Questions You're Asking Right Now</h2>
    
    <div style="margin-bottom:24px">
      <h3 style="color:var(--accent);margin-bottom:8px">"Will this slow down my agents?"</h3>
      <p style="color:var(--muted)">No. Every evaluation takes less than 1 millisecond. Your agents won't notice. The evaluation happens in Python stdlib, no network round trip, no external service.</p>
    </div>
    
    <div style="margin-bottom:24px">
      <h3 style="color:var(--accent);margin-bottom:8px">"Do I need to rewrite my agent code?"</h3>
      <p style="color:var(--muted)">No. You route transactions through one endpoint, <code>/v1/transactions/evaluate</code>, before they execute. One line of integration. Your agent gets a structured JSON response: approved or blocked, with the reason.</p>
    </div>
    
    <div style="margin-bottom:24px">
      <h3 style="color:var(--accent);margin-bottom:8px">"What if a rule blocks a legitimate transaction?"</h3>
      <p style="color:var(--muted)">Rules are yours to configure. Start permissive, tighten as you learn your patterns. Every block is logged with the rule that fired and the transaction details. You can adjust rules via dashboard or API in real time.</p>
    </div>
    
    <div style="margin-bottom:24px">
      <h3 style="color:var(--accent);margin-bottom:8px">"Is this just another monitoring tool?"</h3>
      <p style="color:var(--muted)">No. Monitoring tools watch costs after they happen. Dashboards show you beautiful graphs of your money burning. AgentShield <em>blocks the transaction before it executes</em>. It's the difference between a smoke detector and a fire extinguisher.</p>
    </div>
    
    <div style="margin-bottom:24px">
      <h3 style="color:var(--accent);margin-bottom:8px">"What if it doesn't work for my setup?"</h3>
      <p style="color:var(--muted)">14-day free trial, no credit card. If it doesn't fit, you've lost nothing. The open-source engine is MIT licensed, you can self-host forever for free. The $299 audit has a money-back guarantee: if we don't find $299 in preventable waste, full refund.</p>
    </div>
    
    <div style="margin-bottom:24px">
      <h3 style="color:var(--accent);margin-bottom:8px">"Can I just use rate limits and alerts?"</h3>
      <p style="color:var(--muted)">You can. I did, too. Mine worked perfectly. They triggered at 3:14 AM. I read the email at 6:17 AM. Three hours too late. Rate limits protect the provider. Alerts arrive by email. Neither one can stop a transaction before it executes. That's what AgentShield does.</p>
    </div>
  </div>
</section>
```

---

### CHANGE 12: Exit-Intent Popup

**Problem:** Visitors who bounce are gone forever.

**Add to `public/index.html` `<head>` (CSS) and before `</body>` (JS):**

```html
<!-- Exit intent CSS -->
<style>
.exit-modal-overlay {
  display:none; position:fixed; top:0; left:0; width:100%; height:100%;
  background:rgba(0,0,0,0.85); z-index:9999; justify-content:center; align-items:center;
}
.exit-modal-overlay.show { display:flex; }
.exit-modal {
  background:var(--surface); border:1px solid var(--accent); border-radius:16px;
  padding:48px; max-width:480px; text-align:center; position:relative;
}
.exit-modal h2 { color:var(--accent); font-size:1.8em; margin-bottom:12px; }
.exit-modal p { color:var(--muted); margin-bottom:24px; }
.exit-modal .close-btn {
  position:absolute; top:12px; right:16px; background:none; border:none;
  color:var(--muted); font-size:1.5em; cursor:pointer;
}
.exit-modal input {
  width:100%; padding:14px; margin-bottom:12px; background:var(--bg);
  border:1px solid var(--border); border-radius:6px; color:var(--text); font-size:1em;
}
.exit-modal button {
  width:100%; padding:14px; background:var(--accent); color:#000; border:none;
  border-radius:6px; font-weight:700; font-size:1.05em; cursor:pointer;
}
</style>

<!-- Exit intent HTML -->
<div class="exit-modal-overlay" id="exit-overlay">
  <div class="exit-modal">
    <button class="close-btn" onclick="document.getElementById('exit-overlay').classList.remove('show')">×</button>
    <h2>Wait, Before You Go</h2>
    <p>Get the <strong>AgentShield Spend-Control Starter Kit</strong> for just <strong style="color:var(--accent)">$7</strong> (normally $97). Pre-configured rule templates for OpenAI, Anthropic, and LangChain. The exact rules that would have prevented the $2,800 incident.</p>
    <a href="/tripwire" style="display:block;padding:14px;background:var(--accent);color:#000;border-radius:6px;font-weight:700;text-decoration:none;margin-bottom:8px">Get the $7 Starter Kit →</a>
    <p style="font-size:0.85em;color:var(--muted)">This price is only available on this page.</p>
  </div>
</div>

<!-- Exit intent JS (desktop: mouseleave, mobile: scroll-up) -->
<script>
(function() {
  var shown = false;
  // Desktop: mouse leaves top of page
  document.addEventListener('mouseleave', function(e) {
    if (e.clientY <= 0 && !shown && sessionStorage.getItem('exit_shown') !== '1') {
      shown = true;
      sessionStorage.setItem('exit_shown', '1');
      document.getElementById('exit-overlay').classList.add('show');
      // Track
      try { navigator.sendBeacon('/api/track', JSON.stringify({e:'exit_intent_shown',p:location.pathname,t:Date.now()})); } catch(e){}
    }
  });
  // Mobile: rapid scroll up after scrolling down 35%+
  var lastScroll = window.scrollY;
  var triggered = false;
  window.addEventListener('scroll', function() {
    var scrollY = window.scrollY;
    var pageHeight = document.body.scrollHeight - window.innerHeight;
    if (pageHeight <= 0) return;
    var scrollPct = scrollY / pageHeight;
    if (scrollPct > 0.35 && scrollY < lastScroll - 50 && !triggered && !shown && sessionStorage.getItem('exit_shown') !== '1') {
      triggered = true;
      shown = true;
      sessionStorage.setItem('exit_shown', '1');
      document.getElementById('exit-overlay').classList.add('show');
      try { navigator.sendBeacon('/api/track', JSON.stringify({e:'exit_intent_shown_mobile',p:location.pathname,t:Date.now()})); } catch(e){}
    }
    lastScroll = scrollY;
  }, { passive: true });
})();
</script>
```

---

### CHANGE 13: Order Bump on Checkout

**Problem:** No impulse add-on at checkout.

**Implementation:** In the Stripe checkout flow, add an order bump. Since this uses Stripe Checkout Sessions (not a custom checkout page), implement as a pre-checkout upsell page.

Create `public/checkout-bump.html`, a lightweight page shown BEFORE redirecting to Stripe:

```
Headline: "Wait, Add the Rule Template Pack for $7?"
Body: "Pre-configured enforcement rule templates for OpenAI, Anthropic, LangChain, and common agent patterns. Import-ready JSON. Normally $47, add it to your order for just $7."
[ ] Yes, add the Rule Template Pack (+$7)
[ ] No thanks, just the subscription
```

**Routing:** Add `/checkout` route in `core/api.py`:
```python
elif path == '/checkout':
    self._serve_public('checkout-bump.html')
```

**Modify the Dev tier CTA** in `public/index.html` to go to `/checkout?tier=dev` instead of directly to `/auth`. The checkout page shows the bump, then redirects to `/api/billing/checkout` with the chosen tier.

**Note:** This requires a separate Stripe payment link for the bump. Create a $7 one-time product and store as `STRIPE_PRICE_BUMP`.

---

### CHANGE 14: Final CTA Section (Cost of Inaction)

**Replace the current bottom audit banner with a stronger "Two Futures" section:**

```html
<section class="two-futures" style="padding:60px 0;background:var(--surface)">
  <div class="container">
    <h2 style="text-align:center;font-size:2em;margin-bottom:40px">Two Futures. Your Choice.</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
      
      <!-- Future 1: Do Nothing -->
      <div style="padding:32px;border-radius:12px;background:rgba(255,71,87,0.08);border:1px solid rgba(255,71,87,0.2)">
        <h3 style="color:var(--danger);margin-bottom:16px">Without AgentShield</h3>
        <ul style="list-style:none;color:var(--muted)">
          <li style="padding:6px 0">✗ Your agents run 24/7 with no spend guardrails</li>
          <li style="padding:6px 0">✗ A single retry loop can cost $2,800+ in minutes</li>
          <li style="padding:6px 0">✗ You find out via email, hours too late</li>
          <li style="padding:6px 0">✗ Rate limits protect the provider, not you</li>
          <li style="padding:6px 0">✗ Dashboards show beautiful graphs of your money burning</li>
          <li style="padding:6px 0">✗ Scale to 10+ agents and monitoring becomes impossible</li>
        </ul>
      </div>
      
      <!-- Future 2: With AgentShield -->
      <div style="padding:32px;border-radius:12px;background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.2)">
        <h3 style="color:var(--accent);margin-bottom:16px">With AgentShield</h3>
        <ul style="list-style:none;color:var(--muted)">
          <li style="padding:6px 0">✓ Every transaction evaluated in under 1ms, before it executes</li>
          <li style="padding:6px 0">✓ Runaway agents blocked on the first retry, at $266, not $2,800</li>
          <li style="padding:6px 0">✓ Real-time SSE alerts the instant a block fires</li>
          <li style="padding:6px 0">✓ 9 composable rule types, fully configurable</li>
          <li style="padding:6px 0">✓ Multi-tenant isolation, scale to unlimited agents safely</li>
          <li style="padding:6px 0">✓ Sleep through the night knowing your wallet is locked</li>
        </ul>
      </div>
    </div>
    <div style="text-align:center;margin-top:32px">
      <a href="#risk-calculator" class="cta-btn" style="font-size:1.1em;padding:18px 40px">Start With Your Free Risk Score →</a>
      <p style="margin-top:12px;color:var(--muted);font-size:0.9em">30 seconds. No signup. No credit card.</p>
    </div>
  </div>
</section>
```

---

## DEPLOYMENT INSTRUCTIONS

### Pre-deploy checklist:

1. **Create Stripe products** (manual, human action):
   - Tripwire: $7 one-time payment, "AgentShield Starter Kit" → save as `STRIPE_PRICE_TRIPWIRE`
   - Order bump: $7 one-time, "Rule Template Pack" → save as `STRIPE_PRICE_BUMP`

2. **Set Fly.io secrets:**
   ```bash
   flyctl secrets set --app agentshield RESEND_API_KEY=re_xxxxx
   flyctl secrets set --app agentshield STRIPE_PRICE_TRIPWIRE=price_xxxxx
   flyctl secrets set --app agentshield STRIPE_PRICE_BUMP=price_xxxxx
   flyctl secrets set --app agentshield CRON_SECRET=$(python3.11 -c "import secrets; print(secrets.token_hex(16))")
   ```

3. **Verify Resend domain:** `sipiteno.com` is already verified with Resend. Confirm `noreply@sipiteno.com` works.

### Deploy:

```bash
cd ~/agentshield
flyctl deploy --app agentshield
```

Wait for deploy to complete (~2 min). Verify:
```bash
curl -s https://agentshield.fly.dev/health
# Must return: {"status":"ok","version":"1.0.0"}

curl -s -o /dev/null -w "%{http_code}" https://agentshield.fly.dev/tripwire
# Must return: 200

curl -s -o /dev/null -w "%{http_code}" https://agentshield.fly.dev/checkout
# Must return: 200
```

### Post-deploy verification:

1. **Email capture → sequence:**
   ```bash
   curl -s -X POST https://agentshield.fly.dev/api/email-capture \
     -H 'Content-Type: application/json' \
     -d '{"email":"test@sipiteno.com","source":"deploy_test"}'
   # Must return: {"success":true,"id":"...","email_sent":true}
   ```
   Check Resend dashboard → email delivered.

2. **Email cron:**
   ```bash
   curl -s https://agentshield.fly.dev/api/email-cron \
     -H "X-Cron-Secret: $CRON_SECRET"
   # Must return: {"sent":N,"checked":M}
   ```

3. **Set up daily cron** for the email sequence (Fly.io scheduled task or external cron):
   ```bash
   # Add to fly.toml or use a cron service hitting:
   curl -s https://agentshield.fly.dev/api/email-cron -H "X-Cron-Secret: ..."
   ```
   Schedule: every 4 hours (so emails go out within 4h of their scheduled time).

4. **Full landing page visual check:**
   ```bash
   curl -s https://agentshield.fly.dev/ | grep -c "false-beliefs\|Pre-Flight Enforcement\|value-stack\|exit-modal\|two-futures\|founder"
   # Must return 6+ (each section present)
   ```

5. **Ghost page check:**
   Verify no broken links. All new routes (`/tripwire`, `/checkout`) must return 200.

---

## PITFALLS TO AVOID

1. **Do NOT use `patch()` for multi-line insertions into Python f-strings.** The escaping mangles newlines. Use `write_file` to rewrite `core/api.py` sections, or use a Python script via `terminal()` that reads the file, does `str.replace()`, and writes it back.

2. **Do NOT use `requests` library.** The Docker image is `python:3.11-slim`, no pip installs. Use `urllib.request` for ALL HTTP calls (Resend API, Stripe API).

3. **Do NOT add `requests` to requirements.txt.** The zero-dependency claim is a CORE product feature. Any email/HTTP code must use stdlib only.

4. **Verify Resend domain:** `sipiteno.com` is verified. Do NOT use `@agentshield.fly.dev` as the from-address, Resend requires a verified domain.

5. **Do NOT invent testimonials.** The honesty brand is non-negotiable. The existing "Beta audit participant" quote on `/audit` is the only testimonial. Do NOT fabricate more.

6. **Do NOT inflate the value stack numbers.** The $2,800 figure is real (it's the founder's actual incident). The per-feature values must be reasonable estimates of what those features would cost as standalone services. If unsure, use lower anchors.

7. **Match the existing dark theme.** All new sections must use: `--bg: #0a0a0a`, `--surface: #141414`, `--accent: #00d4aa`, `--text: #e8e8e8`, `--muted: #888`. Do NOT introduce new color variables.

8. **Mobile responsive.** All new grid sections must collapse to single-column on mobile. Add `@media (max-width: 768px)` rules for any new grid layouts.

9. **Test the email capture endpoint BEFORE deploying.** Run locally: `python3.11 run_app.py` → `curl -X POST localhost:7100/api/email-capture ...` → check `email_sent: true`.

10. **The `email_sequence` table must be created in `store.py` `__init__`**, NOT as a migration script. The SQLite DB is ephemeral on Fly.io (unless on a volume). The `CREATE TABLE IF NOT EXISTS` pattern in `__init__` handles this.

---

## SUMMARY: Expected Score Lift

| Brunson Chapter | Current | After | Key Change |
|---|---|---|---|
| DotCom Ch 4 (Lead Magnet) | 45 | 80 | Risk calc repositioned + email-gated |
| DotCom Ch 5 (Tripwire) | 0 | 75 | New $7 starter kit page |
| DotCom Ch 6 (Email Capture) | 25 | 85 | Resend wired + Soap Opera fires |
| DotCom Ch 7 (Profit Maximizer) | 10 | 60 | Order bump + tripwire |
| DotCom Ch 8 (Funnel Scripts/HSO) | 55 | 85 | Value stack + full offer |
| DotCom Ch 16 (Funnel Audibles) | 0 | 70 | Exit-intent popup |
| Expert Ch 2 (Attractive Character) | 20 | 70 | Founder section on landing |
| Expert Ch 6 (3 False Beliefs) | 0 | 80 | False belief crusher section |
| Expert Ch 10-11 (Named Framework) | 10 | 80 | Pre-Flight Enforcement Protocol™ |

**Overall Brunson score estimate: ~35/100 → ~72/100**

---

## IMPLEMENTATION ORDER (do in this sequence)

1. **CHANGE 1**, Wire email sequence (highest impact, fixes the black hole)
2. **CHANGE 3**, Reorder landing page sections
3. **CHANGE 4**, Hero edits
4. **CHANGE 5**, False beliefs crusher
5. **CHANGE 6**, Epiphany bridge depth
6. **CHANGE 7**, Risk calculator email gate + repositioning
7. **CHANGE 8**, Named framework
8. **CHANGE 9**, Value stack
9. **CHANGE 10**, Founder section
10. **CHANGE 11**, FAQ section
11. **CHANGE 2**, Tripwire page
12. **CHANGE 12**, Exit-intent popup
13. **CHANGE 13**, Order bump
14. **CHANGE 14**, Two futures / cost of inaction

After each change, verify locally (`python3.11 run_app.py` → check at `localhost:7100`). Deploy once all changes are verified.

---

## ENVIRONMENT VARIABLES NEEDED

```bash
# Already set on Fly.io:
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_DEV=price_xxx
STRIPE_PRICE_TEAM=price_xxx
STRIPE_PRICE_MANAGED=price_xxx
LICENSING_MASTER_SECRET=xxx

# Needs to be set:
RESEND_API_KEY=re_xxx  # Already in .env.example, verify it's on Fly.io
STRIPE_PRICE_TRIPWIRE=price_xxx  # NEW, create $7 one-time in Stripe
STRIPE_PRICE_BUMP=price_xxx  # NEW, create $7 one-time in Stripe
CRON_SECRET=xxx  # NEW, generate random hex
```

Check current Fly.io secrets: `flyctl secrets list --app agentshield`

---

**END OF PROMPT.** Feed this entire document to a Hermes Agent session as the task prompt. The agent should work autonomously through all 14 changes, verify locally, then deploy. Report any Stripe product creation as a human-action item, the agent cannot create Stripe products without dashboard access.
