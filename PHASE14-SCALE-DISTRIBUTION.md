# MISSION: Scale Distribution From Dozens to Thousands — Get AgentShield Discovered

## ⚠️ READ THIS FIRST

You are NOT posting more GitHub comments. The outreach loop is exhausted — 25 posts across 14 repos produced 5 conversations and 0 trial signups. That loop extracted its value. Stop running it.

Your job in this session is to **put AgentShield in front of thousands of developers** through channels that have built-in distribution: PyPI, Dev.to, awesome lists, and Hacker News.

---

## RULE ZERO: ZERO FABRICATION

Every action backed by tool output. Package published → show the PyPI URL. Article published → show the Dev.to URL. Awesome list PR submitted → show the PR URL. Never invent URLs, statuses, or IDs. Never touch memory. Never mention cron.

---

## WHAT EXISTS (verified — don't rebuild)

- **Product:** https://agentshield.fly.dev — 56/56 eval, 9 rule types, 14/14 tests
- **Content assets:** `/eval-gym-spec` (13KB), `/blog/zeroclaw-preflight-enforcement` (12KB)
- **GitHub:** https://github.com/kindrat86/agentshield (MIT)
- **25 outreach posts** across 14 repos, 5 active conversations
- **2 Dev.to articles** already published (architecture + OpenClaw)
- **Dev.to API key:** Available at `~/.hermes/.env` or in the Dev.to account settings. Account: `maryan_k_bef6cf83fa64e809`
- **Stripe:** Dev $19/mo, checkout wired
- **Plugins:** LangChain callback + CrewAI tool wrapper (in `plugins/`)

---

## PHASE 1: PUBLISH TO PyPI (30 min — highest permanent discovery value)

### Why This Matters
When a developer searches "how to control AI agent costs" on Google, they find blog posts. When they search `pip install agent cost` on PyPI, they find **nothing.** We need to be the first result.

### 1A. Create the package structure

```bash
mkdir -p /Users/sipi/agentshield/dist/agentshield
cd /Users/sipi/agentshield
```

Create `pyproject.toml`:
```toml
[project]
name = "agentshield"
version = "1.0.0"
description = "A firewall for AI agent spending. 7+ composable rules evaluated per-transaction in <1ms. Pure Python stdlib — zero dependencies."
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [{name = "Maryan Kondratyuk", email = "sales@sipiteno.com"}]
keywords = ["ai", "agent", "cost", "budget", "firewall", "spend", "openai", "anthropic", "langchain", "llm"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

[project.urls]
Homepage = "https://agentshield.fly.dev"
Repository = "https://github.com/kindrat86/agentshield"
Documentation = "https://agentshield.fly.dev/eval-gym-spec"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

Create `agentshield/__init__.py` that exports the engine and eval gym:
```python
"""
AgentShield — Firewall for AI Agent Spending

Pure Python 3.11 stdlib. Zero dependencies.
7+ composable rules evaluated per-transaction in <1ms.

Quick Start:
    from agentshield import SpendControlEngine
    
    engine = SpendControlEngine()
    result = engine.evaluate(transaction, rules, prior_transactions)
    # result['decision'] → 'APPROVED', 'BLOCKED', or 'FLAGGED'
"""
from .engine import SpendControlEngine
from .eval_gym import run_eval, SCENARIOS

