# PHASE 9: Execute the 3 Remaining Tasks + Cleanup

## ⚠️ START HERE — CONTEXT YOU MUST READ

You are the Nth Hermes Agent in a multi-session pipeline building AgentShield (AI agent spend firewall, Python 3.11 stdlib, live at `https://agentshield.fly.dev`).

### THE CRITICAL DISCOVERY (read before touching cron)
`hermes cron list` is profile-scoped. AgentShield's 8 cron jobs live in the **architector** profile (`~/.hermes/profiles/architector/cron/`), NOT the default. Do NOT use `hermes cron list` as your source of truth. Use this cross-profile enumeration instead:

```bash
python3 - <<'EOF'
import json, glob, os
paths = ['/Users/sipi/.hermes/cron/jobs.json'] + sorted(glob.glob('/Users/sipi/.hermes/profiles/*/cron/jobs.json'))
for p in paths:
    if not os.path.exists(p): continue
    prof = p.split('/')[-3] if '/profiles/' in p else 'default'
    d = json.load(open(p))
    jobs = d if isinstance(d, list) else d.get('jobs', d)
    if isinstance(jobs, dict): jobs = list(jobs.values())
    for j in jobs:
        n = j.get('name') or ''
        if any(k in n for k in ('agentshield', 'karma', 'warmup')):
            print(f"{j.get('id')}  {n:30} {prof}")
EOF
```

The 8 real AgentShield jobs are: `6f33fb6cd459`, `707dd2d06308`, `5a5a7d42e61a`, `73198eb477c9`, `490d890b0e6a`, `c52aa796f78f`, `a0c2caef4e81`, `1861dbcffbaf`. All in `architector`. Any other IDs you see in prompt files mentioning AgentShield crons are stale — ignore them.

