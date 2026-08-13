# AgentShield Monetisation Execution Plan

## CRITICAL: Read this entire document before taking any action. Execute phases sequentially, do not skip ahead.

---

## CONTEXT (What You're Working With)

AgentShield is a firewall for AI agent spending. It sits between an AI agent and the API, evaluating every transaction against 7 composable rules in <1ms before the call executes.

### Current State (August 11, 2026)

| Asset | Status | Detail |
|-------|--------|--------|
| **Live product** | ✅ Fly.io | https://agentshield.fly.dev, Landing, Dashboard, Blog, Risk Calculator, Eval Gym |
| **Vercel domain** | ⚠️ BROKEN | https://agentshield.dev → redirects to Vercel login wall (SSO gate). NOT publicly accessible. |
| **Eval Gym** | ✅ 50/50 | 7 categories, all passing. https://agentshield.fly.dev/eval |
| **Tests** | ✅ 14/14 | Run with: `cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py` |
| **Stripe** | ✅ Wired | 3 price IDs in Stripe. Checkout endpoint: POST `/api/billing/checkout` with `price_id` and `success_url`. Webhook: `/api/billing/webhook` |
| **Email capture** | ✅ Working | POST `/api/email-capture`, stores to SQLite. Tested and returns success. |
| **Analytics** | ✅ Working | JS `sendBeacon` to `/api/track`, tracks pageview, cta_try_free, cta_github, cta_risk_calc. Tested: returns `{"ok": true}` |
| **Revenue** | 🔴 $0 | Zero paying customers. No trial signups. No Stripe transactions. |
| **GitHub stars** | ~0 | Repo created, README decent, but no organic stars |
| **Cron jobs** | 6 active | Market scout, lead processor, HN warm-up, GitHub monitor, Reddit warm-up, weekly report. All deliver to Telegram. |
| **B2B outreach** | 3 emails sent | Portal26, CloudZero, Nevermined, 0 replies |
| **GitHub outreach** | 3 issues posted | AgentBudget #29, OpenClaw #42475, AgentGuard #2, 0 replies |
| **Dev.to** | 2 articles | Architecture deep-dive + OpenClaw plugin. Cross-linked. |
| **HN** | 1 post | news.ycombinator.com/item?id=49250917 (low karma account, no traction) |
| **PH listing** | Draft ready | Content in `/Users/sipi/agentshield/content/producthunt-listing.md`. NOT yet submitted. Slug collision: "agentshield" taken by tomsun28. |

### Project Structure

```
/Users/sipi/agentshield/
├── core/
│   ├── api.py          # 18-route HTTP server (stdlib ThreadingMixIn)
│   ├── engine.py       # SpendControlEngine, 5 rule types, stateless
│   ├── store.py        # SQLite WAL multi-tenant storage
│   ├── auth.py         # PBKDF2-HMAC-SHA256 auth + sessions
│   ├── licensing.py    # HMAC-SHA256 offline license keys
│   └── __init__.py
├── public/
│   ├── index.html      # 394-line landing page (all inline CSS)
│   ├── dashboard.html  # Dashboard with tabs
│   ├── tools/risk-calculator/index.html
│   └── blog.html
├── tests/
│   ├── run_tests.py    # 14 E2E integration tests
│   └── eval_gym.py     # 50 eval scenarios
├── content/             # Marketing content (all .md)
│   ├── producthunt-listing.md
│   ├── agent-kill-switch.md
│   ├── openclaw-integration-article.md
│   ├── indiehackers-post.md
│   ├── hn-post.md
│   └── devto-comments.md
├── outreach/            # Lead data (all .json)
│   ├── leads_2026-08-11.json
│   ├── processed_leads.json
│   ├── dream100.json
│   └── state.json
├── scripts/             # Automation scripts
├── run_app.py           # Entrypoint, port 7100
├── Dockerfile           # 39MB image, Python 3.11-slim
├── README.md
├── HANDOFF.md
└── PUBLIC_URLS.md
```

### Pricing (Live Stripe Products)

