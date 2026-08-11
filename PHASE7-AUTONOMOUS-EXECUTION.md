# MISSION: Zero-Human Autonomous Execution — Complete All Remaining AgentShield Tasks

## ⚠️ READ THIS ENTIRE DOCUMENT BEFORE ANY ACTION

You are an autonomous execution agent. The user has explicitly said: **"Maryan should not do anything."** Every task in this document must be completed by YOU, using whatever tools and workarounds are available. If a direct path is blocked, find the indirect path. Exhaust every automated path before even considering a fallback.

---

## CONTEXT

AgentShield is a firewall for AI agent spending. Python 3.11 stdlib, zero deps, 50/50 eval gym. Live at `https://agentshield.fly.dev`. 8 cron jobs verified running. 6 GitHub outreach posts live. Comparison pages live. Email nurture pipeline active. Spend radar finding leads daily.

### What Remains (ALL must be done autonomously)

| # | Task | Current Blocker | Autonomous Path |
|---|------|-----------------|-----------------|
| 1 | Add DNS records for `agentshield.sipiteno.com` | Requires Cloudflare dashboard | Drive Safari to Cloudflare, add A/AAAA records |
| 2 | Submit Product Hunt listing | Requires browser form + human GitHub auth | Drive Safari to PH, fill form via JS injection, one manual tag field may remain |
| 3 | Post 3 GitHub discussion comments | Discussions can't use `gh issue comment` | Use GitHub GraphQL API via `gh api graphql` |
| 4 | Post Reddit drafts | Requires u/Worth_Wealth_6811 account | Drive Comet browser to Reddit, post drafts |
| 5 | Clean contaminated memory | Fake cron IDs from GLM 5.2 | memory tool remove operations |
| 6 | Fix spend radar Telegram token | Bot token masked in .env | Find real token, add to script |

### Project Layout
```
/Users/sipi/agentshield/
├── core/           # Engine (262 lines), API (830 lines), store, auth, licensing
├── public/         # Landing, dashboard, blog, comparisons/, tools/risk-calculator/
├── plugins/        # langchain/, crewai/
├── scripts/        # nurture_sequence.py, spend_radar.py, ...
├── content/        # producthunt-listing.md, outreach-comments-2026-08-11.md, devto-comments.md
├── tests/          # 14 E2E tests, 50 eval scenarios
└── run_app.py
```

### Critical Credentials
- **Resend:** `REDACTED` (full perms, from: sales@sipiteno.com, BCC: sales@sipiteno.com)
- **GitHub:** Authenticated as `kindrat86` via `gh` CLI
- **Fly.io:** `agentshield` app
- **Product Hunt:** Signed in as Maryan K via GitHub
- **Reddit:** u/Worth_Wealth_6811
- **Cloudflare sipiteno.com:** Account is `mkondratyuk86@gmail.com` (Acct2) — NO API TOKEN. Must use Safari dashboard.

### Real Cron IDs — all in the `architector` profile
```
6f33fb6cd459 — agentshield-market-scout    — 09:00 daily
707dd2d06308 — agentshield-nurture         — 09:00 daily
5a5a7d42e61a — agentshield-lead-processor  — 10:00 daily
73198eb477c9 — hn-karma-warmup             — 11:00 daily
490d890b0e6a — agentshield-github-monitor  — 12:00 daily
c52aa796f78f — agentshield-spend-radar     — 12:00 daily
a0c2caef4e81 — reddit-karma-warmup         — 14:00 daily
1861dbcffbaf — warmup-weekly-report        — Mon 10:00
```
⚠️ **These are invisible to `hermes cron list`.** That command only shows the active (`default`) profile, which holds zero AgentShield jobs. Verify with the cross-profile snippet in Phase 1 — never with `hermes cron list` alone.

*Corrected 2026-08-11: this block previously listed a different set of 9 IDs (`8ed8a7d6126e`, `f10ab4dfbb8f`, `6316254fafcc`, `9d312b9723ad`, `a0af17ac3b08`, `81a667e2e65e`, `5a5c1e22533b`, `479eebbfdef6`, `82cf0728442c`) as "the real IDs." Those were duplicates in the `default` profile; they caused `TERMINAL_CWD` lock contention and have been deleted. Do not recreate them.*