__version__ = "1.0.0"
__all__ = ["SpendControlEngine", "run_eval", "SCENARIOS"]
```

Copy `core/engine.py` → `agentshield/engine.py`
Copy `tests/eval_gym.py` → `agentshield/eval_gym.py`

### 1B. Test the package locally

```bash
cd /Users/sipi/agentshield
python3.11 -m pip install --user build twine 2>/dev/null || pip3 install build twine
python3.11 -m build
```

Verify the built package:
```bash
# Test install in a temp venv
python3.11 -m venv /tmp/agentshield-test
source /tmp/agentshield-test/bin/activate
pip install dist/agentshield-1.0.0-py3-none-any.whl
python -c "from agentshield import SpendControlEngine, run_eval; results = run_eval(); print(f'{results[\"passed\"]}/{results[\"total\"]} passed')"
deactivate
```

The test must print `56/56 passed`. If it doesn't, fix the import paths before publishing.

### 1C. Publish to PyPI

Check if PyPI credentials exist:
```bash
cat ~/.pypirc 2>/dev/null | head -10
# Or check for API token in environment
env | grep -i PYPI
# Or check .env
grep -i pypi ~/.hermes/.env 2>/dev/null
```

If credentials exist:
```bash
python3.11 -m twine upload dist/agentshield-1.0.0*
```

If NO PyPI credentials exist:
- Create a PyPI account is NOT possible autonomously (requires email verification + 2FA)
- **Fallback:** Document the exact steps for Maryan:
  ```
  1. Go to https://pypi.org/account/register/
  2. Create account as "sipiteno" or "kindrat86"
  3. Go to Account Settings → API tokens → Add API token (scope: "Entire account")
  4. Copy the token (starts with pypi-)
  5. Run: TWINE_PASSWORD=pypi-YOUR_TOKEN TWINE_USERNAME=__token__ python3.11 -m twine upload dist/agentshield-1.0.0*
  ```

### 1D. Verify
After publishing:
```bash
pip install agentshield 2>&1
python3.11 -c "import agentshield; print(agentshield.__version__)"
```

Or if not published yet, verify the build artifacts exist:
```bash
ls -la /Users/sipi/agentshield/dist/
```

---

## PHASE 2: PUBLISH DEV.TO ARTICLE #3 (20 min — built-in distribution to 500+ developers)

### Why This Matters
Our 2 existing Dev.to articles are live and cross-linked. A third article about the Eval Gym Spec has the highest organic reach potential because it's **useful content**, not a product pitch.

### 2A. Read the Eval Gym Spec page
```bash
curl -s https://agentshield.fly.dev/eval-gym-spec | head -200
```

### 2B. Write the article

Create `/Users/sipi/agentshield/content/eval-gym-article.md`:

Title: "56 Test Scenarios for AI Agent Spend Control (MIT Licensed — Steal Them)"

Structure:
```markdown
---
title: 56 Test Scenarios for AI Agent Spend Control
published: true
tags: ai, agents, testing, opensource
cover_image: https://agentshield.fly.dev/eval-gym-spec-preview.png
---

## The Problem With Testing Agent Spend Controls

You built a cost-gating layer for your AI agents. You set a daily limit, a per-call cap, and a velocity check. How do you know it actually works?

Most teams test their spend controls by... not testing them. They set the limits, deploy, and wait for a billing surprise to reveal the gaps.

We wrote 56 labeled test scenarios — covering 9 spend-control rule types — and open-sourced them. MIT licensed. You can copy them into your test suite today.

## The 9 Rule Types

[For each rule type: 1-2 sentence description + the exact scenario that tests it + the expected outcome]

## Edge Cases That Will Bite You

[Cover the 5 edge cases: boundary values, missing fields, empty rulesets, priority ties, malformed inputs]

## How to Use These Scenarios

```python
pip install agentshield
from agentshield import run_eval
results = run_eval()
# 56/56 passed
```

Or just copy the scenarios from tests/eval_gym.py on GitHub.

## The Bigger Picture

Post-facto observability tools (LangSmith, Helicone) tell you what went wrong AFTER it happens. Pre-flight enforcement stops it BEFORE the API call executes. These 56 scenarios validate that your enforcement layer actually works.

Full spec: https://agentshield.fly.dev/eval-gym-spec
GitHub: https://github.com/kindrat86/agentshield
```

### 2C. Publish via Dev.to API

Check for API key:
```bash
grep -i "dev.*api\|DEV_TO\|devto" ~/.hermes/.env 2>/dev/null
```

If key exists:
```bash
curl -s -X POST https://dev.to/api/articles \
  -H "api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/devto-article.json
```

If no API key:
- Read the Dev.to publishing reference: `skill_view name="macos-browser-driving" file_path="references/devto-article-publishing.md"`
- Try publishing via Safari (logged in as maryan_k_bef6cf83fa64e809):
  ```bash
  open -a Safari "https://dev.to/enter"
  ```
  Then fill the editor via JS injection (native setter + dispatchEvent per the skill).

If API AND browser both fail: save the markdown and document the manual steps for Maryan.

---

## PHASE 3: AWESOME LIST SUBMISSIONS (15 min — permanent backlinks + discovery)

### Why This Matters
`awesome-ai-agents` has 50,000+ stars. Being listed there is a permanent, high-traffic discovery channel. These lists are bookmarked by every developer entering the AI agent space.

### 3A. Submit to awesome-ai-agents

```bash
# Read the contributing guidelines
gh repo view e2b-dev/awesome-ai-agents --json description 2>/dev/null || echo "Checking repo..."

# Create PR adding AgentShield
cat << 'BODY' > /tmp/awesome-pr-body.md
## What does this PR do?
Adds AgentShield to the Open Source section.