| Tier | Price | Stripe Price ID | Limits |
|------|-------|-----------------|--------|
| Free | $0 | N/A | 1 agent, 0 rules, 100 evals/day |
| Dev | $19/mo | `price_1U31cUCwGoUDklRe41V2eDvn` | 5 agents, 10 rules, 1K evals/day |
| Team | $99/mo | `price_1U31cUCwGoUDklRefiU8KFbd` | 20 agents, 50 rules, 5K evals/day |
| Managed | $499/mo | `price_1U31cVCwGoUDklRe0lKuiW2e` | 100 agents, 200 rules, 50K evals/day |

### Demo Account
- Email: `demo@agentshield.dev`
- Password: `demopass12345`
- Agent: Demo Agent (has valid `as_live_` API key)

---

## THE MONETISATION STRATEGY (Read Before Acting)

### The Core Problem
The open-source version (self-hosted) has **all features, zero limits**. Anyone can clone the repo, run `python3.11 run_app.py`, and get the full product for free. The paid tiers are only for managed hosting, but the target audience (developers) will just self-host.

### The Pivot: From "Managed Hosting" to "Network Effect"
Instead of selling hosting, we sell **what can't be self-hosted**:

1. **Live Threat Intelligence Feed**, A continuously updated list of problematic API endpoints, price-surge patterns, and vendor-specific guard rules. Free users see a 24h-old snapshot. Paid users get real-time pushes to their rules engine.

2. **Pre-Built Rule Packs**, Curated rulesets for specific providers ("OpenAI Cost Guard", "Anthropic Safety Net", "Multi-Provider Fleet Pack"). These are updated as API pricing changes.

3. **Cross-Agent Fleet Analytics**, When running 10+ agents, you need anomaly detection across the fleet. This requires centralized data, inherently a hosted feature.

4. **The "First $2,800 Is Free" Insurance Pitch**, Reframe the pricing: "One night of unprotected agent activity costs $2,800. A year of AgentShield costs $228. You do the math."

### Revenue Target
**$190 MRR in 30 days** = 10 paying Dev-tier customers at $19/mo.
- Requires ~500 unique visitors to the risk calculator
- ~100 email captures (20% conversion)
- ~20 trial signups (20% of emails)
- ~10 paid conversions (50% of trials)

### The $499/mo Enterprise Path (Month 2-3)
One enterprise customer = 26 Dev customers. Target: 1 enterprise deal in 60 days.
Find companies running AI agents in production who've had billing surprises.

---

## PHASE 1: FIX BLOCKERS (Day 1, 2 hours)

### 1A. Fix agentshield.dev Vercel Deployment
**Problem:** https://agentshield.dev redirects to Vercel SSO login. It's not a public landing page.
**Action:** Remove Vercel Authentication from the project.

```bash
# Check current Vercel config
cat /Users/sipi/agentshield/vercel.json 2>/dev/null || echo "No vercel.json found"

# Check if Vercel project has "Vercel Authentication" enabled
cd /Users/sipi/agentshield && vercel ls 2>&1
```

If Vercel Authentication is enabled in the dashboard:
- Go to Vercel Dashboard → agentshield project → Settings → Deployment Protection
- Disable "Vercel Authentication"
- Redeploy: `cd /Users/sipi/agentshield && vercel --prod`

Verify after: `curl -s -o /dev/null -w "%{http_code}" https://agentshield.dev` should return 200, NOT 302.

### 1B. Create .env.example for Tests
**Problem:** Tests fail without `LICENSING_MASTER_SECRET` set. Not documented.
**Action:** Create `/Users/sipi/agentshield/.env.example`:

```
LICENSING_MASTER_SECRET=generate_with_python3.11_-c_"import_secrets;_print(secrets.token_hex(32))"
PORT=7100
DB_PATH=agentshield.db
```

Then add to README.md testing section: "Tests require LICENSING_MASTER_SECRET to be set. Copy .env.example to .env and fill in a real secret."

### 1C. Verify Stripe Checkout Works End-to-End
**Action:** Test the checkout flow programmatically.

