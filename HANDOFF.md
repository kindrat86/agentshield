# AgentShield — Handoff Document

**Last updated:** August 11, 2026
**Status:** BUILD COMPLETE → DISTRIBUTION IN PROGRESS → MONITORING ACTIVE

---

## Product

**AgentShield** is a per-transaction spend firewall for autonomous AI agents. It evaluates each API call against configurable rules before it executes, blocking runaway spending in under 1ms.

- **URL:** https://agentshield.fly.dev
- **Stack:** Python 3.11 stdlib only (zero runtime dependencies)
- **Storage:** SQLite WAL mode, multi-tenant isolation via `account_id` scoping
- **Licensing:** HMAC-SHA256 offline signed keys
- **Auth:** PBKDF2-HMAC-SHA256, 200k iterations, session cookies
- **Eval gym:** 50/50 scenarios across 7 categories
- **E2E tests:** 14/14 including multi-tenant isolation
- **Performance:** 0.09ms average per evaluation

### Architecture
```
AI Agent → AgentShield Engine → API Provider (OpenAI etc)
                ↓
          Rule Store (SQLite WAL)
                ↓
          Dashboard (SSE feed)
```

## Billing

| Tier | Price | Agents | Rules | Daily Evals |
|------|-------|--------|-------|-------------|
| Free | $0 | 1 | 0 | 100 |
| Dev | $19/mo | 5 | 10 | 1,000 |
| Team | $99/mo | 20 | 50 | 5,000 |
| Managed | $499/mo | 100 | 200 | 50,000 |

- **Stripe Product:** `prod_V37saaKG2iMgAa`
- **Prices:** Dev `price_1U31cUCwGoUDklRe41V2eDvn`, Team `price_1U31cUCwGoUDklRefiU8KFbd`, Managed `price_1U31cVCwGoUDklRe0lKuiW2e`
- **Webhook:** `we_1U31cfCwGoUDklRe8jiQMeTH` → `/api/billing/webhook`
- **Demo account:** `demo@agentshield.dev` / `demopass12345`

## Deployment

- **Platform:** Fly.io, single machine, region `ams`, 256MB shared CPU
- **Dockerfile:** `python:3.11-slim`
- **Deploy command:** `fly deploy` from `~/agentshield/`
- **Git:** 13 commits on `main`, repo at `~/agentshield/`

## Distribution Status

| Channel | Status | Detail |
|---------|--------|--------|
| Product | ✅ LIVE | health OK, eval 50/50 |
| Dev.to | ✅ FIXED | 2 absolute links, 0 broken. API key: `.devto_api_key` |
| Twitter/X | ✅ POSTED | @Sipiteno via Comet browser |
| Reddit | ⚠️ Submitted | r/SideProject, may be shadow-removed |
| HN | ❌ Dead | karma 1, manual warm-up in progress |
| GitHub | ✅ 2 posts | AgentBudget #29, OpenClaw #42475 |
| SEO | ✅ Complete | OG + Twitter Card + JSON-LD on landing + blog |

## Autonomous Pipeline (Cron Stack)

All jobs deliver to Telegram (369633431).

| Job | ID | Schedule | Purpose |
|-----|----|----------|---------|
| Market scout v2 | `f10ab4dfbb8f` | Daily 09:00 | Find leads with AI agent cost problems |
| Lead processor | `6316254fafcc` | Daily 10:00 | Classify leads (customer/partner/community) |
| HN warm-up | `9d312b9723ad` | Daily 11:00 | 2-3 genuine comments on HN (SipitenoMK) |
| GitHub monitor | `a0af17ac3b08` | Daily 12:00 | Check for replies on AgentBudget/OpenClaw |
| Reddit warm-up | `479eebbfdef6` | Daily 14:00 | 3-5 genuine comments (u/Worth_Wealth_6811) |
| Weekly report | `82cf0728442c` | Monday 10:00 | Karma/stats check, flag re-post readiness |

## Outreach

### GitHub Outreach (POSTED ✅)
1. **AgentBudget/agentbudget #29** — Integration proposal for AgentShield rules engine
2. **openclaw/openclaw #42475** — Suggested AgentShield as external spend gateway

### B2B Drafts (awaiting manual submission)
1. **Portal26** — $6M healthcare token overrun case. Contact: portal26.ai
2. **CloudZero** — AI cost monitoring blog. Contact: cloudzero.com
3. **Nevermined** — Agent billing x402. Contact: nevermined.ai

### Market Scout Leads
8 real leads in `outreach/leads_2026-08-11.json` with dollar amounts ($300-$57K/year).

### Dream 100
100 contacts, 1 verified email (okhattab@mit.edu). Cold outreach to this tier is low-yield.

## Credentials & Secrets

- **Dev.to API key:** `~/agentshield/.devto_api_key` (key: `WiSeFSYGiGdpXoKd74vHoVBm`, article ID: 4363885)
- **Stripe key:** `global:STRIPE_SECRET_KEY` in `~/portfolio/config/vault_local.json`
- **Fly.io secrets:** LICENSING_MASTER_SECRET, STRIPE_SECRET_KEY, STRIPE_PRICE_DEV/TEAM/MANAGED, STRIPE_WEBHOOK_SECRET
- **Resend:** `global:RESEND_API_KEY` in vault (for email send pipeline)
- **GitHub:** Authenticated as `kindrat86` via `gh` CLI

## Accounts

| Platform | Username | Status |
|----------|----------|--------|
| GitHub | kindrat86 | Authenticated |
| HN | SipitenoMK | Karma 1, warming up |
| Reddit | u/Worth_Wealth_6811 | Warming up |
| Twitter/X | @Sipiteno | Posted |
| Dev.to | maryan_k_bef6cf83fa64e809 | 3 articles published |

## What Needs Human Action

1. **Submit B2B contact forms** for Portal26, CloudZero, Nevermined (drafts in `outreach/state.json`)
2. **Respond to GitHub replies** when AgentBudget/OpenClaw respond (github-monitor cron will alert via Telegram)
3. **Post to HN** after karma reaches 15+ (weekly-report cron will flag)
4. **Re-post to Reddit** after 40+ warm-up comments (weekly-report cron will flag)

## File Structure

```
~/agentshield/
├── core/           # Engine, store, licensing, auth, API
├── tests/          # Eval gym (50 scenarios), E2E tests (14)
├── public/         # Landing page, dashboard, risk calculator
├── content/        # Blog markdown, Reddit post body
├── outreach/       # Dream 100, leads, state.json, logs
├── scripts/        # Email extraction, send pipeline, warmup stats, random delay
├── Dockerfile
├── fly.toml
├── requirements.txt    # stdlib only
├── PUBLIC_URLS.md
└── HANDOFF.md          # this file
```
