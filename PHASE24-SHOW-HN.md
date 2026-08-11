# MISSION: Post Show HN + 5 More B2B Emails + Reach Out to YC Startups

## ⚠️ YOUR 3 KPIS
1. **Post Show HN** — via Safari `do JavaScript` (HN is server-rendered HTML, no React)
2. **Send 5 more B2B emails** — to YC AI startups and agent platforms
3. **Post 1 more HN comment** — to build karma resilience

---

## RULE ZERO
Zero fabrication. Every claim backed by tool output. Never mention cron. Never touch memory. Sign all communications as "Maryan K." (NOT full surname).

---

## THE SAFARI JAVASCRIPT BREAKTHROUGH

In Phases 22-23, we discovered that **Safari's `do JavaScript` AppleScript command** is the universal solution for all browser automation:

- **HN comment posted** via `osascript -e 'tell application "Safari" to do JavaScript "..."'`
- **8 Twitter tweets posted** via `document.execCommand('insertText')` + button clicks
- **No browser automation tools needed** — no SOM captures, no cua_browser, no React wall

**This technique works on ANY server-rendered or React page in Safari.** Use it for ALL browser tasks in this session.

---

## TASK 1: POST SHOW HN (Priority #1)

### Why This Matters
Show HN is the #1 developer discovery channel. A good Show HN post can reach 5,000-50,000 developers in 24 hours. We have a fully written post at `content/show-hn-post.md`.

### 1A. Read the Show HN post
```bash
read_file path="/Users/sipi/agentshield/content/show-hn-post.md"
```

### 1B. Check HN karma
```bash
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Karma: {d.get(\"karma\", 0)}')
" 2>/dev/null
```

**If karma >= 2:** Proceed to post Show HN.
**If karma = 1:** HN may still allow Show HN posts from karma-1 accounts, but rate-limiting is aggressive. Attempt the post. If HN returns "rate limited" or requires more karma, proceed to Task 3 first (post another value comment), then retry.

### 1C. Navigate Safari to HN submit

```bash
open -a Safari "https://news.ycombinator.com/submit"
```
Wait 3 seconds.

### 1D. Post via Safari do JavaScript

HN's submit form is simple server-rendered HTML with `<input>` fields. This is MUCH easier than X.com's contenteditable div.

```bash
osascript -e 'tell application "Safari" to do JavaScript "
// Fill the title field
var titleInput = document.querySelector(\"input[name=title]\");
if (titleInput) {
    titleInput.value = \"Show HN: AgentShield – A firewall for AI agent spending (56 eval scenarios, pure stdlib)\";
}

// Fill the URL field (use fly.dev since it is most stable)
var urlInput = document.querySelector(\"input[name=url]\");
if (urlInput) {
    urlInput.value = \"https://agentshield.fly.dev\";
}

// If there is a text field (for text posts), leave it empty — this is a link post
titleInput ? \"Title set: \" + titleInput.value : \"Title field not found\";" in document 1' 2>&1
```

Wait 1 second, then submit:

```bash
osascript -e 'tell application "Safari" to do JavaScript "
// Submit the form
var form = document.querySelector(\"form\");
if (form) {
    form.submit();
    \"Form submitted\";
} else {
    \"Form not found\";
}" in document 1' 2>&1
```

Wait 3 seconds.

### 1E. Verify the post

```bash
# Check if we landed on the new post page or an error page
osascript -e 'tell application "Safari" to do JavaScript "document.title + \" | \" + document.body.innerText.substring(0, 200);" in document 1' 2>&1
```

If the page shows the new HN post (title visible, comments section) → **SUCCESS**.

If the page shows "Please confirm your submission" or a captcha → HN anti-spam triggered. Report honestly.

If the page shows "Rate limited" → wait. Do not retry immediately. Report and move to Task 2.

### 1F. Record the post URL

If successful, the URL should be `https://news.ycombinator.com/item?id=NEW_ID`. Capture this.

---

## TASK 2: SEND 5 MORE B2B PARTNERSHIP EMAILS (Priority #2)

### 2A. Find 5 new YC AI startups

We've already contacted: Helicone, LangChain, Braintrust, Portkey, AgentOps, LLMonitor, Peluza, Autoblocks, PromptLayer.

```bash
web_search "Y Combinator AI agent startup 2026 batch"
web_search "YC W26 AI agent framework"
web_search "YC S25 AI infrastructure startup agent"
```

For each result:
1. Find the company name, founder/CTO name, and contact email
2. Draft a personalized partnership/integration email

### 2B. Draft and send 5 emails

**Template for YC startups (partnership angle):**

```bash
curl -s -X POST "https://api.resend.com/emails" \
  -H "Authorization: Bearer REDACTED_RESEND_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "AgentShield <sales@sipiteno.com>",
    "to": ["RECIPIENT_EMAIL"],
    "bcc": ["sales@sipiteno.com"],
    "subject": "Spend-control enforcement for [Company] agents",
    "html": "<p>Hi [name],</p><p>Saw [Company] in the latest YC batch — great work on [specific product feature].</p><p>We built AgentShield, an open-source per-transaction spend firewall for AI agents. It sits between the agent and the API, evaluating every call against configurable rules in <1ms before it executes. Pure Python stdlib, zero dependencies.</p><p><code>pip install agentshield-spend</code></p><p>The 56-scenario eval gym covers 9 rule types including transaction limits, daily totals, velocity detection, session budgets, and cascade cost estimation.</p><p>Would [Company] be interested in integrating AgentShield as a built-in spend-control option? We can co-build the integration.</p><p>Eval gym: https://agentshield.fly.dev/eval<br>GitHub: https://github.com/kindrat86/agentshield</p><p>Maryan K.<br>AgentShield</p>"
  }'
```

