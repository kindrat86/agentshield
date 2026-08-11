# AGENTSHIELD PHASE 6: CLOSE THE GAP TO REVENUE

## ⚠️ MANDATORY: Read this entire document before taking ANY action.

---

## CONTEXT

AgentShield is a firewall for AI agent spending. Python 3.11 stdlib, zero deps, 50/50 eval gym. Deployed at `https://agentshield.fly.dev`. The product is real and working. The funnel infrastructure is complete — all 8 cron jobs exist and run.

*Corrected 2026-08-11: this paragraph previously claimed the nurture and spend-radar crons "were FABRICATED (the IDs 81a667e2e65e and 5a5c1e22533b do not appear in `cronjob list`)." That was profile-blindness, not fabrication — both jobs existed the whole time in the `architector` profile as `707dd2d06308` (nurture) and `c52aa796f78f` (spend-radar), invisible to `hermes cron list`. The IDs `81a667e2e65e` / `5a5c1e22533b` were later-created duplicates in the `default` profile; they have since been deleted. Do not recreate them.*

Your job: execute everything that CAN be done autonomously, and clearly separate what CAN be done from what requires the human (Maryan).

### Project Layout
```
/Users/sipi/agentshield/
├── core/           # Engine, API, store, auth, licensing
├── public/         # Landing, dashboard, blog, risk-calc, comparisons/
├── plugins/        # langchain/, crewai/
├── scripts/        # nurture_sequence.py, spend_radar.py, ...
├── tests/          # run_tests.py (14), eval_gym.py (50)
├── content/        # PH listing, Dev.to, HN posts
├── outreach/       # Leads, dream100
├── run_app.py      # Entrypoint
└── README.md
```

### Key Credentials
- **Resend API:** `REDACTED_RESEND_KEY` (full perms, from: sales@sipiteno.com, BCC: sales@sipiteno.com)
- **Fly.io app:** `agentshield`
- **GitHub repo:** `kindrat86/agentshield`
- **Telegram delivery:** `telegram:369633431`
- **Stripe Dev price ID:** `price_1U31cUCwGoUDklRe41V2eDvn`

### Current REAL Cron Jobs — all in the `architector` profile
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
**TOTAL: 8 jobs**, all under `~/.hermes/profiles/architector/cron/`, all verified running as of 2026-08-11.

⚠️ These are **invisible to `hermes cron list`**, which only shows the active (`default`) profile. Do not conclude they are missing or fabricated — see Phase 1 of `PHASE7-AUTONOMOUS-EXECUTION.md` for the cross-profile check.

*Corrected 2026-08-11: this section previously read "TOTAL: 6 jobs. The nurture and spend-radar jobs DO NOT EXIST." Both exist and both ran successfully that day (`707dd2d06308` at 15:06, `c52aa796f78f` at 15:09).*

---

## VERIFICATION PROTOCOL (Anti-Fabrication Rule)

After creating ANY cron job, you MUST include the ACTUAL output of `cronjob list` in your final report. The output must show these specific fields for every job: `job_id`, `name`, `schedule`, `last_status`. If you claim a job was created but it's not in the list, your entire report will be treated as fabricated. Do NOT invent IDs — show the real ones.

---

## PHASE A: CREATE THE MISSING CRON JOBS (Real This Time)

### A1. Schedule the Email Nurture Cron
The script exists at `/Users/sipi/agentshield/scripts/nurture_sequence.py`. It needs to run daily at 09:00.

Use the `cronjob` tool:
```
action='create'
name='agentshield-nurture'
schedule='0 9 * * *'
prompt='Run the AgentShield nurture email sequence. Execute: cd /Users/sipi/agentshield && python3.11 scripts/nurture_sequence.py. Report how many emails were sent and to whom. The script reads from the SQLite DB agentshield.db, finds new email captures, and sends them Day-1 through Day-5 nurture emails via Resend.'
workdir='/Users/sipi/agentshield'
deliver='telegram:369633431'
```

After creation, run `cronjob list` and capture the real job_id. Do NOT make one up.

### A2. Schedule the Spend Radar Cron
The script exists at `/Users/sipi/agentshield/scripts/spend_radar.py`. Schedule it daily at 12:00.

