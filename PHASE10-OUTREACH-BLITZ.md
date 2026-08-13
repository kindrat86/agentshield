# MISSION: Generate AgentShield's First Revenue, No Infrastructure, Pure Outreach

## ⚠️ READ THIS FIRST, IT CHANGES EVERYTHING

You are NOT here to build infrastructure. You are NOT here to debug cron jobs. You are NOT here to fix memory or clean up prompt files.

You are here to do ONE thing: **find people who just got burned by AI costs and show them AgentShield.**

The product works (50/50 eval, 14/14 tests, health OK). The landing page converts ("14-Day Free Trial" CTAs, comparison pages, risk calculator). The Stripe checkout is wired. Eight cron jobs run daily. Six GitHub outreach posts are live. **None of this has produced a single paying customer.**

The gap is not technical. The gap is **human engagement at the point of pain.**

---

## THE ONLY METRIC THAT MATTERS

How many high-quality, contextual comments did you post today in threads where a real developer is actively complaining about AI API costs?

Target: **10+ comments per session.** No other metric counts.

---

## RULE ZERO: YOU CANNOT FABRICATE

Every claim must be backed by visible tool output in your response. If `gh` returns a comment URL, include it. If a web search returns results, show them. If a page was posted on, show the HTTP status or the URL. Never claim "posted" without a URL. Never claim "searched" without results. Never invent cron IDs, comment IDs, or domain statuses.

---

## WHAT EXISTS (don't rebuild this)

- **Product:** https://agentshield.fly.dev, landing page, dashboard, blog, risk calculator
- **Comparison pages:** `/comparisons/helicone`, `/comparisons/langsmith` (both live, 200 OK)
- **GitHub:** https://github.com/kindrat86/agentshield (MIT, 50 stars target)
- **Stripe:** Dev $19/mo, Team $99/mo, Managed $499/mo, checkout endpoint live
- **Email capture:** POST `/api/email-capture` → SQLite → nurture cron sends 5-day sequence via Resend
- **Credentials:** `gh` CLI authenticated as `kindrat86`. Resend key in `~/.hermes/.env` as `RESEND_API_KEY`.
- **Content files:** `/Users/sipi/agentshield/content/outreach-comments-2026-08-11.md` has 3 draft comments. `/Users/sipi/agentshield/content/producthunt-listing.md` has PH listing content.

---

## PHASE 1: FIND PEOPLE IN PAIN (15 min, repeatable loop)

Search for developers actively complaining about AI costs RIGHT NOW. Post in threads that are OPEN and ACTIVE (created or commented on in the last 30 days).

### 1A. GitHub Issue Search (highest ROI)

Run these searches. For each result that is an OPEN issue with real cost complaints, craft and post a contextual comment offering AgentShield as a solution.

```bash
# Search 1: Direct cost complaints
gh search issues "AI agent cost" "API bill" "spending too much" --limit 10 --state open --sort updated

# Search 2: Runaway loops
gh search issues "agent loop" "infinite" "cost" OR "expensive" --limit 10 --state open --sort updated

# Search 3: Rate limit / retry storm
gh search issues "rate limit" "retry" "expensive" "agent" --limit 10 --state open --sort updated

# Search 4: Token / billing surprises  
gh search issues "token" "cost" "unexpected" OR "surprise" "bill" --limit 10 --state open --sort updated

# Search 5: Budget / spend control
gh search issues "budget" "spend" "control" OR "limit" "agent" --limit 10 --state open --sort updated
```

For each qualifying issue:
1. **Read the full issue** to understand the EXACT pain point
2. **Check if someone already posted an AgentShield comment**, don't duplicate
3. **Craft a reply that:**
   - Acknowledges their specific problem (quote their words)
   - Explains WHY it happens (agents lack budget awareness)
   - Mentions AgentShield as a solution with a brief description
   - Links to the risk calculator: https://agentshield.fly.dev/tools/risk-calculator/
   - Links to the GitHub repo: https://github.com/kindrat86/agentshield
   - Disclosure: "I built this. MIT licensed. Free tier available."
4. **Post it:** `gh issue comment <url> --body-file /tmp/comment-N.md`
5. **Record the URL** of your posted comment

