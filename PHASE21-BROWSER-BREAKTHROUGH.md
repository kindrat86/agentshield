# MISSION: Break Through the Browser Walls — Twitter, HN, DNS

## ⚠️ YOUR 3 KPIS (Complete ALL 3)
1. **Complete the $2,800 Twitter thread** — post tweets 3-8 as replies to tweet 2 from @sipiteno
2. **Build HN karma** — post 1+ genuine value comment on an active thread  
3. **Add DNS records** — make agentshield.sipiteno.com resolve

---

## RULE ZERO
Zero fabrication. Every claim backed by tool output. Never mention cron. Never touch memory.

---

## THE BROWSER AUTOMATION PROBLEM — AND THE SOLUTION

### Why Previous Sessions Failed
X.com, Cloudflare, and Product Hunt are complex React SPAs. Using `computer_use action='capture' mode='som'` on these sites returns 600+ elements per snapshot — menu bars, sidebars, ad iframes, trending topics. This burns 80% of the context budget before the actual target element is found. Previous agents correctly identified this as a limitation and stopped.

### The Solution: Typed Browser Page Rung
The `computer_use` skill documents a specific toolset for exactly this problem: the `cua_browser_*` actions. Instead of pixel-hunting through AX elements, this binds directly to the browser's DevTools protocol. It provides clean, numbered semantic snapshots. It is designed for complex web apps.

**Load the skill:**
```
skill_view name="computer-use"
```

Read the section: "Typed browser page rung" and "Verify → escalate ladder."

The workflow for a typed browser page:
1. `computer_use action='cua_browser_state'` — bind to the browser window using exact `(pid, window_id)`
2. Require `binding_quality='exact'` and `mutation_allowed=true`
3. `computer_use action='cua_browser_state'` — take a semantic snapshot, get a `tab_id` and element `ref`s
4. `computer_use action='cua_browser_click' ref='CURRENT_REF'` — click by semantic ref
5. `computer_use action='cua_browser_type' ref='INPUT_REF' text='...'` — type by semantic ref
6. After every mutation, call `cua_browser_state` again before another action

**If `cua_browser_*` is unavailable or fails to bind:** fall back to `mode='som'` captures, but cap at 2 attempts per site to avoid context exhaustion. Use the `max_elements` parameter (e.g., `max_elements=50`) to limit snapshot size.

---

## TASK 1: COMPLETE THE TWITTER THREAD (Priority #1)

### 1A. Read the thread content
```bash
read_file path="/Users/sipi/agentshield/content/twitter-thread.md"
```
Identify tweets 3 through 8 (they follow tweets 1 and 2 which are already live).

### 1B. Bind to the browser

First, identify the target browser window:
```bash
computer_use action='list_windows'
```
Find the X.com window (in Comet or Safari). Note the exact `pid` and `window_id`.

Then bind:
```
computer_use action='cua_browser_state' pid=PID window_id=WINDOW_ID query='x.com/sipiteno'
```
Require `binding_quality='exact'`.

### 1C. Navigate to tweet 2

If not already there:
```
computer_use action='cua_browser_navigate' url='https://x.com/sipiteno'
```

Take a semantic snapshot:
```
computer_use action='cua_browser_state'
```
Find the `ref` for tweet 2 (starts with "The problem: AI agents don't know they're spending money").

### 1D. Post tweets 3-8

For each remaining tweet (3 through 8):

1. Click "Reply" on the current tweet:
   ```
   computer_use action='cua_browser_click' ref='REPLY_BUTTON_REF'
   ```
   
2. Take a fresh snapshot:
   ```
   computer_use action='cua_browser_state'
   ```
   
3. Find the reply textarea `ref`

4. Type the tweet content:
   ```
   computer_use action='cua_browser_type' ref='TEXTAREA_REF' text='TWEET CONTENT HERE'
   ```
   
5. Take a fresh snapshot, find the submit/post button `ref`

6. Click post:
   ```
   computer_use action='cua_browser_click' ref='POST_BUTTON_REF'
   ```