Use the `cronjob` tool:
```
action='create'
name='agentshield-spend-radar'
schedule='0 12 * * *'
prompt='Run the AgentShield spend radar to find developers complaining about AI agent costs. Execute: cd /Users/sipi/agentshield && python3.11 scripts/spend_radar.py. The script searches GitHub for cost-related issues, finds developers who had billing surprises, and outputs a structured report of leads with draft comments. Deliver the full output.'
workdir='/Users/sipi/agentshield'
deliver='telegram:369633431'
```

After creation, run `cronjob list` and capture the real job_id.

### A3. Verify Both Jobs
Run `cronjob list` and confirm you now have 8 total jobs (6 original + 2 new). Both new jobs should be `enabled: true` with `state: scheduled`.

---

## PHASE B: DNS & DOMAIN — What Maryan Must Do

The Fly.io certificate for `agentshield.sipiteno.com` was created. But DNS records must be added to Cloudflare for it to work.

### B1. Verify Cert Status
```bash
fly certs list -a agentshield
```
Check if `agentshield.sipiteno.com` shows `status: Ready` or `status: Pending`. If it's pending, the DNS records haven't been added yet.

### B2. Produce the Exact DNS Instructions
Output these records for Maryan to add in Cloudflare (sipiteno.com → DNS → Records):

```
Type: A     Name: agentshield    Value: 66.241.125.16    TTL: Auto
Type: AAAA  Name: agentshield    Value: 2a09:8280:1::166:9212:0    TTL: Auto
```

If `fly certs list` shows different IPs, use those instead. These are Fly.io's shared anycast IPs and may vary.

### B3. Explain What Happens After DNS
Once Maryan adds those records:
- Wait 2-5 minutes for DNS propagation
- Fly.io auto-verifies the cert within ~10 minutes
- `https://agentshield.sipiteno.com` starts serving the AgentShield landing page
- The landing page should auto-detect the domain and show `agentshield.sipiteno.com` in CTAs

---

## PHASE C: PRODUCT HUNT LAUNCH PREPARATION

### C1. Verify the PH Listing Content
Read `/Users/sipi/agentshield/content/producthunt-listing.md` and verify:
- Tagline (40 chars max): "A firewall for AI agent spending" — counts the characters
- Description (260 chars max): Check character count
- Maker comment: Complete and compelling
- Screenshot references: Are the URLs correct?

### C2. Check PH Name Collision
Search Product Hunt to confirm `agentshield` is taken:
```bash
web_search "producthunt.com posts agentshield"
```
If tomsun28's tool still occupies the URL, suggest naming variations for Maryan:
- "AgentShield — AI Agent Spend Firewall" (emphasize differentiation)
- "AgentShield — Stop AI Agents From Burning Your Budget"

### C3. Create PH Launch Day Brief
Create `/Users/sipi/agentshield/content/ph-launch-checklist.md` with:
- Exact submission URL: https://www.producthunt.com/posts/new
- What to paste in each field
- Suggested launch time: Tuesday-Thursday 00:01 PST (09:01 Greece time)
- Post-launch: immediately note the real PH URL, then we add the badge

### C4. Prepare the PH Badge
Once we know the real PH URL (after Maryan submits), the badge code is:
```html
<a href="https://www.producthunt.com/posts/AGENTSHIELD-SLUG-HERE" target="_blank">
  <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=POST_ID" alt="AgentShield on Product Hunt" width="250" height="54" />
</a>
```
We cannot add this yet because we need the post ID. Create a placeholder comment in `/Users/sipi/agentshield/public/index.html` where the badge will go.

---

## PHASE D: ORGANIC DISTRIBUTION PUSH

### D1. Dev.to Engagement
We have 2 published articles. Check them:
```bash
web_extract "https://dev.to/maryan_k_bef6cf83fa64e809"
```

For each article, check:
- Number of reactions, comments, reads
- Are there unanswered comments? If so, draft replies

Read `/Users/sipi/agentshield/content/devto-comments.md` — these are draft comments for OTHER people's articles to drive traffic. But Maryan must post them manually (Dev.to has anti-bot protections).

### D2. GitHub Star Campaign
```bash
cd /Users/sipi/agentshield
# Check current stars
gh repo view kindrat86/agentshield --json stargazerCount
```

To increase stars:
1. Post in relevant GitHub Discussions (NOT issues — discussions are for community)
2. Target: LangChain discussions, OpenAI Cookbook, CrewAI community
3. Post template: genuine contribution first, AgentShield mention second