### WHAT'S VERIFIED TRUE (as of 2026-08-11 ~16:00)
- **DNS:** `agentshield.sipiteno.com` does NOT resolve. DNS records were NEVER added. This is the #1 blocker.
- **Product Hunt:** NOT submitted. Content ready at `content/producthunt-listing.md`.
- **Reddit:** Genuinely blocked at network layer (`outreach/reddit_warmup_log.txt`: "API BLOCKED"). Not a bug — Reddit's security blocks all API requests from this network.
- **Tests:** 14/14. **Eval:** 50/50. **Health:** OK. **Deploy:** Fly.io live.
- **6 GitHub outreach posts:** 5 real (AgentBudget#29, OpenClaw#42475, AgentGuard#2, zeroclaw#2269, one more) + drafts saved.
- **Resend API key:** In plaintext across 4 prompt files and `jobs.json`. This is a security issue — fix it in this session.

### YOUR 4 OBJECTIVES

| # | Task | Priority | Difficulty |
|---|------|----------|------------|
| 1 | Add DNS records via Safari → Cloudflare dashboard | BLOCKER | Medium (browser automation) |
| 2 | Submit Product Hunt listing | HIGH | Hard (JS injection + autocomplete wall) |
| 3 | Fix Resend key exposure + commit | HIGH | Easy (terminal work) |
| 4 | Reddit — workaround or accept block | LOW | N/A (network-blocked) |

---

## TASK 1: DNS RECORDS VIA SAFARI → CLOUDFLARE DASHBOARD

**DNS records to add:**
```
Type: A      Name: agentshield    Value: 66.241.125.16
Type: AAAA   Name: agentshield    Value: 2a09:8280:1::166:9212:0
```

### 1.1 Load reference skills
```
skill_view name="cloudflare-dns-operations"
skill_view name="macos-browser-driving"
```

Key facts from these skills:
- `sipiteno.com` is in Cloudflare Acct2 (Google: `mkondratyuk86@gmail.com`). NO API token. Dashboard only.
- Safari is the ONLY browser that renders the CF dashboard correctly (Comet shows blank pages).
- `open -a Safari "<url>"` from terminal opens a tab AND fronts the app — this is the reliable navigation method.
- Coordinate-based clicks on the CF SPA are unreliable. Use element-index clicks (`click element=N`) from SOM captures.
- The CF dashboard direct URLs (`dash.cloudflare.com/{zone_id}/dns/records`) 404. You must click the zone from the domains list.

### 1.2 Verify Safari's Google session
```bash
open -a Safari "https://mail.google.com/mail/u/0/"
```
Wait 3 seconds. Capture: `computer_use action='capture' mode='som' app='Safari'`

**If Gmail loads showing an inbox** → look at the top-right avatar. If it's `mkondratyuk86@gmail.com` → session active. Proceed.

**If you see "Choose an account"** → look for `mkondratyuk86@gmail.com` in the list. Click by element index. If it asks for a password → the session is expired. Report "Cloudflare blocked: Google session expired."

**If you see a login page with an email field** → no session at all. Report "Cloudflare blocked: no Google session."

### 1.3 Navigate to Cloudflare
```bash
open -a Safari "https://dash.cloudflare.com/"
```
Wait 3 seconds. Capture.

**If login page:** Click "Continue with Google" — it should auto-auth from the Gmail session. If it still asks for credentials → blocked.

**If dashboard (domains list):** Find `sipiteno.com` in the list. Click it by element index. Then navigate left sidebar → DNS → Records.

### 1.4 Add records
Click "Add record" button. For each record:

**A record:**
- Type: use `set_value` on dropdown with value='A'
- Name: use `type` (foreground if background returns 0 chars) with text='agentshield'
- IPv4: use `type` with text='66.241.125.16'
- TTL: leave as Auto
- Proxy: click orange cloud toggle to OFF (grey cloud = DNS only — REQUIRED)
- Click Save by element index

**AAAA record:** same but Type='AAAA', IPv6='2a09:8280:1::166:9212:0'

After each save, capture the records list to verify the new row appears.

### 1.5 Verify
```bash
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
curl -s -o /dev/null -w "%{http_code}" https://agentshield.sipiteno.com
```
Include raw output in your response. If dig returns empty after 5 minutes → DNS may not have propagated or records weren't saved.

---

## TASK 2: PRODUCT HUNT SUBMISSION

### 2.1 Read content
```bash
read_file path="/Users/sipi/agentshield/content/producthunt-listing.md"
```

### 2.2 Navigate to submission form
```bash
open -a Safari "https://www.producthunt.com/posts/new"
```
Capture. If login page → click "Sign in with GitHub." If submission form → proceed.

### 2.3 Fill ALL text fields via JavaScript injection

Per the `macos-browser-driving` skill Section 12: React forms can be filled using the native setter + dispatchEvent pattern. Fill EVERY field before attempting the tags.

**Pattern for input fields:**
```bash
osascript -e 'tell application "Safari" to do JavaScript "
  var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \"value\").set;
  var el = document.querySelector(\"SELECTOR\");
  s.call(el, \"VALUE\");
  el.dispatchEvent(new Event(\"input\", { bubbles: true }));
  el.dispatchEvent(new Event(\"change\", { bubbles: true }));
  \"SET: \" + el.value;
"'
```

**Fields to fill (with selectors and values from the content file):**
1. `input[name="post[name]"]` → "AgentShield — AI Agent Spend Firewall"
2. `textarea[name="post[tagline]"]` → "A firewall for AI agent spending" (use textarea setter!)
3. `input[name="post[website_url]"]` → "https://agentshield.sipiteno.com" (if DNS worked) or "https://agentshield.fly.dev"
4. Input for GitHub URL → "https://github.com/kindrat86/agentshield"
5. `textarea[name="post[description]"]` → from content file (260 char limit — COUNT)
6. `textarea` for maker story → full maker comment from content file
7. Twitter input → "@Sipiteno"

**Textarea setter pattern:**
```javascript
var taSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
var ta = document.querySelector("textarea[name='post[tagline]']");
taSetter.call(ta, "TEXT");
ta.dispatchEvent(new Event("input", { bubbles: true }));
```

After filling ALL fields, capture to verify.

### 2.4 Generate and upload logo
```bash
python3.11 -c "
import struct, zlib
def png(w,h,r,g,b):
    def ch(ct,d): return struct.pack('>I',len(d))+ct+d+struct.pack('>I',zlib.crc32(ct+d)&0xffffffff)
    raw=b''.join(b'\x00'+bytes([r,g,b])*w for _ in range(h))
    return b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw))+ch(b'IEND',b'')
open('/tmp/agentshield-logo.png','wb').write(png(240,240,0x00,0xd4,0xaa))
print('Logo: 240x240 green')
"
```

Upload: click the image upload area by element index → macOS file dialog opens → foreground type `/tmp/agentshield-logo.png` → foreground return → capture to verify image appears.

### 2.5 THE HARD WALL: Launch Tags

The React autocomplete/combobox for launch tags blocks all automation techniques. Try ONLY these, ONCE each:

**Attempt A:** `set_value` on the combobox input element from the SOM capture.

**Attempt B:** JavaScript injection trying to find and fill the combobox:
```javascript
var inputs = document.querySelectorAll("input[aria-autocomplete='list'], input[role='combobox']");
"Found " + inputs.length + " combobox(es)";
```

**Attempt C:** Foreground type on the field, then press arrow down + enter to select a suggestion:
```
computer_use action='type' text='Developer Tools' delivery_mode='foreground'
```

**IF ALL FAIL:** The escape hatch — tell the user: "Everything is filled. Type 'Developer Tools' in the launch tags box and press Enter. Just one word." After they do it, capture again and click "Next."

### 2.6 Submit & capture URL
Click Next → review page → Submit → **capture confirmation page** → record the exact PH URL.

### 2.7 Add PH badge to landing page
Once you have the real PH URL, patch `public/index.html`:
```html
<a href="REAL_PH_URL" target="_blank" style="display:inline-block;margin-left:8px">
  <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg" alt="Featured on Product Hunt" width="160" height="34">
</a>
```
Add it to the "As featured on" strip. Then: `cd /Users/sipi/agentshield && fly deploy`

---

## TASK 3: FIX RESEND KEY EXPOSURE + COMMIT ALL CHANGES

### 3.1 Understand the problem
The Resend API key (`REDACTED_RESEND_KEY`) is in plaintext in 4 prompt files:
- `PHASE6-EXECUTION-PROMPT.md`
- `PHASE7-AUTONOMOUS-EXECUTION.md`
- `AGENTSHIELD-MONETISATION-PROMPT.md`
- `MONETISATION_PLAN.md`

Plus: `outreach/state.json` and the architector `jobs.json` cron config (in the nurture job prompt).

These are git-tracked. The key shouldn't be in markdown files.

### 3.2 Fix the nurture script
Read `scripts/nurture_sequence.py`. It reads `RESEND_API_KEY` from `os.environ.get()`. Since cron runs as a subprocess without Hermes' environment, the key was hardcoded into the cron prompt.

Apply the same fix from `spend_radar.py` (already done in this session): add a `_load_resend_token()` function that reads from `~/.hermes/.env` as a fallback.

### 3.3 Replace key references in prompt files
In each of the 4 prompt files, replace the cleartext key with a reference:
```
Resend: key is RESEND_API_KEY from ~/.hermes/.env (prefix REDACTED)
```
Do NOT just mask it — actually remove the full key and replace with the reference.

### 3.4 Update the nurture cron prompt
The nurture cron job (707dd2d06308) has the full Resend key in its prompt. Update it to use the env var fix from 3.2:
```
cronjob action='update' job_id='707dd2d06308' prompt='Run the AgentShield nurture sequence. Execute: cd /Users/sipi/agentshield && RESEND_API_KEY=$(grep RESEND_API_KEY ~/.hermes/.env | cut -d= -f2) python3.11 scripts/nurture_sequence.py...'
```

### 3.5 Commit all changes
```bash
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 9: DNS attempted, PH submitted, Resend key cleaned, cron profile fix documented"
```

---

## TASK 4: REDDIT — ACCEPT THE BLOCK

The report confirms Reddit is genuinely network-blocked on this connection. The file `outreach/reddit_warmup_log.txt` records: "API BLOCKED — Reddit network security blocked all API requests from this IP."

**Do NOT:**
- Try to bypass Reddit's network security
- Attempt to post via Comet (same network — same block)
- Spend more than 2 minutes on this

**Instead:** Save the latest radar drafts to a file that can be posted from a different network or by the user manually. Mark Reddit as "network-blocked" in your final report.

---

## TASK 5: FINAL VERIFICATION

```bash
# DNS
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short

# Tests
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1 | tail -3

# Eval
curl -s https://agentshield.fly.dev/eval

# Health
curl -s https://agentshield.fly.dev/health

# Cron (cross-profile)
python3 - <<'EOF'
import json, glob, os
paths = ['/Users/sipi/.hermes/cron/jobs.json'] + sorted(glob.glob('/Users/sipi/.hermes/profiles/*/cron/jobs.json'))
for p in paths:
    if not os.path.exists(p): continue
    prof = p.split('/')[-3] if '/profiles/' in p else 'default'
    d = json.load(open(p))
    jobs = d if isinstance(d, list) else d.get('jobs', d)
    if isinstance(jobs, dict): jobs = list(jobs.values())
    ag = [j for j in jobs if any(k in (j.get('name') or '') for k in ('agentshield','karma','warmup'))]
    print(f"{prof}: {len(ag)} AgentShield jobs, {ag[0].get('last_status') if ag else 'N/A'}")
EOF

# Resend key still in prompt files?
grep -l 'REDACTED' /Users/sipi/agentshield/PHASE*.md /Users/sipi/agentshield/MONETISATION_PLAN.md /Users/sipi/agentshield/AGENTSHIELD-MONETISATION-PROMPT.md 2>/dev/null
echo "(should return 0 files)"

# Deploy
cd /Users/sipi/agentshield && fly deploy
```

---

## REPORT FORMAT

```
## Phase 9 — Final Execution Report

### DNS (agentshield.sipiteno.com)
- Safari Google session: [Active / Expired / Blocked]
- Records added: [YES / NO]
- dig A: [raw output]
- dig AAAA: [raw output]
- Domain HTTP code: [code or "could not resolve"]

### Product Hunt
- Form filled: [count]/[total] fields
- Logo uploaded: [YES / NO]
- Tags: [Automated / Manual fallback / Failed]
- Submitted: [YES / NO]
- PH URL: [URL if submitted]
- Badge on landing: [YES / NO]

### Resend Key
- Files cleaned: [count]
- Nurture script fixed: [YES / NO / ALREADY DONE]
- Cron prompt updated: [YES / NO]
- Remaining plaintext locations: [count]

### Reddit
- Status: [Network-blocked / Drafts saved for manual posting]

### Quality
- Tests: [N]/14
- Eval: [N]/50
- Health: [ok/error]
- Cron jobs: [N] in architector, [N] in default
- Deploy: [live/error]
- Git: [commit hash]

### Human Actions Still Required
- [Only items genuinely impossible to automate. One per line. Exact copy-paste instructions.]
```