7. Wait 2 seconds, take a snapshot to verify the tweet was posted

8. Find the newly posted tweet, click "Reply" on it, and repeat for the next tweet

### 1E. Critical typing note

If `cua_browser_type` delivers 0 characters (Chromium issue):
- Try `browser_type_mode='keystrokes'` instead of the default `insert_text`
- Try the native setter JS injection approach via `cua_browser_type` with `input_route='dom_event'`
- Fall back to clipboard paste: `echo "TEXT" | pbcopy`, then `computer_use action='cua_browser_pointer' browser_pointer_action='hover' ...` followed by `cmd+v`

### 1F. If ALL typed browser attempts fail

Fall back to `mode='som'` with `max_elements=50` to reduce context cost. Attempt 2 tweets maximum this way. If that also fails, document the exact 3-minute manual steps for Maryan.

---

## TASK 2: BUILD HN KARMA THROUGH GENUINE VALUE (Priority #2)

### 2A. Find active HN threads

```bash
# AI agent threads (last 48h)
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=AI+agent&tags=story&numericFilters=created_at_i>$(python3 -c 'import time; print(int(time.time()) - 172800)')" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for hit in d.get('hits', [])[:15]:
    print(f'{hit[\"objectID\"]:12} pts={hit.get(\"points\",0):3} comments={hit.get(\"num_comments\",0):3} {hit[\"title\"][:80]}')
" 2>/dev/null

# LLM/API cost threads
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=LLM+API+cost&tags=story&numericFilters=created_at_i>$(python3 -c 'import time; print(int(time.time()) - 172800)')" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for hit in d.get('hits', [])[:10]:
    print(f'{hit[\"objectID\"]:12} pts={hit.get(\"points\",0):3} comments={hit.get(\"num_comments\",0):3} {hit[\"title\"][:80]}')
" 2>/dev/null
```

### 2B. Read the top threads

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
print(f'URL: {d.get(\"url\")}')
show(d)
" 2>/dev/null
```

### 2C. Draft and post 2 genuine comments

Comments must:
1. Share a real technical insight from building/deploying AI agents
2. Add to the discussion — correct a misconception, provide a data point
3. Be 3-6 sentences
4. **Do NOT mention AgentShield, GitHub, or any link to our project**
5. Sound like a real developer

Save to `/Users/sipi/agentshield/content/hn-karma-comments-$(date +%Y%m%d).md`.

### 2D. Post via Safari (typed browser or foreground type)

Navigate:
```bash
open -a Safari "https://news.ycombinator.com/item?id=ITEM_ID"
```

Use `cua_browser_*` actions if Safari can be bound. Otherwise foreground `type` on the textarea.

Check karma after:
```bash
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "import sys,json; print(f'Karma: {json.load(sys.stdin).get(\"karma\",0)}')" 2>/dev/null
```

---

## TASK 3: ADD DNS RECORDS (Priority #3)

### 3A. Load skills
```
skill_view name="cloudflare-dns-operations"
```

### 3B. Verify Safari Google session
```bash
open -a Safari "https://mail.google.com/mail/u/0/"
```
Wait 3 seconds. Capture with `max_elements=30` to limit context cost.

If Gmail loads for mkondratyuk86@gmail.com → proceed.

### 3C. Navigate to Cloudflare via typed browser

```bash
open -a Safari "https://dash.cloudflare.com/"
```

Use `cua_browser_*` actions to navigate:
1. `cua_browser_state` — snapshot the dashboard
2. Find `sipiteno.com` ref
3. `cua_browser_click ref='SIPITENO_REF'`
4. `cua_browser_state` — snapshot the zone page
5. Find DNS → Records navigation ref
6. `cua_browser_click ref='DNS_REF'`

### 3D. Add A and AAAA records

Once on the DNS Records page:

1. Click "Add record":
   ```
   computer_use action='cua_browser_click' ref='ADD_RECORD_REF'
   ```

2. Take a fresh snapshot. Find the type dropdown, name field, IPv4 field.

3. Fill the A record:
   - Type: `cua_browser_set_input` or `set_value` with value='A'
   - Name: `cua_browser_type ref='NAME_REF' text='agentshield'`
   - IPv4: `cua_browser_type ref='IPV4_REF' text='66.241.125.16'`
   - Proxy: click the orange cloud toggle to turn OFF (grey cloud)
   - Save: `cua_browser_click ref='SAVE_REF'`

4. Repeat for AAAA record:
   - Type: AAAA
   - Name: agentshield
   - IPv6: `2a09:8280:1::166:9212:0`

### 3E. Verify DNS propagation
```bash
sleep 120  # Wait 2 minutes
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
```

---

## TASK 4: SEND 5 MORE B2B EMAILS (Priority #4 — if time permits)

### 4A. Find 5 new targets

We've emailed: Helicone, LangChain, Braintrust, Portkey, AgentOps, LLMonitor, Peluza, Autoblocks, PromptLayer. Find NEW companies.

```bash
web_search "AI agent framework startup 2026"
web_search "AI cost management tool startup 2026"
web_search "LLM observability platform 2026"
```

### 4B. Send via Resend (curl, not Python)

Use the templates from Phase 20 (framework pitch / observability partnership / audit prospect). Sign as "Maryan K."

```bash
curl -s -X POST "https://api.resend.com/emails" \
  -H "Authorization: Bearer REDACTED" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "AgentShield <sales@sipiteno.com>",
    "to": ["RECIPIENT"],
    "bcc": ["sales@sipiteno.com"],
    "subject": "SUBJECT",
    "html": "HTML BODY"
  }'