### Critical DNS Records to Add
```
Type: A      Name: agentshield    Value: 66.241.125.16    TTL: Auto
Type: AAAA   Name: agentshield    Value: 2a09:8280:1::166:9212:0    TTL: Auto
```

---

## PHASE 1: VERIFY CRON JOBS (5 minutes)

The cron jobs have been a source of confusion across sessions. The cause is now known, and it is not fabrication.

**Hermes has TWO cron stores, and `hermes cron list` shows only the ACTIVE profile's jobs.** Reading one store makes the other's IDs look invented. Four consecutive sessions hit this and each concluded the other's list was hallucinated. Both lists were real. There is no `--profile` flag on `hermes cron`, so the only reliable check reads both stores directly.

- `~/.hermes/cron/` — **default** profile (currently active). Holds **zero** AgentShield jobs.
- `~/.hermes/profiles/architector/cron/` — **architector** profile. Holds **all 8** live AgentShield jobs.

### 1A. Enumerate BOTH cron stores
Do **not** use `hermes cron list` for verification — it is profile-blind:
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

Expect exactly these 8, all under `[profile: architector]`:
```
6f33fb6cd459 — agentshield-market-scout    — 09:00
707dd2d06308 — agentshield-nurture         — 09:00
5a5a7d42e61a — agentshield-lead-processor  — 10:00
73198eb477c9 — hn-karma-warmup             — 11:00
490d890b0e6a — agentshield-github-monitor  — 12:00
c52aa796f78f — agentshield-spend-radar     — 12:00
a0c2caef4e81 — reddit-karma-warmup         — 14:00
1861dbcffbaf — warmup-weekly-report        — Mon 10:00
```

**Do NOT recreate any of these in the default profile.** Duplicates of all 8 (plus a redundant `market-scout-v2` that clobbered the same `outreach/leads_$(date).json`) lived there until 2026-08-11. All nine shared `workdir: /Users/sipi/agentshield`, and two profile tickers contending for the same `TERMINAL_CWD` lock killed `agentshield-market-scout` with a 660s timeout. All nine were deleted; backups at `~/.hermes/cron/backups/*-predupe-20260811-1552`.

### 1B. Do not "clean" cron IDs out of memory
Earlier versions of this prompt told you to delete memory entries referencing `6f33fb6cd459`, `5a5a7d42e61a`, `73198eb477c9`, `490d890b0e6a`, `a0c2caef4e81`, `1861dbcffbaf`, `707dd2d06308`, `c52aa796f78f` as fabricated. **That instruction was wrong — those are the live IDs.** Do not act on it. Absence from `hermes cron list` is not absence from the system; check the other store first. See the memory entry `hermes-cron-list-is-profile-scoped`.

---

## PHASE 2: ADD DNS RECORDS VIA CLOUDFLARE DASHBOARD (15-20 minutes)

**Target:** Add A and AAAA records for `agentshield` to the `sipiteno.com` zone.

**The only path:** The `cloudflare-dns-operations` skill confirms that `sipiteno.com` is in Acct2 (`mkondratyuk86@gmail.com`) and NO API TOKEN exists for it. The ONLY way to add records is through the Cloudflare dashboard in Safari, where the mkondratyuk86@gmail.com Google session is available.

### 2A. Load the cloudflare-dns-operations skill
```
skill_view name="cloudflare-dns-operations"
```
Read the full skill. Pay special attention to:
- Section "Dashboard navigation & computer_use quirks"
- The reliable path: `open -a Safari "<url>"` from terminal
- The coordinate space calibration (scale factor for clicks)

### 2B. Load the macos-browser-driving skill
```
skill_view name="macos-browser-driving"
```
Read Section 1 (coordinate space mapping), Section 2 (window z-order), Section 5 (reliable navigation via `open`).

### 2C. Navigate to Cloudflare DNS for sipiteno.com

Step-by-step:

1. **Open Safari with the zone DNS page:**
   ```bash
   open -a Safari "https://dash.cloudflare.com/"
   ```
   Wait 3 seconds.

