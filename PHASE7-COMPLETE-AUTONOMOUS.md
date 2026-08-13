# MISSION: Zero-Human Execution, DNS + PH + Reddit + Memory

## CRITICAL: Read fully. Execute in order. Never fabricate. Verify with tools.

---

## WHAT YOU ARE

An autonomous agent running on the user's Mac. You have access to:
- `computer_use`, drives macOS GUI applications in the background
- `terminal`, shell access
- `gh` CLI, GitHub authenticated as `kindrat86`
- `fly` CLI, Fly.io authenticated
- Safari browser, carries Google + GitHub OAuth sessions
- Comet browser, carries Reddit session

## WHAT MUST BE DONE (4 tasks, zero human)

| Task | Current State | Goal |
|------|---------------|------|
| DNS | `agentshield.sipiteno.com` not resolving | Add A/AAAA records, verify propagation |
| Product Hunt | Content ready, not submitted | Submit listing, get live URL |
| GitHub Discussions | 3 drafts saved | Post all 3 via API |
| Reddit | Drafts from radar | Post on safe subreddits |

## VERIFICATION RULE
After claiming ANY action is complete, prove it with tool output. Never claim a cron job was created without showing `cronjob list`. Never claim a record was added without showing `dig` output. Never claim PH was submitted without showing the confirmation URL.

---

## PHASE 1: VERIFY CRON JOBS (5 min)

**Read this before touching any cron job.** Hermes has TWO cron stores, and `hermes cron list` shows only the **active** profile's jobs. Reading one store makes the other's IDs look fabricated. That is exactly what happened: four consecutive sessions accused each other of hallucinating cron IDs, and two competing "verified" lists got written into these prompts. **Both lists were real.** Neither was a hallucination.

- `~/.hermes/cron/`, **default** profile (currently active). Holds **zero** AgentShield jobs.
- `~/.hermes/profiles/architector/cron/`, **architector** profile. Holds **all 8** live AgentShield jobs.

There is no `--profile` flag on `hermes cron`. The only reliable check reads both stores directly.

### Action:

**Step 1, enumerate BOTH stores.** Do **not** use `hermes cron list` for this; it is profile-blind. Run this exactly as written (the heredoc body must stay at column 0, indenting it produces `IndentationError`):

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
            print(f"{j.get('id')}  {n:30} {(j.get('schedule_display') or ''):12} last={j.get('last_status')}  [profile: {prof}]")
