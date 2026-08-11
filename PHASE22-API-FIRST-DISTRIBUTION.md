# MISSION: Post Twitter Thread via xurl CLI + HN Karma + DNS via API

## ⚠️ YOUR 3 KPIS
1. **Post the remaining 6 tweets (3-8) of the $2,800 thread using `xurl reply`**
2. **Post 1 genuine HN comment via Safari (HN is server-rendered HTML, not React)**
3. **Add DNS records via Cloudflare API (token-based, no browser)**

---

## RULE ZERO
Zero fabrication. Never mention cron. Never touch memory. Sign all communications as "Maryan K."

---

## TASK 1: COMPLETE THE TWITTER THREAD VIA xurl CLI (Priority #1)

### The Breakthrough
`xurl` is installed at `/Users/sipi/.local/bin/xurl` — it's X's official CLI. It posts tweets/replies directly from the terminal. No browser needed. **This is how we bypass the React SPA problem entirely.**

### 1A. Check xurl auth status
```bash
xurl auth status 2>&1
```

If `my-app` has `oauth2: (none)`:
- The app `my-app` exists but has a placeholder Client ID (`YOUR_CLI…`)
- Check if there's another app with real credentials
- If NO app has credentials: proceed to 1B (user setup required)

### 1B. If xurl needs authentication (user action required)

The user must complete OAuth2 one time. Document this precisely:

```
TWITTER/xurl SETUP (5 minutes, one time only):

1. Go to: https://developer.x.com/en/portal/dashboard
2. Create or open an app
3. Set redirect URI to: http://localhost:8080/callback
4. Copy the Client ID and Client Secret
5. Run these commands in terminal (NOT in the agent — secrets involved):

   xurl auth apps add my-app --client-id YOUR_REAL_CLIENT_ID --client-secret YOUR_REAL_CLIENT_SECRET
   xurl auth oauth2 --app my-app
   xurl auth default my-app

6. Verify:
   xurl auth status
   xurl whoami

After this, the agent can post tweets programmatically forever.
```

### 1C. If xurl IS authenticated

First, find tweet 2's ID (the last live tweet in the thread):

```bash
# Get the user's recent tweets
xurl user @sipiteno 2>&1
# Or search for the specific tweet
xurl search "from:sipiteno \"AI agents don't know\"" -n 1 2>&1
```

Extract the tweet ID from the JSON response.

### 1D. Post tweets 3-8 as replies

Read the thread content:
```bash
read_file path="/Users/sipi/agentshield/content/twitter-thread.md"
```

For each remaining tweet (3 through 8), post it as a reply to the PREVIOUS tweet:

```bash
# Tweet 3 (reply to tweet 2)
xurl reply TWEET2_ID "TWEET_3_CONTENT" 2>&1
# Record the returned tweet ID

# Tweet 4 (reply to tweet 3)
xurl reply TWEET3_ID "TWEET_4_CONTENT" 2>&1
# Record the returned tweet ID

# Continue for tweets 5-8
```

**IMPORTANT:** The X API returns the new tweet ID in the JSON response. Use that ID for the next reply. Do NOT guess IDs.

### 1E. Verify the thread
```bash
# Check that 8 tweets are now visible
xurl user @sipiteno 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Account: @{d.get(\"data\",{}).get(\"username\",\"?\")}')
" 2>/dev/null

# Or search for the thread
xurl search "from:sipitend" -n 10 2>&1
```

---

## TASK 2: POST HN COMMENT VIA SAFARI (Priority #2)

HN is server-rendered HTML (not a React SPA). The comment textarea is a plain `<textarea>` with a form action. This is MUCH simpler than X.com.

### 2A. Find active threads

```bash
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=AI+agent&tags=story&numericFilters=created_at_i>$(python3 -c 'import time; print(int(time.time()) - 172800)')" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for hit in d.get('hits', [])[:15]:
    print(f'{hit[\"objectID\"]:12} pts={hit.get(\"points\",0):3} comments={hit.get(\"num_comments\",0):3} {hit[\"title\"][:80]}')
" 2>/dev/null
```

### 2B. Read the top thread

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

### 2C. Draft a genuine comment

3-6 sentences. Real technical insight. **Zero AgentShield mentions.** Sound like a developer. Save to `/Users/sipi/agentshield/content/hn-karma-comment-$(date +%Y%m%d).md`.

### 2D. Post via Safari

```bash
open -a Safari "https://news.ycombinator.com/item?id=ITEM_ID"
```