### 1B. GitHub Discussion Search

Discussions use the GraphQL API, not `gh issue comment`. Use `gh api graphql`:

```bash
# Search discussions
gh search discussions "AI cost" "expensive" "API" --limit 10

# To post on a discussion:
# 1. Get discussion node ID via GraphQL
# 2. Use addDiscussionComment mutation
```

### 1C. Web Search for Off-GitHub Pain

```bash
# Find cost complaints on other platforms
web_search "site:reddit.com AI agent API cost expensive 2026"
web_search "site:news.ycombinator.com AI agent spending bill"
web_search "\"AI agent\" \"cost\" OR \"spending\" \"problem\" OR \"complaint\" 2026"
web_search "site:dev.to AI agent cost expensive bill"
web_search "\"openai bill\" OR \"claude expensive\" OR \"runaway agent\" developer"
```

For results on platforms where you can post:
- **Hacker News:** Use the HN API if possible, or create draft comments for Maryan
- **Dev.to:** Use the REST API if authenticated, or draft comments
- **Reddit:** Genuinely blocked at network level, draft comments only
- **Other forums:** Draft comments with exact URLs

---

## PHASE 2: CRAFT PERFECT OUTREACH COMMENTS (continuous)

### The Template

Every comment must follow this structure:

```
[1-2 sentences acknowledging their specific problem, quoting their words]

This is a structural problem with autonomous AI agents: [one-sentence explanation of WHY this happens, agents don't know they're spending money].

We built AgentShield to solve exactly this: a per-transaction spend firewall that evaluates every API call against rules YOU set before it executes. [One specific rule that would have prevented THEIR scenario].

- <1ms evaluation overhead
- Pure Python 3.11 stdlib, zero dependencies
- Self-host in 60 seconds, or managed from $19/mo

Risk calculator (no signup, 30 seconds): https://agentshield.fly.dev/tools/risk-calculator/
GitHub: https://github.com/kindrat86/agentshield

Disclosure: I built it after an AI agent spent $2,800 in 60 seconds while I was asleep. MIT licensed.
```

### Anti-Patterns (DO NOT USE)
- "Great question!", fake enthusiasm
- "I think you'll find...", condescending
- "Our solution is...", corporate tone
- Multi-paragraph explanations, get to the point
- Generic copy-paste, every comment must reference specifics from their issue

---

## PHASE 3: FOLLOW-UP ON EXISTING OUTREACH (5 min)

Check if anyone replied to the 6 existing outreach posts:

```bash
# Check each issue for new comments since we posted
gh issue view https://github.com/NousResearch/hermes-agent/issues/21172 --comments 2>/dev/null | head -20
gh issue view https://github.com/openclaw/openclaw/issues/42475 --comments 2>/dev/null | head -20
gh issue view https://github.com/zeroclaw-labs/zeroclaw/issues/2269 --comments 2>/dev/null | head -20
gh issue view https://github.com/cinatra-ai/cinatra/issues/2580 --comments 2>/dev/null | head -20
gh issue view https://github.com/shakacode/agent-workflows/issues/393 --comments 2>/dev/null | head -20
```

If any have replies, respond promptly. A conversation is worth 100 one-off comments.

---

## PHASE 4: DNS, ONE ATTEMPT, THEN MOVE ON (10 min max)

The `agentshield.sipiteno.com` domain is still not resolving. This hurts credibility but is not a revenue blocker.

### 4A. Load skills
```
skill_view name="cloudflare-dns-operations"
skill_view name="macos-browser-driving"
```

### 4B. Try one Safari → Cloudflare session
```bash
open -a Safari "https://mail.google.com/mail/u/0/"
```
Wait 3 seconds. Capture: `computer_use action='capture' mode='som' app='Safari'`

**If Gmail loads showing mkondratyuk86@gmail.com inbox** → session active → proceed to Cloudflare:
```bash
open -a Safari "https://dash.cloudflare.com/"
```
Capture. Click sipiteno.com. Navigate to DNS → Records. Add:
- A: agentshield → 66.241.125.16 (proxy OFF, grey cloud)
- AAAA: agentshield → 2a09:8280:1::166:9212:0 (proxy OFF)

