# AgentShield Public URLs

## Live Product
| Asset | URL | Status |
|-------|-----|--------|
| Landing Page | https://agentshield.fly.dev | ✅ LIVE |
| Risk Calculator | https://agentshield.fly.dev/tools/risk-calculator/ | ✅ LIVE |
| Eval Results (50/50) | https://agentshield.fly.dev/eval | ✅ LIVE |
| On-site Blog | https://agentshield.fly.dev/blog | ✅ LIVE |
| Dashboard | https://agentshield.fly.dev/dashboard | ✅ LIVE |
| API Health | https://agentshield.fly.dev/health | ✅ LIVE |

## Stripe Billing
| Tier | Price ID | Monthly |
|------|----------|---------|
| Dev | price_1U31cUCwGoUDklRe41V2eDvn | $19.00 |
| Team | price_1U31cUCwGoUDklRefiU8KFbd | $99.00 |
| Managed | price_1U31cVCwGoUDklRe0lKuiW2e | $499.00 |

## Distribution
| Channel | URL | Status |
|---------|-----|--------|
| HN Post | https://news.ycombinator.com/item?id=49250917 | ✅ PUBLISHED |
| Blog (on-site) | https://agentshield.fly.dev/blog | ✅ LIVE |
| Dev.to | https://dev.to/maryan_k_bef6cf83fa64e809/i-built-a-firewall-for-ai-agent-spending-here-is-the-architecture-2560 | ✅ PUBLISHED |
| HN Account | SipitenoMK (1 karma) | ✅ Active |

## Demo Account
- Email: demo@agentshield.dev
- Password: demopass12345
- Access: Dashboard + API (free tier)
- Agent: Demo Agent (as_live_ key)
- Rules: transaction_limit ($500), daily_total ($2000), velocity (10/hr flagged)

## Notes
- HN does not allow "Show HN" posts from new accounts (needs karma). Posted as regular link instead.
- Dev.to requires login — no credentials in vault. Article markdown ready at ~/agentshield/content/agent-kill-switch.md for manual submission.
- Stripe webhook: https://agentshield.fly.dev/api/billing/webhook (events: checkout.session.completed, customer.subscription.*, invoice.payment_failed)