## AgentShield
- **Description:** A per-transaction spend firewall for AI agents. Evaluates every API call against 7+ composable rules in <1ms before it executes. Pure Python stdlib — zero dependencies.
- **GitHub:** https://github.com/kindrat86/agentshield
- **Website:** https://agentshield.fly.dev
- **License:** MIT
- **Why it belongs here:** AI agents make autonomous API calls with no budget awareness. AgentShield is the only open-source per-transaction enforcement layer (not observability — enforcement). 56/56 eval gym, self-hostable in 60 seconds.

## Category
Open Source AI Agent Tools
BODY
```

Find the correct README and submit a PR:
```bash
# Fork and clone
gh repo fork e2b-dev/awesome-ai-agents --clone=false 2>/dev/null

# Or create an issue requesting addition
gh issue create --repo e2b-dev/awesome-ai-agents \
  --title "Add AgentShield — AI Agent Spend Firewall (open source, MIT)" \
  --body-file /tmp/awesome-pr-body.md 2>&1
```

### 3B. Submit to other relevant lists

```bash
# awesome-langchain
gh issue create --repo gkammaris/awesome-langchain \
  --title "Add AgentShield — LangChain spend control callback" \
  --body "AgentShield provides a LangChain BaseCallbackHandler that intercepts LLM calls and evaluates cost against configurable rules before execution. MIT licensed. https://github.com/kindrat86/agentshield" 2>&1

# awesome-llm (if exists)
gh search repos "awesome-llm" --limit 5
```

### 3C. Add topics to GitHub repo
```bash
cd /Users/sipi/agentshield
gh repo edit kindrat86/agentshield \
  --add-topic ai-agents \
  --add-topic cost-management \
  --add-topic spend-control \
  --add-topic firewall \
  --add-topic openai \
  --add-topic anthropic \
  --add-topic langchain \
  --add-topic budget \
  --add-topic api-costs \
  --add-topic python 2>&1
```

Verify:
```bash
gh repo view kindrat86/agentshield --json repositoryTopics --jq '.repositoryTopics[].name'
```

---

## PHASE 4: CHECK ACTIVE CONVERSATIONS FOR REPLIES (10 min)

The 5 active conversations may have gotten replies since Phase 13. Check FIRST — a reply is worth 100 new posts.

```bash
# Check all threads for new comments
for url in \
  "https://github.com/openclaw/openclaw/issues/42475" \
  "https://github.com/zeroclaw-labs/zeroclaw/issues/2269" \
  "https://github.com/langchain-ai/langchain/issues/31647" \
  "https://github.com/rocketride-ai/rocketride/issues/1693" \
  "https://github.com/elitea-ai/elitea/issues/6010"; do
  echo "=== $(basename $(dirname $url))/$(basename $url) ==="
  gh issue view "$url" --comments 2>&1 | tail -20
  echo ""
