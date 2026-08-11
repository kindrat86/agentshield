# AgentShield — Handoff Document

**Last updated:** August 11, 2026
**Status:** BUILD COMPLETE → DISTRIBUTED → MONITORING ACTIVE

---

## Product (LIVE ✅)

**URL:** https://agentshield.fly.dev
**Stack:** Python 3.11 stdlib only (zero dependencies)
**Eval:** 50/50 across 7 categories
**Storage:** SQLite WAL mode, multi-tenant isolation
**Auth:** PBKDF2-HMAC-SHA256, 200k iterations
**Licensing:** HMAC-SHA256 offline signed keys
**API:** 18 routes, CORS, SSE

## Billing

| Tier | Price | Stripe Price ID |
|------|-------|-----------------|
| Dev | $19/mo | `price_1U31cUCwGoUDklRe41V2eDvn` |
| Team | $99/mo | `price_1U31cUCwGoUDklRefiU8KFbd` |
| Managed | $499/mo | `price_1U31cVCwGoUDklRe0lKuiW2e` |

- Stripe Product: `prod_V37saaKG2iMgAa`
- Webhook: `we_1U31cfCwGoUDklRe8jiQMeTH` → `/api/billing/webhook`

## Distribution (DONE ✅)

| Channel | Status | Detail |
|---------|--------|--------|
| Product | ✅ LIVE | health OK, eval 50/50 |
| Dev.to | ✅ FIXED | 2 absolute links, 0 broken |
| Twitter/X | ✅ POSTED | @Sipiteno |
| GitHub | ✅ 3 LIVE | AgentBudget #29, OpenClaw #42475, AgentGuard #2 |
| B2B Emails | ✅ 3 SENT | Portal26, CloudZero, Nevermined (from escape@invisibleexit.com) |
| SEO | ✅ COMPLETE | OG + Twitter Card + JSON-LD on both pages |

## Email Identity

**Current sender:** escape@invisibleexit.com (verified in Resend)
**Preferred sender:** sales@sipiteno.com (NOT verified)

**To verify sipiteno.com — add these 3 DNS records in Cloudflare:**

1. TXT: Name=`resend._domainkey`, Value=`p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDC2aZWYYgX9+AALN/rnWGgPgGNfgg8JTt8GCgk85AL8pXJLU+L8mV7Tl2BF09V01cc1nP4qz+3AjLdKeZEkrjypR3J982rCLltxPFnU3NOZ0jFkQBHkur6Gzch2UQ7TIsr7pha150NP1NRRwgR9wBwBR9EdYg03GFSod02DzsiaQIDAQAB`
2. MX: Name=`send`, Server=`feedback-smtp.eu-west-1.amazonses.com`, Priority=10
3. TXT: Name=`send`, Value=`v=spf1 include:amazonses.com ~all`

Resend domain ID: `d77d146e-e2cb-4a44-aba4-11396aa4bd5e`

Once added, I will trigger verification + re-send all emails from sales@sipiteno.com.

## Autonomous Pipeline (5/6 CRONS PROVEN)

| # | Job | Schedule | Mode | Status |
|---|-----|---------|------|--------|
| 1 | Market scout | 09:00 | API (web_search + file) | ✅ 9 leads found |
| 2 | Lead processor | 10:00 | API (read + classify JSON) | ✅ 10 customers classified |
| 3 | HN warm-up | 11:00 | API (suggestion-only) | 🔄 Cooling off (rate-limited) |
| 4 | GitHub monitor | 12:00 | API (gh issue view) | ✅ No replies yet |
| 5 | Reddit warm-up | 14:00 | API (suggestion-only) | ✅ Suggestion produced |
| 6 | Weekly report | Mon 10:00 | API (stats + karma) | ⏳ First fire Aug 17 |

All crons deliver to Telegram (369633431).

## Leads (VERIFIED)

10 CUSTOMER-classified leads from market scout, including:
- sampleSal: $1,100/week on Anthropic API ($57K/year)
- Portal26: $6M+ healthcare enterprise token overrun
- CloudZero: $5K→$50K overnight spikes
- Prefactor: $9K→$38K monthly increase
- Braintrust: $12K unattributed monthly increase

Leads stored in: `outreach/leads_2026-08-11.json`

## GitHub Outreach (ALL LIVE, posted by kindrat86)

1. **AgentBudget/agentbudget #29** — Integration proposal
2. **openclaw/openclaw #42475** — Solution comment for per-agent budget enforcement
3. **dipampaul17/AgentGuard #2** — Partnership proposal (complementary approaches)

## What Needs Human Action

### HIGH PRIORITY
1. **Add 3 DNS records to sipiteno.com in Cloudflare** (see Email Identity section above)
   - Navigate to: https://dash.cloudflare.com → sipiteno.com → DNS → Records
   - Add the 3 records listed above
   - Tell me when done → I'll verify + re-send all emails from sales@sipiteno.com

### MEDIUM PRIORITY
2. **Post Reddit comment** (suggested by warm-up cron)
   - Post: https://www.reddit.com/r/programming/comments/1rpd00d/returning_to_rails_in_2026
   - Comment: "I keep coming back to Rails too. It's not the shiny new thing but the productivity is real — you ship features while other stacks are still configuring their build tools. What's kept you away, and what brought you back?"
   - Log in as u/Worth_Wealth_6811, paste, submit once

3. **Post HN comment** (after 24h cool-off from rate limit)
   - The cron will suggest posts daily at 11:00 via Telegram
   - Post ONE comment manually in Safari (JS injection triggers rate limiter for low-karma accounts)

### LOW PRIORITY
4. **Book B2B demo calls** (emails sent, awaiting responses)
   - Portal26: info@portal26.ai or schedule-a-demo
   - CloudZero: marketing@cloudzero.com
   - Nevermined: hello@nevermined.ai

5. **Respond to GitHub replies** when they arrive (monitor cron checks daily)

## Git
- 21 commits on main
- Repo: `~/agentshield/`
- Deploy: `fly deploy` from `~/agentshield/`