EOF
```

**Step 2, expect exactly these 8 jobs**, all under `[profile: architector]`:

```
6f33fb6cd459, agentshield-market-scout , 09:00
707dd2d06308, agentshield-nurture      , 09:00
5a5a7d42e61a, agentshield-lead-processor, 10:00
73198eb477c9, hn-karma-warmup          , 11:00
490d890b0e6a, agentshield-github-monitor, 12:00
c52aa796f78f, agentshield-spend-radar  , 12:00
a0c2caef4e81, reddit-karma-warmup      , 14:00
1861dbcffbaf, warmup-weekly-report     , Mon 10:00
```

**Step 3, do NOT recreate any of these in the default profile.** Duplicates of all 8 (plus a redundant `market-scout-v2`) existed there until 2026-08-11. All nine shared `workdir: /Users/sipi/agentshield`, and two profile tickers contending for the same `TERMINAL_CWD` lock killed `agentshield-market-scout` with a 660s lock timeout. The duplicate `nurture` job also created a check-then-send race against Resend. All nine were deleted; backups are at `~/.hermes/cron/backups/*-predupe-20260811-1552`.

**Step 4, there is no blocklist of "fake" IDs**, and earlier versions of this prompt were wrong to publish one. If an ID is missing from the active profile, check the other store before drawing any conclusion. Absence from `hermes cron list` is not absence from the system.

---

## PHASE 2: DNS RECORDS VIA SAFARI → CLOUDFLARE DASHBOARD (15 min)

### Context
The `cloudflare-dns-operations` skill confirms: `sipiteno.com` is in Cloudflare Acct2 (Google login: `mkondratyuk86@gmail.com`). NO API token exists for this account. The ONLY path is the Safari dashboard. Safari on this Mac carries the Google session.

### Step 1: Verify Safari's Google session
```bash
open -a Safari "https://mail.google.com/mail/u/0/"
```
Wait 3 seconds. Capture:
```
computer_use action='capture' mode='som' app='Safari'
```
Look for evidence of which Google account is signed in:
- Does Gmail load showing an inbox?
- Look at the top-right avatar/profile picture
- If it shows `mkondratyuk86@gmail.com` → session active, proceed to Step 2
- If it shows a login page → check if clicking "Sign in" presents mkondratyuk86 in the account chooser
- If no Google session at all → this path is blocked, skip to Phase 3

### Step 2: Navigate to Cloudflare DNS
```bash
open -a Safari "https://dash.cloudflare.com/"
```
Capture. If you see the Cloudflare dashboard (domains list), click `sipiteno.com`. If you see a login page, click "Continue with Google", it should auto-authenticate using the Gmail session verified in Step 1.

### Step 3: Navigate to DNS Records
Once on the sipiteno.com zone page, navigate to DNS → Records:
- Look for "DNS" in the left sidebar menu
- Click "Records" sub-item
- Capture to verify you see existing DNS records

### Step 4: Add A record
Click "Add record" button. In the form:
- Type dropdown: use `set_value` to select "A"
- Name field: use `type` (foreground if background returns 0 chars) to type `agentshield`
- IPv4 address: use `type` to type `66.241.125.16`
- TTL: leave as Auto
- Proxy: click the orange cloud toggle to turn it OFF (grey cloud = DNS only)
- Click Save

Capture after saving to verify the record appears in the list.

**Pitfall alert:** Per the skill, coordinate clicks on CF SPA elements can be unreliable. Use element-index clicks (`click element=N`) from the SOM capture, not raw coordinates.

### Step 5: Add AAAA record
Same as Step 4 but:
- Type: AAAA
- Name: `agentshield`
- IPv6 address: `2a09:8280:1::166:9212:0`

### Step 6: Verify DNS propagation
Wait 2 minutes, then:
```bash
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
```
If both return the expected IPs → DNS is working.

### Step 7: Verify Fly.io cert
```bash
fly certs list -a agentshield
```
The `agentshield.sipiteno.com` cert should transition from "Pending" to "Ready" within ~10 min.

### Step 8: Test the domain
```bash
curl -s -o /dev/null -w "%{http_code}" https://agentshield.sipiteno.com
```
Should return 200.

---

## PHASE 3: PRODUCT HUNT SUBMISSION VIA SAFARI (20 min)

### Context
PH uses GitHub OAuth. The user is signed in as "Maryan K" via GitHub. Safari carries this session. The submission form is a React SPA. Per the `macos-browser-driving` skill Section 12, React text inputs and textareas CAN be filled via JavaScript native setter + dispatchEvent. The launch tags autocomplete is a HARD WALL, but we have a strategy.

### Content
Read `/Users/sipi/agentshield/content/producthunt-listing.md` to get all text.

### Step 1: Navigate to PH submission
```bash
open -a Safari "https://www.producthunt.com/posts/new"
```
Capture. If you see a login page, click "Sign in with GitHub." If you see the submission form, proceed.

### Step 2: Fill all text fields via JavaScript injection

**Technique** (from skill Section 12):
```bash
osascript -e 'tell application "Safari" to do JavaScript "
  var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \"value\").set;
  var input = document.querySelector(\"input[name='post[name]']\");
  nativeSetter.call(input, \"AgentShield, AI Agent Spend Firewall\");
  input.dispatchEvent(new Event(\"input\", { bubbles: true }));
  input.dispatchEvent(new Event(\"change\", { bubbles: true }));
"'
```

Fill these fields using this technique, reading values from `producthunt-listing.md`:

1. **Product name:** "AgentShield, AI Agent Spend Firewall"
2. **Tagline (40 chars):** "A firewall for AI agent spending" (35 chars). If too short: "A firewall for AI agent budgets & safety"
3. **Website URL:** `https://agentshield.sipiteno.com` (if Phase 2 succeeded) OR `https://agentshield.fly.dev` (fallback)
4. **GitHub URL:** `https://github.com/kindrat86/agentshield`
5. **Description (260 chars):** Count the characters from the listing doc before injecting. Trim if needed.
6. **Maker story (first comment):** The longest field. Use the textarea setter pattern:
```javascript
var taSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
var ta = document.querySelector("textarea[name='post[maker_story]']");
taSetter.call(ta, "FULL TEXT HERE...");
ta.dispatchEvent(new Event("input", { bubbles: true }));
```
7. **Twitter handle:** `@Sipiteno`

After each fill, verify: `'VALUE IS: ' + input.value`.

### Step 3: Handle images

The listing needs a logo (240×240) and screenshots.

**Generate logo:**
```bash
python3.11 << 'PYEOF'
# Try using Pillow if available, otherwise a minimal approach
try:
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (240, 240), '#0a0a0a')
    draw = ImageDraw.Draw(img)
    # Green shield
    draw.polygon([(120, 15), (220, 45), (220, 130), (120, 220), (20, 130), (20, 45)], fill='#00d4aa')
    draw.polygon([(120, 45), (190, 65), (190, 125), (120, 190), (50, 125), (50, 65)], fill='#0a0a0a')
    img.save('/tmp/agentshield-logo.png')
    print('Logo created with Pillow')
except ImportError:
    # Minimal PNG using stdlib
    import struct, zlib
    def create_png(width, height, color):
        def chunk(ctype, data):
            c = ctype + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        raw = b''
        for y in range(height):
            raw += b'\x00' + bytes(color) * width
        return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
    with open('/tmp/agentshield-logo.png', 'wb') as f:
        f.write(create_png(240, 240, (0x00, 0xd4, 0xaa)))
    print('Logo created with stdlib')
PYEOF
```

**Upload logo:**
- Click the PH image upload area (the dotted box or "Add logo" button) by element index
- A macOS native file dialog opens
- Use **foreground** `type` to type the path: `/tmp/agentshield-logo.png`
- Press `return` to confirm
- Per the skill, native dialogs DO accept foreground keystrokes

**Generate and upload screenshots** (same process):
1. Capture the eval page or risk calculator from the live site
2. Save as PNG
3. Upload via file dialog

### Step 4: THE HARD WALL, Launch Tags

**Problem:** The launch tags autocomplete/combobox React component cannot be bypassed with JS, foreground type, or any known technique. The PH form's "Next step" button stays disabled until at least one tag is selected.

**Strategy, attempt these ONCE each, then escalate:**

**Attempt A:** Use `set_value` on the combobox input:
```
computer_use action='set_value' element=N value='Developer Tools'
```
(Find the element index from the capture.)

**Attempt B:** Use foreground type on the combobox, then `return`:
```
computer_use action='type' text='Developer Tools' delivery_mode='foreground'
computer_use action='key' keys='return' delivery_mode='foreground'
```

**Attempt C:** Try JavaScript to find and interact with the combobox's underlying input:
```javascript
// The combobox likely uses a hidden input or contenteditable
var inputs = document.querySelectorAll('input[role="combobox"], input[aria-autocomplete]');
if (inputs.length > 0) {
  var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  s.call(inputs[0], 'Developer Tools');
  inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
  inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
}
```

**If ALL 3 fail:** The escape hatch is presenting the browser window to the user with a single action:
- Fill EVERYTHING else via JS injection
- Capture the form showing all fields populated
- Then say: "The launch tags field needs one tag typed. Type 'Developer Tools' and press Enter. Then I'll submit."
- **After the user types the tag**, capture again, verify the Next button is enabled, and click it.

### Step 5: Review and Submit
- Click "Next step" or "Continue"
- On the review page, capture and verify
- Click "Submit" or "Launch"
- **Capture the confirmation page and record the exact URL** (e.g., `producthunt.com/posts/agentshield-2`)

### Step 6: Add PH badge to landing page
Once you have the real PH URL, patch `public/index.html` to add the badge near the "As featured on" strip:
```html
<a href="REAL_PH_URL" target="_blank" style="display:inline-block;margin-left:12px">
  <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=POST_ID" alt="Featured on Product Hunt" width="160" height="34" />
</a>
```
Then:
```bash
cd /Users/sipi/agentshield && fly deploy
```

---

## PHASE 4: POST GITHUB DISCUSSION COMMENTS (10 min)

### Context
Drafts at `/Users/sipi/agentshield/content/outreach-comments-2026-08-11.md`. GitHub Discussions use the GraphQL API, `gh api graphql` works for this.

### Step 1: Post on Gemini CLI Discussion #4472

Read COMMENT 1 from the drafts file. Then:

```bash
# Get the discussion node ID
DID=$(gh api graphql -f query='
query($owner:String!,$repo:String!,$num:Int!) {
  repository(owner:$owner,name:$repo) {
    discussion(number:$num) { id }
  }
}' -f owner='google-gemini' -f repo='gemini-cli' -f num=4472 --jq '.data.repository.discussion.id')

echo "Discussion ID: $DID"

# Post the comment
gh api graphql -f query='
mutation($did:ID!,$body:String!) {
  addDiscussionComment(input:{discussionId:$did,body:$body}) {
    comment { id url }
  }
}' -f did="$DID" -f body="@/tmp/gemini-comment-body.txt"
```

### Step 2: Post on Copilot Discussion #192948

Same pattern but `owner='orgs'`, `repo='community'`, `num=192948`.

### Step 3: Post on Copilot Discussion #198015

Same pattern, `num=198015`.

Read the draft body from `outreach-comments-2026-08-11.md` for each. If a specific draft doesn't exist for #198015, craft a comment based on the thread context.

**Important:** GraphQL mutations can fail if the body contains special characters. Escape them properly or write the body to a temp file first.

---

## PHASE 5: REDDIT DRAFTS VIA COMET (10 min)

### Context
Reddit account: `u/Worth_Wealth_6811`. Browser: Comet. Safe subreddits only (user is banned from r/SaaS, r/Entrepreneur, r/startups, r/SideProject).

### Step 1: Check Comet Reddit session
```bash
open -a Comet "https://www.reddit.com"
```
Capture with `computer_use action='capture' mode='som' app='Comet'`.

Check: do you see a logged-in user (avatar in top-right, karma count)? If yes → proceed. If "Log In" button → blocked (note in final report).

### Step 2: Check for fresh radar drafts
```bash
ls -la /Users/sipi/.hermes/profiles/architector/cron/output/c52aa796f78f/ 2>/dev/null || echo "No output yet"
cat $(ls -t /Users/sipi/.hermes/profiles/architector/cron/output/c52aa796f78f/*.md 2>/dev/null | head -1) 2>/dev/null | head -80
```
Note: the spend radar is `c52aa796f78f` in the **architector** profile, its output is NOT under `~/.hermes/cron/output/`. Telegram delivery has been failing with a 401 (masked bot token), so read the on-disk report.

### Step 3: Post on relevant subreddits
For each draft from the radar that's in a SAFE subreddit:
1. Navigate to the post URL: `open -a Comet "<url>"`
2. Find the comment box element (may require scrolling)
3. Click the comment box by element index
4. Use foreground `type` to enter the comment text
5. Click "Comment" or "Reply" button
6. Capture to verify the comment appears

**Per macos-browser-driving skill Section 4:** Chromium-based browsers (Comet) may return "delivered 0 of N" for `type` in background mode. Use `delivery_mode='foreground'` for typing into Comet.

**Per skill Section 6:** Do NOT use AppleScript for clicks (blocked). Use element-index clicks from SOM captures.

---

## PHASE 6: FINAL VERIFICATION & COMMIT (5 min)

```bash
# Verify DNS
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short

# Verify PH badge on landing page
curl -s https://agentshield.fly.dev/ | grep -c "producthunt"

# Verify cron pipeline
# Run cronjob list and show all 8 jobs

# Verify tests
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py

# Verify eval
curl -s https://agentshield.fly.dev/eval

# Commit
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 7: DNS, PH, discussions, Reddit, autonomous execution" && git log --oneline -3
```

---

## FINAL REPORT

Produce a report with these exact sections:

```
## Phase 7, Final Autonomous Execution Report

### DNS (agentshield.sipiteno.com)
- Records added: [YES/NO, with screenshot filename or dig output]
- A record verified: [dig output]
- AAAA record verified: [dig output]
- Domain serves content: [HTTP code]

### Product Hunt
- Submitted: [YES/NO]
- PH URL: [exact URL after submission]
- Badge added to landing page: [YES/NO]
- Images uploaded: [count]

### GitHub Discussions
- Gemini CLI #4472: [POSTED/FAILED], [URL]
- Copilot #192948: [POSTED/FAILED], [URL]  
- Copilot #198015: [POSTED/FAILED], [URL]

### Reddit
- Session active: [YES/NO]
- Posts made: [count, subreddits]
- Blocked by login: [YES/NO]

### Quality
- Tests: [count]/14
- Eval: [count]/50
- Cron jobs: [count] active
- Health: [ok/error]

### Human Actions Still Required
- [ONLY list what truly could not be automated after exhausting ALL paths. For each, provide exact copy-paste instructions.]
```