Since HN is server-rendered HTML:
- Capture with `max_elements=30` (should be plenty for HN's simple page)
- Find the comment textarea element
- Use foreground `type` to enter the comment
- Click "add comment"

### 2E. Check karma
```bash
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "import sys,json; print(f'Karma: {json.load(sys.stdin).get(\"karma\",0)}')" 2>/dev/null
```

---

## TASK 3: DNS RECORDS VIA CLOUDFLARE API (Priority #3)

### The New Approach
Instead of browser automation on the Cloudflare dashboard SPA, use the Cloudflare REST API directly. This requires a scoped API token.

### 3A. Check for existing token

```bash
grep -i "CLOUDFLARE_API_TOKEN\|CLOUDFLARE_DNS_EDIT\|CF_API" ~/.hermes/.env 2>/dev/null
env | grep -i CLOUDFLARE 2>/dev/null
```

### 3B. If no token exists

We need the zone ID for sipiteno.com first. Try with the read-only vault token:

```bash
# The vault has a read-only token that can look up zones
RO_TOKEN=$(grep "CLOUDFLARE_API_TOKEN" ~/.hermes/.env 2>/dev/null | cut -d= -f2 | tr -d '"')
if [ -n "$RO_TOKEN" ]; then
    curl -s "https://api.cloudflare.com/client/v4/zones?name=sipiteno.com" \
      -H "Authorization: Bearer $RO_TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d.get('result'):
    print(f'Zone ID: {d[\"result\"][0][\"id\"]}')
else:
    print('No access to sipiteno.com zone (expected — dashboard-only)')
" 2>/dev/null
fi
```

If this returns "No access" → we need a token with DNS edit permissions for sipiteno.com.

Document for Maryan:
```
CLOUDFLARE API TOKEN (2 minutes, enables DNS automation forever):

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use template: "Edit zone DNS"
4. Zone Resources: Include → Specific zone → sipiteno.com
5. Continue to summary → Create Token
6. Copy the token

Then run:
echo 'CLOUDFLARE_DNS_EDIT_TOKEN=YOUR_TOKEN' >> ~/.hermes/.env

After that, the agent can add DNS records via API — no browser needed.
```

### 3C. If a DNS-edit token IS available

```bash
TOKEN=$(grep "CLOUDFLARE_DNS_EDIT" ~/.hermes/.env 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "")

if [ -z "$TOKEN" ]; then
    echo "No DNS edit token found"
    # Skip to next task
else
    # Get zone ID
    ZONE=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=sipiteno.com" \
      -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])" 2>/dev/null)
    
    echo "Zone ID: $ZONE"
    
    # Add A record
    curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"type":"A","name":"agentshield","content":"66.241.125.16","ttl":1,"proxied":false}'
    
    # Add AAAA record
    curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"type":"AAAA","name":"agentshield","content":"2a09:8280:1::166:9212:0","ttl":1,"proxied":false}'
fi
```

### 3D. Verify
```bash
sleep 120
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
curl -s -o /dev/null -w "%{http_code}" https://agentshield.sipiteno.com 2>&1
```

---

## TASK 4: SEND 5 MORE B2B EMAILS (if time permits)

Find 5 NEW companies (we've emailed 13 so far):

```bash
web_search "AI agent framework 2026 open source"
web_search "LLM cost optimization startup 2026"
web_search "AI gateway platform enterprise 2026"
```

Send via Resend (curl, not Python):
```bash
curl -s -X POST "https://api.resend.com/emails" \
  -H "Authorization: Bearer REDACTED_RESEND_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "AgentShield <sales@sipiteno.com>",
    "to": ["RECIPIENT"],
    "bcc": ["sales@sipiteno.com"],
    "subject": "SUBJECT",
    "html": "HTML BODY"
  }'
```

Sign as "Maryan K."

---

## TASK 5: CHECK GITHUB CONVERSATIONS

```bash
for url in \
  "https://github.com/openclaw/openclaw/issues/42475" \
  "https://github.com/zeroclaw-labs/zeroclaw/issues/2269" \
  "https://github.com/langchain-ai/langchain/issues/31647"; do
  echo "=== $(basename $(dirname $url))/$(basename $url) ==="
  gh issue view "$url" --comments 2>&1 | tail -15
  echo ""
done
```

---

## TASK 6: VERIFY & COMMIT

```bash
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1 | tail -3
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 22: xurl Twitter + HN comment + DNS API + B2B emails"
```

---

## REPORT FORMAT

```
## Phase 22 — API-First Distribution Report

### Twitter Thread (via xurl)
- xurl auth status: [Authenticated / Needs setup]
- If needs setup: [exact setup steps documented]
- If authenticated:
  - Tweet 2 ID: [ID]
  - Tweets 3-8 posted: [count/6 — include tweet IDs from xurl JSON response]
  - Thread complete: [YES / NO]

### HN Karma
- Comment posted: [YES/NO — include HN URL]
- Karma before: 1
- Karma after: [number]

### DNS (via Cloudflare API)
- DNS edit token found: [YES / NO]
- If no token: [exact token creation steps documented]
- If token found:
  - A record added: [YES / NO — include API response]
  - AAAA record added: [YES / NO]
  - dig A: [output]
  - dig AAAA: [output]

### B2B Emails (if sent)
- New emails: [count]
- Companies: [list]

### GitHub Conversations
- New replies: [count]

### Quality
- Health: [ok/error]
- Eval: [N]/56
- Tests: [N]/14
- Git: [hash]

### Maryan Actions Required
- [ONLY what truly couldn't be automated — should be the one-time xurl OAuth and CF token creation if not already done]
```

---

## HARD RULES

1. **KPI 1: Complete the Twitter thread via `xurl reply`.** This is the entire reason we're using xurl — it bypasses the browser entirely.

2. **KPI 2: Post 1 HN comment.** HN is server-rendered HTML — browser typing works fine on HN.

3. **KPI 3: Add DNS records via Cloudflare API.** No browser. Pure `curl`.

4. **If xurl needs OAuth setup, that's a ONE-TIME human action.** Document it precisely. Once done, the agent can post to Twitter forever without any browser.

5. **If Cloudflare needs a DNS edit token, that's a ONE-TIME human action.** Document it precisely. Once done, the agent can manage DNS forever without any browser.

6. **Never mention cron. Never touch memory. Never fabricate. Sign as "Maryan K."**

7. **The xurl approach is the breakthrough.** If authenticated, it solves the Twitter thread in 6 `xurl reply` commands — zero browser, zero React, zero context exhaustion. This is the out-of-the-box solution.