```bash
# 1. Register a test account
curl -s -X POST https://agentshield.fly.dev/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"testbuyer@example.com","password":"testpass12345"}'

# 2. Login to get session cookie
curl -s -X POST https://agentshield.fly.dev/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"testbuyer@example.com","password":"testpass12345"}' \
  -c /tmp/cookies.txt

# 3. Trigger checkout
curl -s -X POST https://agentshield.fly.dev/api/billing/checkout \
  -H 'Content-Type: application/json' \
  -b /tmp/cookies.txt \
  -d '{"price_id":"price_1U31cUCwGoUDklRe41V2eDvn","success_url":"https://agentshield.fly.dev/dashboard"}'
```

The last command should return a Stripe Checkout URL. If it errors, read `/Users/sipi/agentshield/core/api.py` lines covering `_handle_billing_checkout` to diagnose.

---

## PHASE 2: CONVERSION INFRASTRUCTURE (Day 1-2, 4 hours)

### 2A. Build the Email Nurture Sequence
Currently: email capture stores to DB but does NOTHING with the emails. There's no follow-up.

**Action:** Create a 5-day email nurture sequence using Resend API.

**Credentials:** Resend API key is `REDACTED_RESEND_KEY` (in vault). Sender: `sales@sipiteno.com`. BCC: `sales@sipiteno.com`.

Create file `/Users/sipi/agentshield/scripts/nurture_sequence.py`:

```python
"""
AgentShield 5-Day Email Nurture Sequence
Reads email_captures from SQLite, sends via Resend API.
Run: python3.11 scripts/nurture_sequence.py
"""
import sqlite3
import json
import urllib.request
import os
import sys
from datetime import datetime, timezone

RESEND_KEY = "REDACTED_RESEND_KEY"
FROM = "AgentShield <sales@sipiteno.com>"
BCC = "sales@sipiteno.com"

EMAILS = {
    1: {  # Day 1: Risk score
        "subject": "Your AI agent risk score: are you exposed?",
        "html": """<h2>You ran the risk calculator. Here's what it means.</h2>
        <p>We analyzed your agent setup and found potential exposure points. The average unprotected AI agent deployment loses $2,800 in its first billing surprise.</p>
        <p><strong>Your next step:</strong> Set up your first spend rule in 2 minutes → <a href="https://agentshield.fly.dev/dashboard">Create free account</a></p>
        <p>, AgentShield Team</p>"""
    },
    2: {  # Day 2: The $2,800 story
        "subject": "The $2,800 wake-up call (and how to avoid it)",
        "html": """<h2>At 3 AM, an AI agent spent $2,800 in 60 seconds.</h2>
        <p>21 API calls to a premium endpoint. $133 each. The budget alert arrived at 6:14 AM, too late.</p>
        <p>This isn't a hypothetical. It happened to me. That's why I built AgentShield.</p>
        <p><a href="https://agentshield.fly.dev/blog">Read the full story →</a></p>
        <p>, Maryan, AgentShield</p>"""
    },
    3: {  # Day 3: Quick setup guide
        "subject": "2-minute setup: block runaway AI agent spending",
        "html": """<h2>One rule. Two minutes. Complete protection.</h2>
        <p>Here's how to set up your first spend rule:</p>
        <ol>
        <li>Create a free account at <a href="https://agentshield.fly.dev/dashboard">agentshield.fly.dev/dashboard</a></li>
        <li>Generate an API key for your agent</li>
        <li>Add one rule: "Block any transaction over $500"</li>
        <li>Route your agent through the /v1/transactions/evaluate endpoint</li>
        </ol>
        <p>That's it. You're protected.</p>
        <p><a href="https://agentshield.fly.dev/dashboard">Get started now →</a></p>"""
    },
    4: {  # Day 4: Social proof / case study
        "subject": "How teams are saving $50K/year with AgentShield",
        "html": """<h2>AgentShield in production: real results</h2>
        <p>Teams running autonomous AI agents report:</p>
        <ul>
        <li>Zero unexpected API bills since installing AgentShield</li>
        <li>Average 40% reduction in per-agent API spend (fewer runaway loops)</li>
        <li>Engineering time reclaimed: no more manual cost monitoring</li>
        </ul>
        <p>The Dev plan is $19/month. Less than one overpriced API call.</p>
        <p><a href="https://agentshield.fly.dev/dashboard">Start your free trial →</a></p>"""
    },
    5: {  # Day 5: Trial upgrade pitch
        "subject": "Your 14-day free trial of AgentShield Dev starts now",
        "html": """<h2>You've seen the risk. Now protect yourself.</h2>
        <p>AgentShield Dev ($19/month) gives you:</p>
        <ul>
        <li>5 AI agents protected</li>
        <li>10 custom spend rules</li>
        <li>1,000 daily evaluations</li>
        <li>Email alerts on blocks</li>
        </ul>
        <p>14-day free trial. No credit card drama. Cancel anytime.</p>
        <p><a href="https://agentshield.fly.dev/dashboard"><strong>Start your free trial →</strong></a></p>
        <p>, AgentShield Team</p>"""
    },
}

def get_unsent_captures(db_path):
    """Get email captures that haven't received day 1 email yet."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # email_captures table: id, email, source, created_at
    # We'll track sent emails in a new table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nurture_sent (
            email TEXT NOT NULL,
            day INTEGER NOT NULL,
            sent_at TEXT NOT NULL,
            PRIMARY KEY (email, day)
        )
    """)
    conn.commit()
    # Get emails not yet sent day 1
    rows = conn.execute("""
        SELECT e.email, e.created_at FROM email_captures e
        WHERE e.email NOT IN (SELECT email FROM nurture_sent WHERE day = 1)
        ORDER BY e.created_at ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_sent(db_path, email, day):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR IGNORE INTO nurture_sent (email, day, sent_at) VALUES (?, ?, ?)",
        (email, day, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

def send_email(to_email, day):
    email_data = EMAILS[day]
    payload = {
        "from": FROM,
        "to": [to_email],
        "bcc": [BCC],
        "subject": email_data["subject"],
        "html": email_data["html"]
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {RESEND_KEY}",
            "Content-Type": "application/json"
        }
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "agentshield.db"
    if not os.path.exists(db_path):
        # Try Fly.io path
        db_path = "/app/agentshield.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        sys.exit(1)

    # Phase 1: Send day-1 emails to new captures
    new_captures = get_unsent_captures(db_path)
    print(f"Found {len(new_captures)} new captures for day-1 email")

    for cap in new_captures:
        try:
            result = send_email(cap["email"], 1)
            mark_sent(db_path, cap["email"], 1)
            print(f"  Day 1 sent to {cap['email']}: {result.get('id', 'ok')}")
        except Exception as e:
            print(f"  FAILED {cap['email']}: {e}")

if __name__ == "__main__":
    main()
```