done
```

**If anyone replied to the Phase 13 value-first gifts:**
- @yun520-1 responding to the eval gym spec → HIGHEST PRIORITY. Respond immediately.
- @theonlyhennygod responding to the ZeroClaw case study → HIGH PRIORITY. Respond.
- Any other reply → respond thoughtfully.

**If nobody replied:** That's expected. The asks are recent. Move to Phase 5.

---

## PHASE 5: SHOW HN POST (10 min — potential for massive reach)

### Why This Matters
Show HN is the #1 channel for developer tool discovery. A good Show HN post can reach 5,000-50,000 developers in 24 hours. Our HN account (SipitenoMK) has been warming up via cron and may have enough karma now.

### 5A. Check HN karma
```bash
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Karma: {d.get(\"karma\", 0)}')
print(f'Submitted: {len(d.get(\"submitted\", []))} items')
" 2>/dev/null || echo "HN API check failed"
```

### 5B. If karma >= 5: Attempt Show HN post

The previous HN post (item 49250917) was a regular link post that got no traction. A **Show HN** text post has better algorithmic treatment.

Draft the Show HN post:

Title: `Show HN: AgentShield – A firewall for AI agent spending (56 eval scenarios, Python stdlib)`

Body:
```
I built a per-transaction spend firewall for AI agents after one of my agents spent $2,800 in 60 seconds while I was asleep.

The problem: AI agents make autonomous API calls with zero budget awareness. A single infinite loop, retry storm, or context accumulation bug can drain your API budget before you wake up. Observability tools (Helicone, LangSmith) show you what happened AFTER the bill arrives. Nothing stops the transaction BEFORE it executes.

AgentShield sits between your agent and the API. Every transaction is evaluated against 7+ composable rules in under 1ms. First rule that matches wins.

Rule types:
- Transaction limits (block any single call over $X)
- Daily totals (cap cumulative spend per agent per day)
- Velocity detection (flag if N+ calls happen in a time window)
- Merchant allowlists (only allow approved API providers)
- Category blocks (block entire spending categories)
- Session budgets (session-scoped spend cap with decay tightening)
- Cascade cost estimation (pre-dispatch EV: call_cost + fail_probability × reversal_cost)

I wrote 56 labeled test scenarios for spend-control engines and open-sourced them (MIT). Eval gym: https://agentshield.fly.dev/eval

Pure Python 3.11 standard library. Zero dependencies. Runs on 256MB RAM. Self-hostable in 60 seconds.

GitHub: https://github.com/kindrat86/agentshield
Live demo + risk calculator: https://agentshield.fly.dev

The last two rule types (session_budget and cascade_cost) were suggested by an engineer at HeartFlow who's building production cost-gating. Happy to discuss the architecture or take feature requests.
```

### 5C. Post via Safari

```bash
open -a Safari "https://news.ycombinator.com/submit"
```
Capture. If logged in:
- Fill the title field via `type` (foreground mode)
- Fill the URL or text field
- Submit

If NOT logged in or karma too low:
- Save the draft to `/Users/sipi/agentshield/content/show-hn-post.md`
- Note: "HN post requires manual submission — karma may still be too low for Show HN"

---

## PHASE 6: VERIFY & COMMIT (5 min)

```bash
# Product health
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# Tests
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1 | tail -3

# Package build
ls -la /Users/sipi/agentshield/dist/ 2>/dev/null || echo "No dist/ — package not built"

# New content
ls -la /Users/sipi/agentshield/content/eval-gym-article.md 2>/dev/null
ls -la /Users/sipi/agentshield/content/show-hn-post.md 2>/dev/null

# GitHub topics
gh repo view kindrat86/agentshield --json repositoryTopics --jq '[.repositoryTopics[].name]' 2>/dev/null

# Commit
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 14: PyPI package build, Dev.to article, awesome list PRs, Show HN draft, topics added"
git log --oneline -3
```

---

## REPORT FORMAT

```
## Phase 14 — Scale Distribution Report

### PyPI Package
- Package built: [YES / NO]
- Local test (56/56): [YES / NO]
- Published to PyPI: [YES / NO — include URL if YES]
- If not published: [exact steps for Maryan]

### Dev.to Article #3
- Article written: [YES / NO]
- Published via API: [YES / NO — include URL if YES]
- If not published: [exact steps for Maryan]

### Awesome List Submissions
| List | Issue/PR | URL | Status |
|------|----------|-----|--------|
| awesome-ai-agents | ... | ... | Open/Merged |
| awesome-langchain | ... | ... | Open/Merged |

### GitHub Topics
- Added: [count] topics
- Topics: [list]

### Active Conversation Replies
| Thread | Person | Replied? | Action |
|--------|--------|----------|--------|
| OpenClaw #42475 | @yun520-1 | Yes/No | ... |
| ZeroClaw #2269 | @theonlyhennygod | Yes/No | ... |

### Show HN
- HN karma: [number]
- Post submitted: [YES / NO — include URL if YES]
- If not submitted: [reason]

### Quality
- Health: [ok/error]
- Eval: [N]/56
- Tests: [N]/14
- Git: [hash]

### Distribution Reach Estimate
| Channel | Estimated Reach | Status |
|---------|----------------|--------|
| GitHub comments (25 posts) | ~500 viewers | Exhausted |
| Dev.to article | ~500-5000 readers | [Published/Drafted] |
| PyPI package | Permanent discovery | [Published/Built] |
| Awesome lists | ~50000+ stargazers | [Submitted] |
| Show HN | ~5000-50000 viewers | [Submitted/Drafted] |

### Human Actions Still Required
- [ONLY what truly couldn't be automated]
```

---

## HARD RULES

1. **KPI: Get AgentShield into 3+ channels with built-in distribution.** Not more comments. Channels that reach thousands.

2. **PyPI is the #1 priority.** `pip install agentshield` is the permanent discovery channel. If credentials block publishing, build the package and document exact steps for Maryan.

3. **Dev.to article #3 is the #2 priority.** It has built-in distribution via tags and feeds. The eval gym content is genuinely useful — not a pitch.

4. **Check active conversations FIRST.** If @yun520-1 or @theonlyhennygod replied, that's worth more than everything else combined.

5. **Never mention cron. Never touch memory. Never fabricate.**

6. **Accept publication blocks gracefully.** If PyPI needs email verification, say so. If Dev.to API key is missing, say so. Build everything, document the manual step.

7. **Every awesome list submission must follow the list's contribution guidelines.** Read the CONTRIBUTING.md before submitting.

8. **The Show HN post must be the best piece of writing in the session.** It's our one shot at thousands of developers. No typos. Clear structure. The $2,800 story hook. Technical depth. Links to live demo.