```

---

## TASK 5: VERIFY & COMMIT

```bash
# Product health
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# DNS
dig agentshield.sipiteno.com A +short

# HN karma
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "import sys,json; print(f'Karma: {json.load(sys.stdin).get(\"karma\",0)}')" 2>/dev/null

# Commit
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 21: Typed browser rung — Twitter thread, HN karma, DNS records"
git log --oneline -3
```

---

## REPORT FORMAT

```
## Phase 21 — Browser Breakthrough Report

### Twitter Thread
- Typed browser bound: [YES / NO]
- Tweets 3-8 posted: [count/6 — include URLs]
- Method used: [cua_browser_type / keystrokes / foreground type / manual fallback]
- Context budget: [did the typed rung solve the 600-element problem?]

### HN Karma
- Comments posted: [count — include HN URLs]
- Starting karma: 1
- Ending karma: [number]

### DNS
- Safari Google session: [Active / Not active]
- Records added: [YES / NO — via typed browser or set_value]
- dig A: [output]
- dig AAAA: [output]

### B2B Emails (if sent)
- New emails: [count]
- Companies: [list]

### Quality
- Health: [ok/error]
- Eval: [N]/56
- Tests: [N]/14
- Git: [hash]

### Maryan Actions Required
- [ONLY what truly couldn't be automated after using the typed browser rung]
```

---

## HARD RULES

1. **KPI 1: Complete the Twitter thread using `cua_browser_*` actions.** This is the primary test of whether the typed browser rung solves the React SPA problem.

2. **KPI 2: Post 1+ HN comment.** Genuine value, zero AgentShield mentions.

3. **KPI 3: Add DNS records.** Use typed browser if possible.

4. **Use `max_elements=50` on any `mode='som'` capture** to prevent context exhaustion if the typed rung is unavailable.

5. **Never mention cron. Never touch memory. Never fabricate.**

6. **Sign all emails as "Maryan K."** (not full surname).

7. **If the typed browser rung works on X.com**, that changes everything — it means Product Hunt submission, Cloudflare, and all other React SPA targets are now viable. Document the technique clearly.

8. **If the typed browser rung does NOT work or is unavailable**, fall back to foreground `type` with `max_elements=50` captures. Attempt max 2 tweets this way. If context is still a problem, document manual steps.