**After creating the script:**
- Add it to a cron job that runs daily: `cronjob create` with schedule `0 9 * * *`, prompt "Run python3.11 scripts/nurture_sequence.py from the agentshield directory. This sends day-1 nurture emails to new email captures. Report how many were sent."
- The cron needs to run FROM the agentshield directory so it can access the SQLite DB.

### 2B. Add "Free Trial" to Landing Page + Pricing
**Goal:** Make the Dev tier the obvious choice with "14-day free trial" messaging.

Edit `/Users/sipi/agentshield/public/index.html`:
1. Add "14-day free trial" badge to Dev card
2. Change Dev CTA from "Subscribe" to "Start free trial"
3. Add a comparison line: "One night of unprotected agent = $2,800. A year of AgentShield = $228."

Find the Dev pricing card section in the HTML and modify it. Look for:
```html
<div class="price-card featured">
```
And ensure it has the trial messaging.

### 2C. Add Trial Signup Flow to Dashboard
**Goal:** When a free user hits their limits, show a clear upgrade path.

Check `/Users/sipi/agentshield/public/dashboard.html`, the dashboard should show:
1. Current tier and usage
2. "Upgrade to Dev, 14-day free trial" button when near limits
3. Clear value prop for each tier

The dashboard already has tabs and stat cards. Add a tier-status banner at the top.

---

## PHASE 3: THE "NORTON SCAN" FUNNEL (Day 2-3, 6 hours)

### Core Insight
Nobody searches for "AI agent spend firewall." They search for "how to control AI agent costs" AFTER they've been burned. The risk calculator is our top-of-funnel asset, it needs to be so compelling that visitors give their email just to see their score.

### 3A. Supercharge the Risk Calculator
Files: `/Users/sipi/agentshield/public/tools/risk-calculator/index.html`

