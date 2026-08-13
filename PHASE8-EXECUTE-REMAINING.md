# MISSION: Execute the 3 Remaining Human Tasks Autonomously

## ⚠️ RULE ZERO: YOU CANNOT FABRICATE ANY RESULT

Every claim you make must be backed by tool output included IN your response. If you cannot produce evidence, say so honestly. Do not invent URLs, cron IDs, comment IDs, or domain statuses.

## CONTEXT

AgentShield is a firewall for AI agent spending. Python 3.11 stdlib, zero deps, 50/50 eval gym. Live at `https://agentshield.fly.dev`. The entire funnel infrastructure is built: 8 real cron jobs verified, 6 GitHub outreach posts live, comparison pages live, email nurture active, spend radar operational.

## WHAT STILL MUST BE DONE (3 tasks)

| # | Task | Priority |
|---|------|----------|
| 1 | Add DNS records for `agentshield.sipiteno.com` in Cloudflare | BLOCKER |
| 2 | Submit Product Hunt listing | HIGH |
| 3 | Post on safe Reddit subreddits | MEDIUM |

## YOUR TOOLKIT

- `computer_use`, drives macOS desktop GUI (Safari, Comet) in the background
- Safari, carries Google OAuth session for Cloudflare, GitHub OAuth for PH
- Comet, carries Reddit session for u/Worth_Wealth_6811
- `terminal`, shell access
- `gh` CLI, GitHub API authenticated as kindrat86
- `web_extract`, `web_search`, internet access

## REFERENCE SKILLS (load before starting)

Load these at the start of your session:
```
skill_view name="cloudflare-dns-operations"
skill_view name="macos-browser-driving"  
```

The cloudflare skill confirms: `sipiteno.com` is in Acct2 (Google login: `mkondratyuk86@gmail.com`). No API token exists for it. The ONLY path is the Safari dashboard.

The macos-browser-driving skill Section 2 says: the target window must be frontmost for hit-test clicks. Section 5 says: `open -a Safari "<url>"` is the reliable way to open a URL (this also fronts the app). Section 12 says: React forms can be filled via JavaScript native setter + dispatchEvent. Section 3 says: any navigation invalidates the snapshot, always capture fresh before acting.

---

## TASK 1: DNS RECORDS FOR agentshield.sipiteno.com

**Goal:** Add these two records to the sipiteno.com Cloudflare zone:
- A record: `agentshield` → `66.241.125.16`
- AAAA record: `agentshield` → `2a09:8280:1::166:9212:0`

### Step-by-step:

### 1A. Verify Safari session
```bash
open -a Safari "https://mail.google.com/mail/u/0/"
```
Wait 3 seconds. Then:
```
computer_use action='capture' mode='som' app='Safari'
```
Read the capture. There are 3 possible states:

**State A, Gmail loads showing an inbox:**
Look at the top-right corner. If you see an avatar or profile picture, check if it belongs to `mkondratyuk86@gmail.com`. If yes → great, session is active. Proceed to Step 1B.

**State B, Google account chooser page:**
If you see "Choose an account" with a list of accounts, look for `mkondratyuk86@gmail.com`. Click it by element index. Then capture again. If it asks for a password → this path is blocked. Report: "Cloudflare: Google session expired, needs password re-entry."

**State C, Gmail login page (email field):**
The session is not active. Report: "Cloudflare: no active Google session in Safari."

### 1B. Navigate to Cloudflare dashboard
```bash
open -a Safari "https://dash.cloudflare.com/"
```
Wait 3 seconds. Capture:
```
computer_use action='capture' mode='som' app='Safari'
```

**If you see a Cloudflare login page:** Look for "Continue with Google" button. Click it. It should auto-authenticate using the Gmail session verified in 1A. If it asks for a password again → blocked.

**If you see the Cloudflare dashboard (domains list):** Look for `sipiteno.com` in the list. Click it by element index.

**Important:** Per the cloudflare skill, direct zone URLs (`dash.cloudflare.com/{zone_id}/dns/records`) 404 in the new dashboard. You MUST click the zone from the domains list.

### 1C. Navigate to DNS Records
On the sipiteno.com zone overview page:
- Look for "DNS" in the left sidebar
- Click it (may need to expand a section first)
- Click "Records"
- Capture and verify you see existing DNS records for sipiteno.com