### D3. Reddit Draft Comments
Read `/Users/sipi/agentshield/content/hn-post.md` and any Reddit draft content.
Search Reddit (safe subreddits only: r/datasets, r/juststart, r/devops, r/programming, r/MachineLearning, r/OpenAI) for recent posts about:
- AI agent costs
- OpenAI billing surprises
- Claude API pricing complaints
- LangChain/LangSmith cost discussions

For each found, draft a helpful comment. Save to `/Users/sipi/agentshield/content/reddit-drafts-$(date +%Y%m%d).md`.

**CRITICAL:** DO NOT POST on Reddit. User is BANNED from several subreddits (r/SaaS, r/Entrepreneur, r/startups, r/SideProject). Only DRAFT comments. Maryan posts them from u/Worth_Wealth_6811.

---

## PHASE E: CODE & DEPLOYMENT VERIFICATION

### E1. Test Comparison Pages
```bash
# Verify both comparison pages serve complete HTML with CTA
curl -s https://agentshield.fly.dev/comparisons/helicone | grep -c "Risk Calculator\|Try it free\|AgentShield"
curl -s https://agentshield.fly.dev/comparisons/langsmith | grep -c "Risk Calculator\|Try it free\|AgentShield"
```
Both should return counts > 0. If either returns 0, the page needs fixing.

### E2. Test Plugin Imports
```bash
cd /Users/sipi/agentshield
python3.11 -c "
import sys
sys.path.insert(0, 'plugins/langchain')
from agent_shield_callback import AgentShieldCallback
print('LangChain plugin: OK')
"
python3.11 -c "
import sys
sys.path.insert(0, 'plugins/crewai')
from agent_shield_tool import shield_tool
print('CrewAI plugin: OK')
"
```
Both must print "OK". If either fails, fix the import errors.

### E3. Run Full Test Suite
```bash
cd /Users/sipi/agentshield
LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1
```
Must show "Ran 14 tests ... OK".

### E4. Verify Eval Gym Live
```bash
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['passed']}/{d['total']} passed\")"
```
Must print "50/50 passed".

### E5. Deploy to Fly.io
If any files changed:
```bash
cd /Users/sipi/agentshield && fly deploy
```

### E6. Git Commit
```bash
cd /Users/sipi/agentshield
git add -A
git commit -m "Phase 6: nurture + radar crons scheduled, DNS brief, PH prep, Reddit drafts"
```

---

## PHASE F: PRODUCE THE HUMAN HANDOFF

At the end of your run, produce a clean summary. It must contain:

### Section 1: What Was Done (with real evidence)
- Cron jobs created with REAL IDs (paste output of `cronjob list`)
- Files modified, created, or fixed
- Git commit hash
- Deploy status

### Section 2: What Maryan Must Do (exact copy-paste instructions)
```
🚨 MARYAN ACTION REQUIRED:

1. ADD DNS RECORDS (Cloudflare → sipiteno.com → DNS):
   Type: A     Name: agentshield    Value: 66.241.125.16
   Type: AAAA  Name: agentshield    Value: 2a09:8280:1::166:9212:0
   (Wait 10 min, then https://agentshield.sipiteno.com goes live)

2. SUBMIT PRODUCT HUNT:
   - Go to: https://www.producthunt.com/posts/new
   - Name: "AgentShield — AI Agent Spend Firewall"
   - Tagline: "A firewall for AI agent spending"
   - Content: Copy from /Users/sipi/agentshield/content/producthunt-listing.md
   - After submission, TELL ME the new URL so I can add the badge

3. POST REDDIT COMMENTS (from u/Worth_Wealth_6811):
   - [Link to draft file you created]
```

### Section 3: Traffic Funnel Status
- Landing page: [URL + status]
- Comparison pages: [both URLs + 200 status]
- Email capture: [URL + test result]
- Cron pipeline: [total jobs, all enabled]
- Risk calculator: [URL + status]

---

## CRITICAL FINAL STEP

After completing Phase A and verifying the cron jobs exist, send yourself a final message to Telegram as a test:
```bash
# Use the send_message tool or curl to Resend
```
Confirm delivery works. Then produce the final handoff report.

---

## DO NOT:
- Fabricate cron job IDs — show real `cronjob list` output
- Post on Reddit or Product Hunt (Maryan must do this)
- Change the core engine, store, or auth code
- Remove or downgrade the free tier
- Add pip dependencies without documenting them