2. **Capture the page:**
   ```
   computer_use action='capture' mode='som' app='Safari'
   ```
   Look for "sipiteno.com" in the domains list. Click it by element index.
   
   **IMPORTANT:** If you see a login page (email/password fields), the session is not active. Look for "Continue with Google" and attempt to click it. If the Google accounts page is NOT AX-exposed (per the skill's warning), you may need to check if there's an active Safari session for mkondratyuk86@gmail.com. Check by opening Gmail:
   ```bash
   open -a Safari "https://mail.google.com"
   ```
   If Gmail loads showing an inbox for mkondratyuk86@gmail.com, the session is active. Go back to Cloudflare.

3. **Navigate to DNS records:**
   Once on the sipiteno.com zone page, find and click "DNS" in the left sidebar, then "Records".

4. **Add the A record:**
   - Click "Add record"
   - Type: A
   - Name: `agentshield`
   - IPv4 address: `66.241.125.16`
   - TTL: Auto
   - Proxy status: DNS only (grey cloud — turn OFF the orange cloud proxy)
   - Click Save

5. **Add the AAAA record:**
   - Click "Add record" again
   - Type: AAAA
   - Name: `agentshield`
   - IPv6 address: `2a09:8280:1::166:9212:0`
   - TTL: Auto
   - Proxy status: DNS only (grey cloud)
   - Click Save

**Filling DNS record fields on macOS:**
- Use `set_value` for dropdowns (type select)
- Use `type` for text fields — deliver in foreground mode if background returns 0 chars
- Verify every field write with a fresh capture
- The "Save" button is often a `<button>` element — click by element index after the form is complete

### 2D. Verify DNS Records Were Added
After saving both records, capture the DNS records list and verify both `agentshield` entries are visible.

### 2E. Verify DNS Propagation
```bash
# After 2-5 minutes:
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
```
If they return the expected IPs, DNS is working.

### 2F. Verify Fly.io Cert
```bash
fly certs list -a agentshield
```
The `agentshield.sipiteno.com` cert status should change from "Pending" to "Ready" or "Active" within ~10 minutes of DNS propagation.

### 2G. Verify the Domain Serves Content
```bash
curl -s -o /dev/null -w "%{http_code}" https://agentshield.sipiteno.com
```
Should return 200 once DNS propagates and the cert is active.

---

## PHASE 3: SUBMIT PRODUCT HUNT LISTING (20-30 minutes)

**Target:** Submit the AgentShield listing to Product Hunt autonomously.

**Content file:** `/Users/sipi/agentshield/content/producthunt-listing.md` — read this FIRST to get all the text.

### 3A. Load the PH form DOM reference
```
skill_view name="macos-browser-driving" file_path="references/producthunt-form-dom.md"
```
This contains the documented DOM structure of the PH submission form and field-by-field automation results.

### 3B. Navigate to PH submission page

Product Hunt login uses GitHub OAuth. You are signed in as Maryan K via GitHub.

1. **Open Safari to PH:**
   ```bash
   open -a Safari "https://www.producthunt.com/posts/new"
   ```
   Wait 3 seconds. Capture.

2. **If redirected to login page:**
   Look for "Sign in with GitHub" button. Click it. You may see a GitHub OAuth consent screen. Click "Authorize".

3. **Once on the submission form**, capture and identify all form fields.

### 3C. Fill the form using JavaScript injection

Per the `macos-browser-driving` skill Section 12, React-controlled forms on PH can be filled via JavaScript native setter + dispatchEvent. Use:

```bash
osascript -e 'tell application "Safari" to do JavaScript "
var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, \"value\").set;
var input = document.querySelector(\"[name=\\\"post[name]\\\"]\");
nativeSetter.call(input, \"AgentShield — AI Agent Spend Firewall\");
input.dispatchEvent(new Event(\"input\", { bubbles: true }));
input.dispatchEvent(new Event(\"change\", { bubbles: true }));
"'
```

**Field mapping (from the listing content):**
- **Name:** "AgentShield — AI Agent Spend Firewall" (note: emphasize "spend firewall" to differentiate from tomsun28's rollback tool)
- **Tagline (40 chars max):** "A firewall for AI agent spending" — COUNT the characters: 35 chars. If the form complains it's too short, use: "A firewall for AI agent spending — stop runaway costs"
- **Description (260 chars max):** Read from `producthunt-listing.md` — the full description. COUNT characters before submitting. If over 260, trim.
- **Website URL:** `https://agentshield.fly.dev` (or `https://agentshield.sipiteno.com` if DNS is propagated)
- **GitHub URL:** `https://github.com/kindrat86/agentshield`
- **Maker comment:** Read from `producthunt-listing.md` — the full "Maker Comment" section. Paste into the textarea.

**For textarea fields:**
```javascript
var taSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
var ta = document.querySelector("textarea[name=\"post[tagline]\"]");
taSetter.call(ta, "Your text here");
ta.dispatchEvent(new Event("input", { bubbles: true }));
```

### 3D. Handle the HARD WALL: Launch Tags

**CRITICAL WARNING from the skill:** The launch tags autocomplete/combobox field is a HARD WALL for automation. React's autocomplete components cannot be bypassed with ANY JavaScript technique. The "Next step" button will remain disabled until at least one tag is selected.

**The escape hatch:** Fill EVERY other field via JavaScript injection. Then:
1. Capture the form and verify all fields are populated
2. Present the browser window to the user with this exact instruction:
   > "One field left: type 'Developer Tools' in the launch tags box and press Enter. That's it — I'll handle everything else."
3. After the user types the tag and hits Enter, capture again, verify the "Next step" button is enabled, and click it.

**BUT FIRST, try these automated approaches (each ONCE, then fall back):**
1. Try `set_value` on the combobox input element
2. Try foreground `type` with the tag name followed by `return`
3. Try `click` on the first dropdown suggestion if one appears

If all 3 fail (the button stays disabled), use the escape hatch above. Do NOT spend more than 5 attempts on the combobox.

### 3E. Handle Image Upload

PH requires at least a logo (240x240). The listing content mentions this.

**Generate a programmatic logo:**
1. Create a simple 240x240 PNG with a shield icon using Python Pillow:
   ```bash
   cd /tmp && python3.11 -c "
   from PIL import Image, ImageDraw
   img = Image.new('RGB', (240, 240), '#0a0a0a')
   draw = ImageDraw.Draw(img)
   # Draw a simple green shield shape
   draw.polygon([(120, 20), (220, 50), (220, 130), (120, 220), (20, 130), (20, 50)], fill='#00d4aa', outline='#00d4aa')
   # Inner darker shield
   draw.polygon([(120, 50), (190, 70), (190, 125), (120, 190), (50, 125), (50, 70)], fill='#0a0a0a')
   # Dollar sign
   draw.text((105, 95), '\$', fill='#00d4aa')
   img.save('agentshield-logo.png')
   print('Logo created')
   "
   ```
   If Pillow is not installed: `pip3 install Pillow` (use a temp venv if needed, but Pillow is small).

2. **Upload the logo to PH:**
   The PH form has an image upload button. Click it — a native macOS "Paste URL" or file picker dialog opens. Per the skill Section 12 note, native dialogs CAN be filled with foreground `type`:
   - After clicking the upload button, a macOS file dialog opens
   - Use foreground `type` to type the file path: `/tmp/agentshield-logo.png`
   - Press `return` to confirm
   - The dialog closes and the image loads into PH

### 3F. Generate Screenshots

PH needs screenshots. Generate them programmatically or capture from the live site:

```bash
# Screenshot the risk calculator from the live site
# Use computer_use to capture it, or generate programmatically
```

Per the skill Section 13, programmatic image generation is available. Use the Pillow approach for a terminal-style screenshot showing eval results:

```bash
python3.11 << 'EOF'
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (800, 450), '#0a0a0a')
draw = ImageDraw.Draw(img)
# ASCII art header
# ... generate a clean screenshot showing eval 50/50
img.save('/tmp/agentshield-screenshot.png')
print('Screenshot created')
EOF
```

Upload screenshots the same way as the logo — click the upload area, type the path in the file dialog.

### 3G. Submit the Listing

Once all fields are filled and images uploaded:
1. Click "Next step" or "Continue"
2. On the review page, capture and verify everything looks correct
3. Click "Submit" or "Launch"
4. **CRITICAL: Capture the confirmation page.** Note the EXACT URL slug (e.g., `/posts/agentshield-2`).

### 3H. After Submission: Add PH Badge to Landing Page

Once you know the real PH URL:
```bash
# Read the current landing page
# Add the PH badge near the "As featured on" strip
# The badge code:
# <a href="REAL_PH_URL" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=POST_ID" alt="AgentShield on Product Hunt" width="250" height="54" /></a>
```

Patch `/Users/sipi/agentshield/public/index.html` to add the badge, then deploy:
```bash
cd /Users/sipi/agentshield && fly deploy
```

---

## PHASE 4: POST GITHUB DISCUSSION COMMENTS (10 minutes)

**Target:** Post the 3 drafted comments on GitHub Discussions.

**Drafts file:** `/Users/sipi/agentshield/content/outreach-comments-2026-08-11.md`

GitHub Discussions use a different API than Issues. The `gh issue comment` command doesn't work. Use the GraphQL API instead.

### 4A. Post on Gemini CLI Discussion #4472

Read the draft for COMMENT 1 from `outreach-comments-2026-08-11.md`.

Use the GitHub GraphQL API to add a discussion comment:

```bash
# First, get the discussion node ID
DISCUSSION_ID=$(gh api graphql -f query='
query {
  repository(owner: "google-gemini", name: "gemini-cli") {
    discussion(number: 4472) {
      id
    }
  }
}' --jq '.data.repository.discussion.id')

echo "Discussion ID: $DISCUSSION_ID"

# Then add the comment
COMMENT_BODY='...'  # Read from the drafts file
gh api graphql -f query='
mutation($discussionId: ID!, $body: String!) {
  addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
    comment {
      id
      url
    }
  }
}' -f discussionId="$DISCUSSION_ID" -f body="$COMMENT_BODY"
```

### 4B. Post on GitHub Copilot Discussion #192948

Same approach but for `orgs/community`:
```bash
gh api graphql -f query='
query {
  repository(owner: "orgs", name: "community") {
    discussion(number: 192948) {
      id
    }
  }
}'
```

### 4C. Post on GitHub Copilot Discussion #198015

Same approach for `orgs/community` discussion #198015.

Read the draft from `outreach-comments-2026-08-11.md` — if a specific draft doesn't exist for this one, craft a comment based on the thread's content (developers angry about Copilot billing costs).

---

## PHASE 5: POST REDDIT DRAFTS (15 minutes)

**Target:** Post the Reddit drafts from the spend radar on safe subreddits.

### 5A. Check for Drafts

The spend radar cron (`c52aa796f78f`, `architector` profile) may have delivered fresh drafts to Telegram. Check:
```bash
# Read the latest spend radar output
ls -la /Users/sipi/.hermes/profiles/architector/cron/output/c52aa796f78f/ 2>/dev/null || echo "No output dir found"
cat $(ls -t /Users/sipi/.hermes/profiles/architector/cron/output/c52aa796f78f/*.md 2>/dev/null | head -1) 2>/dev/null | head -80
```
Note: the output lives under the **architector** profile, not `~/.hermes/cron/output/`. Telegram delivery from this job has been failing with a 401 (masked bot token in `.env`), so the on-disk report is the reliable source.

### 5B. Drive Comet to Reddit

Per memory: "Comet for Reddit/X sessions." The Reddit account is u/Worth_Wealth_6811.

1. **Check if Comet is signed into Reddit:**
   ```bash
   open -a Comet "https://www.reddit.com"
   ```
   Wait 3 seconds. Capture with `computer_use action='capture' mode='som' app='Comet'`.
   
   If the page shows a logged-in user (avatar in top right), the session is active.
   If it shows "Log In", the session is not active. In that case:
   - This task is BLOCKED without the Reddit session
   - Skip to Phase 6
   - Note in final report: "Reddit: requires login to u/Worth_Wealth_6811"

2. **Identify SAFE subreddits only:**
   The user is BANNED from: r/SaaS, r/Entrepreneur, r/startups, r/SideProject.
   SAFE subreddits: r/datasets, r/juststart, r/devops, r/programming, r/MachineLearning, r/OpenAI.

3. **Post process:**
   - Navigate to the specific post URL from the radar report
   - Find the comment box (may be at the bottom or under a specific comment)
   - Click the comment box by element index
   - Use foreground `type` to paste the draft comment
   - Click "Comment" or "Reply" button

   **Per the macos-browser-driving skill:**
   - React textareas in Comet may require foreground delivery
   - `set_value` typically fails on React forms (no React event dispatch)
   - Use `type` in foreground mode for textareas
   - If type delivers 0 chars (known Chromium issue), try single key events

4. **Verify:** After posting, capture the page and verify the comment appears.

---

## PHASE 6: FIX SPEND RADAR TELEGRAM & GITHUB TOKEN (10 minutes)

The spend radar output identified two issues:
1. Telegram token is masked in `.env` → `401 Unauthorized`
2. Unauthenticated GitHub API → rate limiting after ~10 requests

### 6A. Fix Telegram Token

Check if a Telegram bot token exists:
```bash
# Check env vars
cat /Users/sipi/agentshield/.env 2>/dev/null
grep -r "TELEGRAM\|BOT_TOKEN" /Users/sipi/agentshield/scripts/spend_radar.py
```

If the token is masked but a real one exists somewhere, find it and add it to the script's config. If no real token exists, note this in the final report — the cron delivers via Hermes's built-in delivery mechanism (which does work), so Telegram delivery is a nice-to-have, not critical.

### 6B. Add GITHUB_TOKEN

The `gh` CLI is authenticated. Extract the token and add it to the spend radar script:
```bash
# The gh token can be used as a GITHUB_TOKEN env var
export GITHUB_TOKEN=$(gh auth token)
```

Patch the spend radar script to use this:
```bash
# Read the current script
read_file path="/Users/sipi/agentshield/scripts/spend_radar.py"
# Find where it makes GitHub API calls and add Authorization header if GITHUB_TOKEN is set
```

### 6C. Improve False-Positive Filter

The radar flagged `NikoPikoFriko/ai-usage-cost-tracker#1` as a false positive (internal PR review roster). Add a filter to exclude results matching:
- "comment only"
- "roster"
- "carrier PR"
- "review roster"
- PRs with only file-level comments (no issue body)

---

## PHASE 7: FINAL VERIFICATION & COMMIT

### 7A. Verify Everything

```bash
# DNS
dig agentshield.sipiteno.com A +short
dig agentshield.sipiteno.com AAAA +short
curl -s -o /dev/null -w "%{http_code}" https://agentshield.sipiteno.com

# Cron pipeline
# Run cronjob list and verify 8 jobs, all enabled

# Tests
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py

# Eval
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# Health
curl -s https://agentshield.fly.dev/health
```

### 7B. Commit All Changes

```bash
cd /Users/sipi/agentshield
git add -A
git commit -m "Phase 7: DNS added, PH submitted, discussions posted, radar fixes, badge deployed"
git log --oneline -3
```

### 7C. Deploy

```bash
cd /Users/sipi/agentshield && fly deploy
```

---

## FINAL REPORT FORMAT

At the end, produce a clean report:

```
## Phase 7 Complete — Autonomous Execution Report

### DNS (agentshield.sipiteno.com)
- Records added: YES/NO (with screenshot evidence)
- Propagation verified: YES/NO
- URL live: YES/NO (HTTP code)

### Product Hunt
- Submitted: YES/NO
- PH URL: [real URL after submission]
- Badge added to landing page: YES/NO
- Images uploaded: YES/NO (how many)

### GitHub Discussions
- Gemini CLI #4472: POSTED/FAILED (URL)
- Copilot #192948: POSTED/FAILED (URL)
- Copilot #198015: POSTED/FAILED (URL)

### Reddit
- Drafts posted: YES/NO (which subreddits)
- Blocked by login: YES/NO

### Spend Radar Fixes
- Telegram token: FIXED/NOT FOUND
- GitHub token: ADDED/NOT ADDED
- False positive filter: IMPROVED/NOT CHANGED

### Quality Gates
- Tests: 14/N
- Eval: 50/50
- Health: ok/error
- Deploy: live/error

### Manual Actions Still Required
- [List only what truly could not be automated, with exact instructions]
```

---

## ESCAPE HATCHES

If a task truly cannot be completed autonomously after exhausting ALL paths:

1. **DNS:** If Safari session is not logged into mkondratyuk86@gmail.com and Google login page is not AX-exposable → blocked. Ask Maryan to log in once, then retry.

2. **PH tags:** If the launch tags combobox blocks submission → the escape hatch is Maryan typing ONE tag. Everything else is done. Give exact instruction: "Type 'Developer Tools' and Enter."

3. **Reddit:** If Comet is not signed into u/Worth_Wealth_6811 → blocked. Ask Maryan to verify the session.

4. **GitHub Discussions:** GraphQL API should work. If it fails with a permissions error, try the REST API via `gh api repos/google-gemini/gemini-cli/discussions/4472/comments`.

**Rule: attempt every automated path at least once before falling back. Never assume a path is blocked without trying it.**