### 1D. Add the A record
Click "Add record" button. A form appears with fields:
- **Type dropdown:** Use `set_value` with value='A' on the select element
- **Name:** Use `type` action with text='agentshield'. If background mode returns 0 chars, use `delivery_mode='foreground'`
- **IPv4 address:** Use `type` with text='66.241.125.16'
- **TTL:** Leave as Auto (don't touch it)
- **Proxy status:** Click the orange cloud icon to turn it OFF. Grey cloud = DNS only. This is required.
- **Click Save**

After clicking Save, capture the records list again. You should see a new row with:
- Type: A
- Name: agentshield
- Content: 66.241.125.16
- Proxy: DNS only (grey cloud)

**If you don't see it:** the record wasn't saved. Try again or report the failure.

### 1E. Add the AAAA record
Same process as 1D but:
- Type: AAAA
- Name: agentshield
- IPv6: 2a09:8280:1::166:9212:0

Capture after saving to verify both records are present.

### 1F. Verify DNS propagation
Wait 2 minutes, then run:
```bash
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
```
**Include the raw output in your response.** If both return the expected IPs → DNS is working. If they return nothing → DNS hasn't propagated yet, wait 2 more minutes and retry. If still nothing after 5 minutes → the records might not have been saved correctly.

### 1G. Verify Fly.io certificate
```bash
fly certs list -a agentshield
```
The cert for `agentshield.sipiteno.com` should show a status. If it shows "Ready" → cert is active. If "Pending" → wait 5 more minutes and check again.

### 1H. Test the domain
```bash
curl -s -o /dev/null -w "%{http_code}" https://agentshield.sipiteno.com
```
**Include the HTTP code in your response.** 200 = domain is live and serving.

---

## TASK 2: PRODUCT HUNT SUBMISSION

**Content file:** `/Users/sipi/agentshield/content/producthunt-listing.md`, read this first.

### 2A. Read the listing content
```bash
read_file path="/Users/sipi/agentshield/content/producthunt-listing.md"
```
Extract: tagline, description, maker comment, URLs, Twitter handle.

### 2B. Navigate to PH submission
```bash
open -a Safari "https://www.producthunt.com/posts/new"
```
Wait 3 seconds. Capture.

**If redirected to login:** Look for "Sign in with GitHub" button. Click it. You should auto-authenticate (Maryan K's GitHub OAuth is in Safari's session). If you get a GitHub authorization screen, click "Authorize."

**If you see the submission form:** Proceed.

### 2C. Fill text fields via JavaScript injection

Per the macos-browser-driving skill Section 12, React forms can be filled using the native setter technique. For each field, run:

```bash
osascript -e 'tell application "Safari" to do JavaScript "
  var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \"value\").set;
  var el = document.querySelector(\"SELECTOR\");
  nativeSetter.call(el, \"VALUE\");
  el.dispatchEvent(new Event(\"input\", { bubbles: true }));
  el.dispatchEvent(new Event(\"change\", { bubbles: true }));
  \"VALUE IS: \" + el.value;
"'
```

Fill these fields with values from the content file:

1. **Product name**, selector: `input[name="post[name]"]`, value: `"AgentShield, AI Agent Spend Firewall"`
2. **Tagline**, selector: `textarea[name="post[tagline]"]`, use textarea setter (not input setter), value: `"A firewall for AI agent spending"`
3. **Website URL**, selector: `input[name="post[website_url]"]`, value: `"https://agentshield.sipiteno.com"` (if DNS worked) or `"https://agentshield.fly.dev"`
4. **GitHub URL**, value: `"https://github.com/kindrat86/agentshield"`
5. **Description**, use textarea setter, value from content file (260 chars max, COUNT before injecting)
6. **Maker story**, use textarea setter, full maker comment from content file
7. **Twitter**, value: `"@Sipiteno"`

For textarea fields, use this pattern instead:
```javascript
var taSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
var el = document.querySelector("textarea[name='post[tagline]']");
taSetter.call(el, "TEXT");
el.dispatchEvent(new Event("input", { bubbles: true }));
```

After filling ALL fields, capture the form to verify they're populated.

### 2D. Generate and upload logo

**Generate logo:**
```bash
python3.11 << 'PYEOF'
import struct, zlib
def create_png(w, h, r, g, b):
    def chunk(ct, data):
        c = ct + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    raw = b''.join(b'\x00' + bytes([r, g, b]) * w for _ in range(h))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
with open('/tmp/agentshield-logo.png', 'wb') as f:
    f.write(create_png(240, 240, 0x00, 0xd4, 0xaa))
print('Logo created: 240x240 green (#00d4aa)')
PYEOF
```

**Upload:**
1. Capture the PH form and find the image upload area (look for "Add logo" or a dotted upload box)
2. Click it by element index
3. A macOS file picker dialog opens
4. Use `computer_use action='type' text='/tmp/agentshield-logo.png' delivery_mode='foreground'`
5. Press `computer_use action='key' keys='return' delivery_mode='foreground'`
6. Wait 2 seconds, capture again. The image should appear.

Per the macos-browser-driving skill: "Native browser dialogs DO accept foreground keystrokes." This should work.

### 2E. Handle Launch Tags, THE MAIN CHALLENGE

The PH form has a "Launch Tags" autocomplete/combobox. This React component is known to be a HARD WALL for automation. Try these approaches ONCE each:

**Attempt 1:** `set_value`
```
computer_use action='set_value' element=N value='Developer Tools'
```
(Find element N from the capture, look for input with role="combobox")

**Attempt 2:** JavaScript injection
```bash
osascript -e 'tell application "Safari" to do JavaScript "
  var inputs = document.querySelectorAll(\"input[aria-autocomplete='list'], input[role='combobox']\");
  \"Found \" + inputs.length + \" combobox(es)\";
"'
```
If found, try:
```javascript
var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
s.call(inputs[0], 'Developer Tools');
inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
inputs[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
```

**Attempt 3:** Foreground typing
```
computer_use action='type' text='Developer Tools' delivery_mode='foreground'
```
Then wait 1 second for dropdown to appear, capture, and if a suggestion is visible, click it.

**If all 3 fail, ESCAPE HATCH:**
Tell the user: *"Everything is filled except one field. Type 'Developer Tools' in the launch tags box and press Enter. That's it."* Then wait for them to do it, capture again, and proceed.

### 2F. Submit
Once all fields are filled and images uploaded:
1. Click "Next step" or "Continue" by element index
2. Capture the review page
3. If everything looks correct, click "Submit" or "Launch"
4. **Capture the confirmation page and record the URL**

### 2G. After submission, add PH badge
Once you have the real PH URL, add the badge to the landing page:

Read `/Users/sipi/agentshield/public/index.html` and find the "As featured on" strip. Add after the GitHub link:
```html
<a href="PH_URL_HERE" target="_blank" style="display:inline-block;margin-left:8px">
  <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg" alt="Featured on Product Hunt" width="160" height="34">
</a>
```

Then patch the file and deploy:
```bash
cd /Users/sipi/agentshield
fly deploy
```

Verify:
```bash
curl -s https://agentshield.fly.dev/ | grep -c "producthunt"
```
Should return > 0.

---

## TASK 3: REDDIT DRAFTS

### 3A. Verify Comet Reddit session
```bash
open -a Comet "https://www.reddit.com"
```
Wait 3 seconds. Capture:
```
computer_use action='capture' mode='som' app='Comet'
```

Check the top-right corner. If you see a user avatar or username → session is active. If you see "Log In" → blocked. Report which state.

### 3B. Find fresh radar drafts
```bash
# Check latest spend radar output
cat $(ls -t /Users/sipi/.hermes/profiles/architector/cron/output/c52aa796f78f/*.md 2>/dev/null | head -1) 2>/dev/null | head -80
```

If no fresh drafts exist, use the radar to generate new ones:
```bash
cd /Users/sipi/agentshield && python3.11 scripts/spend_radar.py 2>&1 | head -80
```

### 3C. Post drafts
For each draft targeting a SAFE subreddit (r/datasets, r/juststart, r/devops, r/programming, r/MachineLearning, r/OpenAI):

1. Navigate: `open -a Comet "<post_url>"`
2. Capture to find the comment box
3. Click comment box by element index
4. Type the draft using `delivery_mode='foreground'`:
   ```
   computer_use action='type' text='DRAFT TEXT HERE' delivery_mode='foreground'
   ```
5. Click "Comment" or "Reply" button by element index
6. Capture to verify the comment appears

If Comet returns "delivered 0 of N" for type (a known Chromium issue), try pasting:
- Copy text to clipboard: `echo "DRAFT" | pbcopy`
- Then in Comet: `computer_use action='key' keys='cmd+v' delivery_mode='foreground'`

---

## FINAL VERIFICATION

Run these checks and include the raw output:

```bash
# DNS
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
curl -s -o /dev/null -w "HTTP: %{http_code}" https://agentshield.sipiteno.com

# Tests
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1 | tail -3

# Eval
curl -s https://agentshield.fly.dev/eval

# Health
curl -s https://agentshield.fly.dev/health

# PH badge
curl -s https://agentshield.fly.dev/ | grep -c "producthunt"

# Cron pipeline
# Run cronjob list and count enabled jobs

# Deploy
cd /Users/sipi/agentshield && fly deploy
```

---

## REPORT FORMAT

Produce this exact report at the end:

```
## Autonomous Execution Report

### DNS
- Safari session: [Active as X / Not active / Blocked]
- A record added: [YES / NO / FAILED (reason)]
- AAAA record added: [YES / NO / FAILED (reason)]
- dig A output: [raw output]
- dig AAAA output: [raw output]
- Domain serves content: [HTTP code]

### Product Hunt
- Safari session: [Authenticated / Not authenticated]
- Fields filled: [count]/[total]
- Images uploaded: [count]
- Tags filled: [Automated / Manual fallback used]
- Submitted: [YES / NO]
- PH URL: [URL or "Not yet submitted"]
- Badge on landing page: [YES / NO]

### Reddit
- Comet session: [Active / Not active]
- Drafts found: [count]
- Drafts posted: [count]
- Subreddits: [list]

### Quality Checks
- Tests: [N]/14
- Eval: [N]/50
- Health: [ok/error]
- Deploy: [live/error]

### Tasks Still Requiring Human
- [Only list what truly couldn't be automated. Be specific with exact instructions.]
```