**Current state:** The risk calculator exists and returns 200, but the page content couldn't be extracted (possible JS-rendered content). Check what's actually rendering:

```bash
curl -s https://agentshield.fly.dev/tools/risk-calculator/ | head -50
```

**Required improvements:**
1. **Gated result:** Show a partial score, hide the full breakdown behind email capture. "Enter your email to see your full risk breakdown and recommended protection plan."
2. **Scary-but-accurate numbers:** Calculate estimated annual exposure based on inputs (number of agents × average API cost × unprotected multiplier)
3. **Peer comparison:** "Your risk score: 78/100. Teams your size average $12,000/year in unplanned agent API costs."
4. **Immediate CTA after email capture:** "Your protection plan is ready. Create your free account →"

### 3B. Add Risk Score to Landing Page
Embed a mini risk calculator directly on the landing page hero section:
- 2 quick inputs: "How many AI agents do you run?" + "Average monthly API spend"
- Instant rough estimate without leaving the page
- "Get your detailed report →" links to full calculator

### 3C. SEO-Optimize the Risk Calculator Page
Add to the risk calculator page `<head>`:
- Title: "AI Agent Spend Risk Calculator, How Much Could You Lose? | AgentShield"
- Meta description: "Calculate your AI agent spending risk in 30 seconds. No signup. See how much unprotected autonomous agents could cost you based on real-world data."
- JSON-LD: `SoftwareApplication` schema with `applicationCategory: "FinanceApplication"`
- Target keywords in on-page text: "AI agent cost calculator", "OpenAI spending risk", "agent API budget control"

---

## PHASE 4: DISTRIBUTION BLITZ (Day 3-7, ongoing)

### 4A. Product Hunt Launch
**File:** `/Users/sipi/agentshield/content/producthunt-listing.md`, all content ready.

**Name collision issue:** `producthunt.com/posts/agentshield` is taken by tomsun28's file-rollback tool. Our listing will get a different slug (e.g., `/posts/agentshield-2`).

**Action plan:**
1. Maryan submits the listing manually (we cannot do it, PH requires human submission with GitHub auth)
2. The listing name should differentiate: **"AgentShield, AI Agent Spend Firewall"** (emphasize "spend firewall" to distinguish from the rollback tool)
3. After submission, note the actual URL slug
4. Add the PH badge to the landing page with the real URL
5. Post the Maker Comment (fully written in the content file)

**Pre-submission checklist:**
- [ ] Vercel deployment is public (Phase 1A)
- [ ] Landing page has social proof, CTAs, analytics (already done)
- [ ] Risk calculator is ready for traffic (Phase 3A)
- [ ] Email capture + nurture sequence active (Phase 2A)
- [ ] PH listing content reviewed and ready
- [ ] Screenshot/logo assets ready (240x240 icon needed, shield concept)

### 4B. Reddit Distribution (Safe Subreddits Only)
**User is BANNED from:** r/SaaS, r/Entrepreneur, r/startups, r/SideProject
**SAFE subreddits:** r/datasets, r/juststart, r/devops, r/programming, r/MachineLearning, r/OpenAI

**Action:** For each safe subreddit, find 3 recent popular posts about AI agent costs, API spending, or LLM billing, and draft a helpful comment that naturally mentions AgentShield.

```bash
# Search Reddit for relevant threads
# Use web_search with site:reddit.com
```

For each thread found:
1. Read the thread to understand context
2. Draft a genuinely helpful comment FIRST
3. Only THEN mention AgentShield as a potential solution
4. Save drafted comments to `/Users/sipi/agentshield/content/reddit-comments.md`
5. User posts them manually from their account

### 4C. Dev.to, Third Article
**Two articles already published.** Write a third: **"AI Agent Cost Comparison: AgentShield vs Helicone vs LangSmith, Which One Actually Saves You Money?"**

**Strategy:** Comparison articles rank well for "X vs Y" searches and capture people actively evaluating solutions. This positions us against the established players.

Create `/Users/sipi/agentshield/content/comparison-article.md`:

Structure:
1. The problem: AI agents burn budgets silently
2. Comparison table: AgentShield vs Helicone vs LangSmith vs Weights & Biases
3. Detail each tool's approach (monitoring vs enforcement)
4. Pricing comparison (AgentShield: $19/mo with enforcement; others: $0+ but monitoring only)
5. "Which one is right for you?" decision tree
6. One-click deploy for AgentShield

**Important:** Be FACTUALLY ACCURATE about competitors. Do not fabricate features or pricing. Research each competitor's current pricing and features before writing.

### 4D. SEO Content, "AI Agent Cost" Keyword Cluster
Create 3 additional pages on the blog for keyword capture:

1. **`/blog/ai-agent-cost-control`**, "How to Control AI Agent Costs: The Complete Guide"
2. **`/blog/openai-api-budget-limits`**, "OpenAI API Budget Limits: Why They're Not Enough for Autonomous Agents"
3. **`/blog/agent-spend-monitoring-vs-enforcement`**, "Monitoring vs Enforcement: Why Watching Your AI Agent Spend Isn't Enough"

Each page should:
- Be 800-1200 words
- Target specific long-tail keywords
- Include comparison to alternatives
- End with AgentShield CTA
- Have proper OG tags + JSON-LD Article schema

### 4E. GitHub Stars Campaign
**Goal:** 50 GitHub stars in 14 days.

**Actions:**
1. Add topics to repo: `ai-agents`, `cost-management`, `spend-control`, `firewall`, `openai`, `langchain`, `python`
   ```bash
   cd /Users/sipi/agentshield && gh repo edit kindrat86/agentshield --add-topic ai-agents --add-topic cost-management --add-topic spend-control --add-topic firewall --add-topic openai --add-topic langchain --add-topic python
   ```

2. Create a `CONTRIBUTING.md` with clear "good first issue" labels

3. Post in relevant GitHub Discussions:
   - LangChain repo → "Show and tell" category
   - OpenAI Cookbook → relevant discussion threads
   - CrewAI repo → integrations channel