**If no Google session or Cloudflare shows login** → stop. Do not spend more time on this. Report: "DNS blocked, no active Cloudflare session in Safari. Requires Maryan to log into mkondratyuk86@gmail.com in Safari, then retry."

---

## PHASE 5: ATTEMPT PRODUCT HUNT SUBMISSION (15 min max)

### 5A. Read content
```bash
read_file path="/Users/sipi/agentshield/content/producthunt-listing.md"
```

### 5B. Navigate to PH
```bash
open -a Safari "https://www.producthunt.com/posts/new"
```
Capture.

### 5C. Fill fields via JavaScript injection
Per the `macos-browser-driving` skill Section 12, React forms accept native setter + dispatchEvent.

Fill ALL text fields first (name, tagline, website, GitHub, description, maker story, Twitter). Then attempt the tags.

### 5D. Upload logo
Generate 240x240 green PNG at `/tmp/agentshield-logo.png`, click upload area, type path in native file dialog via foreground keystrokes.

### 5E. Tags, 3 attempts then fall back
Attempt: set_value → JavaScript injection → foreground type. If all fail, mark PH as "blocked by autocomplete, needs Maryan to type 'Developer Tools' in tags field."

### 5F. If submitted
Capture confirmation page → record URL → add badge to index.html → fly deploy.

---

## PHASE 6: REDDIT, SAVE DRAFTS ONLY (5 min)

Reddit is network-blocked on this connection. DO NOT attempt to post. Instead:

```bash
# Run the spend radar to find fresh leads
cd /Users/sipi/agentshield && python3.11 scripts/spend_radar.py 2>&1 | head -100
```

Save any Reddit-suitable drafts to `/Users/sipi/agentshield/content/reddit-drafts-$(date +%Y%m%d).md`.

For each draft, include:
- Exact subreddit
- Exact post URL  
- The full comment text ready to copy-paste
- A note: "Posted on safe subreddit? (user is banned from r/SaaS, r/Entrepreneur, r/startups, r/SideProject)"

---

## PHASE 7: QUICK QUALITY CHECKS (5 min)

```bash
# Verify product is healthy
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval 2>&1 | python3 -c "import sys,json; print(json.load(sys.stdin)['passed'])" 2>/dev/null

# Check existing outreach
gh issue list --search "kindrat86" --state all --limit 10 2>/dev/null || echo "gh search limited"
```

---

## REPORT FORMAT

```
## Outreach Session Report, $(date +%Y-%m-%d)

### New Comments Posted Today
| # | Platform | Issue/Discussion | URL | Status |
|---|----------|------------------|-----|--------|
| 1 | GitHub | repo#issue | https://github.com/... | Posted |
| 2 | ... | ... | ... | ... |

### Existing Outreach, New Replies
| # | Original Post | New Reply? | Action |
|---|---------------|------------|--------|
| 1 | zeroclaw#2269 | Yes/No | Responded/Waiting |

### Leads Found (Not Yet Contacted)
| # | Platform | URL | Why Relevant |
|---|----------|-----|-------------|
| 1 | GitHub | ... | ... |

### DNS
- Safari session: [Active / Not active]
- Records added: [YES / NO]
- dig output: [raw]

### Product Hunt
- Submission status: [Submitted / Blocked by tags / Not attempted]
- PH URL: [URL if submitted]

### Reddit
- Drafts saved: [count] → /Users/sipi/agentshield/content/reddit-drafts-*.md

### Quality
- Health: [ok/error]
- Eval: [N]/50

### Top 3 Actions for Next Session
1. [Highest-ROI action]
2. [Second-highest]
3. [Third-highest]
```

---

## HARD RULES

1. **Post >10 comments per session.** This is the only KPI.
2. **Never mention cron.** No cleanup, no verification, no ID lists, no "checking cron state." The cron pipeline is running. Ignore it.
3. **Never edit memory.** No memory tool calls. No profile updates. Memory manipulation has burned 5 sessions.
4. **Never fabricate.** Show the URL of every posted comment. Show the raw output of every search.
5. **Accept browser walls gracefully.** If Cloudflare/PH login is blocked, say so and move on. Do not spend 10+ turns on a single form field.
6. **Every comment must reference specifics from the target thread.** Zero generic copy-paste.