Record each Resend message ID.

---

## TASK 3: POST 1 MORE HN COMMENT FOR KARMA (Priority #3)

### 3A. Find an active thread

```bash
# AI / LLM threads from the last 24 hours
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=AI+LLM+agent&tags=story&numericFilters=created_at_i>$(python3 -c 'import time; print(int(time.time()) - 86400)')" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for hit in d.get('hits', [])[:10]:
    print(f'{hit[\"objectID\"]:12} pts={hit.get(\"points\",0):3} comments={hit.get(\"num_comments\",0):3} {hit[\"title\"][:80]}')
" 2>/dev/null
```

### 3B. Read the top thread

```bash
curl -s "https://hn.algolia.com/api/v1/items/ITEM_ID" | python3 -c "
import sys, json
def show(item, depth=0):
    if depth > 1: return
    text = (item.get('text') or '')[:300]
    by = item.get('author', '?')
    pts = item.get('points', '?')
    print(f\"{'  '*depth}{by} ({pts}pt): {text}\")
    for c in (item.get('children') or [])[:3]:
        show(c, depth+1)
d = json.load(sys.stdin)
print(f'TITLE: {d.get(\"title\")}')
show(d)
" 2>/dev/null
```

### 3C. Draft and post a genuine comment

3-6 sentences. Real technical insight. **Zero AgentShield mentions.**

Post via Safari `do JavaScript` (proven method from Phases 22-23):

```bash
open -a Safari "https://news.ycombinator.com/item?id=ITEM_ID"
```

Wait 3 seconds.

```bash
osascript -e 'tell application "Safari" to do JavaScript "
// Find the comment textarea
var ta = document.querySelector(\"textarea[name=text]\");
if (ta) {
    ta.value = \"COMMENT TEXT HERE\";
    \"Textarea found and filled: \" + ta.value.length + \" chars\";
} else {
    \"Textarea not found\";
}" in document 1' 2>&1
```

Wait 1 second, then submit:

```bash
osascript -e 'tell application "Safari" to do JavaScript "
var form = document.querySelector(\"form[action=item]\");
if (form) {
    form.submit();
    \"Form submitted\";
} else {
    \"Form not found\";
}" in document 1' 2>&1
```

### 3D. Check karma
```bash
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "import sys,json; print(f'Karma: {json.load(sys.stdin).get(\"karma\",0)}')" 2>/dev/null
```

---

## TASK 4: CHECK ACTIVE GITHUB CONVERSATIONS (5 min)

```bash
for url in \
  "https://github.com/openclaw/openclaw/issues/42475" \
  "https://github.com/zeroclaw-labs/zeroclaw/issues/2269" \
  "https://github.com/langchain-ai/langchain/issues/31647" \
  "https://github.com/cinatra-ai/cinatra/issues/2580" \
  "https://github.com/shakacode/agent-workflows/issues/393"; do
  echo "=== $(basename $(dirname $url))/$(basename $url) ==="
  gh issue view "$url" --comments 2>&1 | tail -15
  echo ""
done
```

If anyone replied → respond. The audit page is a perfect follow-up: "If you want to see how these rules map to YOUR production data: https://agentshield.sipiteno.com/audit"

---

## TASK 5: VERIFY & COMMIT

```bash
# Product health (use the new domain!)
curl -s https://agentshield.sipiteno.com/health
curl -s https://agentshield.sipiteno.com/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# DNS
dig agentshield.sipiteno.com A +short

# HN karma
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "import sys,json; print(f'Karma: {json.load(sys.stdin).get(\"karma\",0)}')" 2>/dev/null

# Commit
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 24: Show HN posted, YC startup emails, HN karma building"
git log --oneline -3
```

---

## REPORT FORMAT

```
## Phase 24 — Mass Distribution Report

### Show HN
- Attempted: [YES / NO]
- Karma at time of post: [number]
- Post URL: [URL if successful]
- Error if any: [rate limited / captcha / success]

### B2B Emails
| # | Company | Email | Resend ID |
|---|---------|-------|-----------|
| 1 | ... | ... | ... |

### HN Karma Comment
- Thread: [title + URL]
- Comment posted: [YES / NO]
- Karma before: [number]
- Karma after: [number]

### GitHub Conversations
- New replies: [count]

### Quality
- Health: [ok/error]
- Eval: [N]/56
- DNS: [resolves / not resolving]
- Git: [hash]

### Maryan Actions Required
- [ONLY if Show HN was rate-limited or blocked]
```

---

## HARD RULES

1. **KPI 1: Post Show HN.** Use Safari `do JavaScript` to fill the submit form. This is the same method that posted 8 tweets and 1 HN comment. If HN rate-limits, document it.

2. **KPI 2: Send 5 more B2B emails.** Target YC AI startups. Sign as "Maryan K."

3. **KPI 3: Post 1 more HN comment.** Genuine value. Zero AgentShield mentions.

4. **Use the new domain in all links.** `agentshield.sipiteno.com` is live and resolving. Use it in emails, HN posts, and GitHub comments instead of `agentshield.fly.dev`.

5. **Never mention cron. Never touch memory. Never fabricate.**

6. **The Safari `do JavaScript` technique is the standard for all browser tasks.** It works on HN (server-rendered HTML) and X.com (React contenteditable). If any task requires browser interaction, use `osascript -e 'tell application "Safari" to do JavaScript "..."' in document 1'`.

7. **If Show HN is posted successfully**, that is the single biggest distribution event in the project's history. The post links to the live demo, the eval gym, and the GitHub repo. Monitor for comments and respond to every single one.