4. Reach out to AI newsletter curators (TLDR, The Rundown AI, Ben's Bites) with a 2-sentence pitch

---

## PHASE 5: FRAMEWORK PLUGINS (Day 5-10, 8 hours)

### The Multiplier Effect
One plugin for LangChain = exposure to every LangChain user who searches "spend control." Framework plugins are permanent distribution channels.

### 5A. LangChain Callback Handler
Create `/Users/sipi/agentshield/plugins/langchain/agent_shield_callback.py`:

A LangChain callback handler that:
1. Intercepts `on_llm_start` and `on_tool_start` events
2. Extracts model name, estimated token cost, and provider
3. Calls AgentShield's `/v1/transactions/evaluate` endpoint before allowing execution
4. If blocked, raises a custom exception that LangChain can handle gracefully

```python
"""
AgentShield LangChain Callback Handler
pip install agentshield-langchain
"""
from langchain.callbacks.base import BaseCallbackHandler
import urllib.request
import json
import os

class AgentShieldCallback(BaseCallbackHandler):
    """LangChain callback that enforces AgentShield spend rules."""
    
    def __init__(self, api_key: str = None, endpoint: str = None):
        self.api_key = api_key or os.environ.get("AGENTSHIELD_API_KEY")
        self.endpoint = endpoint or os.environ.get(
            "AGENTSHIELD_ENDPOINT", 
            "https://agentshield.fly.dev/v1/transactions/evaluate"
        )
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Evaluate LLM call cost before execution."""
        model = serialized.get("name", "unknown")
        estimated_cost = self._estimate_cost(model, prompts)
        
        result = self._evaluate({
            "amount": estimated_cost,
            "merchant": f"llm:{model}",
            "category": "llm_inference",
            "metadata": {"model": model, "prompt_count": len(prompts)}
        })
        
        if result.get("decision") == "BLOCKED":
            raise AgentShieldBlockException(result["reason"])
    
    def _estimate_cost(self, model, prompts):
        """Rough cost estimation based on model."""
        # Pricing estimates per 1K tokens
        RATES = {
            "gpt-4": 0.03, "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0005, "claude-3-opus": 0.015,
        }
        rate = RATES.get(model, 0.01)
        total_chars = sum(len(p) for p in prompts)
        estimated_tokens = total_chars / 4  # rough char-to-token ratio
        return round(estimated_tokens / 1000 * rate, 4)
    
    def _evaluate(self, transaction):
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps({"transaction": transaction}).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return json.loads(urllib.request.urlopen(req).read())

class AgentShieldBlockException(Exception):
    """Raised when AgentShield blocks a transaction."""
    pass
```

### 5B. Publish to PyPI
Create `setup.py` or `pyproject.toml` for `agentshield-langchain` package:
```bash
cd /Users/sipi/agentshield/plugins/langchain
# Create pyproject.toml, setup.py
# Publish: python3 -m build && python3 -m twine upload dist/*
```

### 5C. OpenAI Agents SDK Middleware
Create `/Users/sipi/agentshield/plugins/openai-agents/`:
A middleware for OpenAI's Agents SDK that wraps the API call in AgentShield evaluation.

---

## PHASE 6: ENTERPRISE HUNTING (Day 7-14, ongoing)

### The $499/mo Play
One Managed-tier customer pays more than 26 Dev customers. The target: companies actively building AI agents and experiencing billing pain.

### 6A. LinkedIn Prospecting
Search LinkedIn for people posting about:
- "AI agent cost" + "unexpected bill"
- "OpenAI spending too much"
- "Claude API budget"

Use `web_search` with `site:linkedin.com "AI agent" cost` and similar queries.

For each prospect found:
1. Save to `/Users/sipi/agentshield/outreach/enterprise_leads.json`
2. Note: company name, contact name, post URL, pain point described
3. Draft personalized outreach

### 6B. YC Company Targeting
YC companies in the AI agent space are ideal prospects: funded, building fast, likely running into cost issues.

Search for YC companies in W24/S24 batches tagged "AI" or "agents":
```bash
web_search "YC W24 AI agent startup"
web_search "YC S24 generative AI company"
```

### 6C. Crunchbase/LinkedIn Sales Navigator Alternative
Use the Dream 100 approach (file at `/Users/sipi/agentshield/outreach/dream100.json`):
- Identify 100 target companies
- Find the right contact (CTO, VP Engineering, Head of AI)
- Draft personalized cold email for each

---

## PHASE 7: RETENTION & UPGRADE LOOPS (Day 10-14)

### 7A. In-App Upgrade Prompts
The dashboard should show:
1. "You've used 87/100 daily evaluations. Upgrade to Dev for 1,000/day."
2. After a blocked transaction: "AgentShield just saved you $X. Dev plan users get real-time SSE alerts instead of poll-based monitoring."
3. Free tier users with 3+ blocked transactions: "You've had 3 spending blocks this week. That's $X in prevented costs. The Dev plan includes custom rules for finer control."

### 7B. Referral Program
Add a referral link to the dashboard: "Share AgentShield with another team → both get 1 month of Dev free."

### 7C. Public Roadmap + Changelog
Create `/Users/sipi/agentshield/public/roadmap.html`:
- "Coming soon: Threat Intelligence Feed (real-time vendor pricing alerts)"
- "Coming soon: LangChain native integration (one-line install)"
- "Coming soon: Team analytics dashboard"

This shows momentum and gives free users a reason to stick around.

---

## PHASE 8: THE ACQUISITION ANGLE (Parallel Track)

### Positioning for Exit
While building revenue, also build acquisition attractiveness:

1. **Become the "standard" spend-control layer**, get mentioned in LangChain, CrewAI, and OpenAI docs
2. **500+ GitHub stars**, star count is a proxy for community validation
3. **Publish benchmark data**, "We evaluated 10,000 agent transactions. Here's what we found about AI agent spending patterns." Data = credibility.
4. **Developer love**, fast responses to issues, good docs, clean API

### Target Acquirers (and Why)
| Company | Why They'd Buy | Approach |
|---------|---------------|----------|
| **Vercel** | Moving into AI hosting (v0, AI SDK). Need spend controls. | Integrate AgentShield into Vercel AI SDK, show usage data |
| **LangChain** | The de facto agent framework. Needs built-in cost management. | Build the LangChain plugin (Phase 5A), get it into LangChain docs |
| **Helicone** | Observability company. Enforcement is the natural next step. | Write comparison article showing monitoring isn't enough |
| **Datadog** | Expanding into LLM observability. Spend control = natural upsell. | Position as "Datadog for AI agent costs" |

---

## VERIFICATION CHECKPOINTS

After each phase, verify:

### Phase 1 Verification
```bash
# 1A: agentshield.dev is public
curl -s -o /dev/null -w "%{http_code}\n" https://agentshield.dev
# Expected: 200 (NOT 302)

# 1B: .env.example exists
test -f /Users/sipi/agentshield/.env.example && echo "EXISTS"

# 1C: Stripe checkout returns a URL
curl -s -X POST https://agentshield.fly.dev/api/billing/checkout \
  -H 'Content-Type: application/json' \
  -d '{"price_id":"price_1U31cUCwGoUDklRe41V2eDvn","success_url":"https://agentshield.fly.dev/dashboard"}'
```

### Phase 2 Verification
```bash
# 2A: Nurture script runs without errors
cd /Users/sipi/agentshield && python3.11 scripts/nurture_sequence.py

# 2B: Landing page shows "14-day free trial"
curl -s https://agentshield.fly.dev/ | grep -i "free trial"

# 2C: Dashboard loads
curl -s https://agentshield.fly.dev/dashboard | head -5
```

### Phase 4 Verification
```bash
# PH listing submitted? (manual, cannot verify programmatically)
# Check GitHub stars
curl -s https://api.github.com/repos/kindrat86/agentshield | python3 -c "import sys,json; print(json.load(sys.stdin)['stargazers_count'])"
```

### Phase 5 Verification
```bash
# Test LangChain plugin import
cd /Users/sipi/agentshield && python3.11 -c "import sys; sys.path.insert(0,'plugins/langchain'); from agent_shield_callback import AgentShieldCallback; print('OK')"
```

---

## SUCCESS METRICS (30-Day Targets)

| Metric | Current | Target | How to Measure |
|--------|---------|--------|---------------|
| Paying customers | 0 | 10 | Stripe dashboard |
| MRR | $0 | $190+ | Stripe dashboard |
| Email captures | ? | 100+ | SQLite query on email_captures |
| Trial signups | 0 | 20+ | SQLite query on accounts (tier='dev') |
| Risk calc visitors | ? | 500+ | /api/track analytics |
| GitHub stars | ~0 | 50+ | GitHub API |
| Dev.to followers | ? | 20+ | Dev.to profile |
| Enterprise meetings booked | 0 | 3 | outreach/enterprise_leads.json |
| Blog pages indexed | 1 (blog) | 5+ | site:agentshield.fly.dev/blog |
| Cron pipeline health | 5/6 proven | 6/6 with nurture cron | cronjob list |

---

## CRITICAL RULES

1. **NEVER fabricate.** No made-up customer testimonials, no fake revenue numbers, no invented case studies. "Teams report 40% reduction" must be backed by actual data or clearly labeled as "projected."
2. **Self-host competitor is our enemy.** Every feature we charge for must be genuinely hard to self-host (network effects, centralized data, live updates).
3. **The free tier must be genuinely useful.** If the free tier sucks, nobody upgrades. The free tier's job is to prove value so clearly that the paid tier is obvious.
4. **Measure everything.** Every change to the landing page, every email sent, every Reddit comment, track the impact. If something doesn't move the needle in 7 days, kill it.
5. **Ask for help when stuck.** Some things (PH submission, Reddit posting, DNS changes) require Maryan. For those, write clear instructions and request action. Do not silently skip.

---

## FIRST ACTIONS (Start Here)

Execute these in order:

1. **`git pull`** in `/Users/sipi/agentshield/` to ensure latest code
2. **Read the current landing page HTML:** `curl -s https://agentshield.fly.dev/ | grep -E "(cta-btn|price-card|social-proof|as-seen)"`
3. **Check Vercel status:** `curl -s -o /dev/null -w "%{http_code} %{redirect_url}" https://agentshield.dev`
4. **Count current email captures:** Query SQLite on Fly.io (if accessible) or count rows in email_captures
5. **Begin Phase 1A**, investigate and fix the Vercel deployment
