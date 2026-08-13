# MISSION: Ship `pip install agentshield` + Awesome Lists + Show HN

## ⚠️ YOUR KPI: `pip install agentshield` must work by end of session

Nothing else matters. Not GitHub comments. Not Dev.to articles. Not cron jobs. Not memory. If `pip install agentshield && python3.11 -c "from agentshield import run_eval; print(run_eval()['passed'])"` prints `56`, the session is a success.

---

## RULE ZERO

Zero fabrication. Every claim backed by tool output. Package built → show the file listing. Published → show the PyPI URL. Awesome list PR → show the PR URL. If blocked, say so honestly and document exact steps for Maryan. Never mention cron. Never touch memory.

---

## WHAT EXISTS RIGHT NOW

- **Live product:** https://agentshield.fly.dev, 56/56 eval, 9 rule types, 14/14 tests
- **Engine:** `/Users/sipi/agentshield/core/engine.py`, `SpendControlEngine` class, pure stdlib (decimal, datetime)
- **Eval gym:** `/Users/sipi/agentshield/tests/eval_gym.py`, 56 scenarios, `SCENARIOS` list + `run_eval()` function
- **3 Dev.to articles** published (architecture, OpenClaw plugin, ZeroClaw case study)
- **29 GitHub posts** across 14 repos, 5 active conversations
- **Comparison pages:** `/comparisons/helicone`, `/comparisons/langsmith`
- **Eval gym spec:** `/eval-gym-spec` (13KB live page)
- **GitHub repo:** https://github.com/kindrat86/agentshield (MIT)
- **Dev.to account:** `maryan_k_bef6cf83fa64e809`

### What the Previous Session Missed
The Phase 14 prompt asked for PyPI, Dev.to, awesome lists, Show HN, and GitHub topics. The agent only did the Dev.to article. The other 4 tasks were not attempted. This session does ALL of them.

---

## TASK 1: BUILD AND PUBLISH THE PyPI PACKAGE (45 min, PRIORITY #1)

### 1A. Create the package directory structure

```bash
mkdir -p /Users/sipi/agentshield/pkg/agentshield
cd /Users/sipi/agentshield
```

### 1B. Create `pkg/pyproject.toml`

```bash
cat > /Users/sipi/agentshield/pkg/pyproject.toml << 'TOMLEOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "agentshield"
version = "1.0.0"
description = "A firewall for AI agent spending. 9 composable rules evaluated per-transaction in <1ms. Pure Python stdlib, zero dependencies."
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Maryan Kondratyuk", email = "sales@sipiteno.com"}
]
keywords = [
    "ai", "agent", "cost", "budget", "firewall", "spend",
    "openai", "anthropic", "langchain", "llm", "api-costs",
    "spend-control", "cost-management", "rate-limit", "token"
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Networking :: Firewalls",
]

[project.urls]
Homepage = "https://agentshield.fly.dev"
Repository = "https://github.com/kindrat86/agentshield"
Documentation = "https://agentshield.fly.dev/eval-gym-spec"
"Bug Tracker" = "https://github.com/kindrat86/agentshield/issues"
Changelog = "https://github.com/kindrat86/agentshield/blob/main/CHANGELOG.md"

[tool.setuptools.packages.find]
where = ["."]
TOMLEOF
```

### 1C. Create `pkg/agentshield/__init__.py`

This is what users import. It must export the engine and the eval gym runner.

```bash
cat > /Users/sipi/agentshield/pkg/agentshield/__init__.py << 'PYEOF'
"""
AgentShield, Firewall for AI Agent Spending
=============================================
Pure Python 3.11 stdlib. Zero dependencies.
9 composable rules evaluated per-transaction in <1ms.

Quick Start:
    >>> from agentshield import SpendControlEngine
    >>> engine = SpendControlEngine()
    >>> result = engine.evaluate(
    ...     transaction={"amount": 10.00, "merchant": "openai-api", "category": "llm_inference"},
    ...     rules=[{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
    ...     prior_transactions=[]
    ... )
    >>> result["decision"]
    'APPROVED'

Rule Types (9):
    - transaction_limit, block if a single transaction exceeds max_amount
    - daily_total      , block if cumulative daily spend exceeds max_daily
    - velocity         , flag if transaction count in rolling window exceeds max_count
    - merchant_allowlist, block if merchant is NOT in the allowed list
    - category_block   , block if category IS in the blocked list
    - session_budget   , session-scoped spend cap with optional decay tightening
    - cascade_cost     , pre-dispatch EV: call_cost + fail_probability × reversal_cost
    - edge_cases       , boundary values, malformed inputs, empty rulesets
    - clean_approval   , normal transactions that should pass

MIT Licensed. See: https://github.com/kindrat86/agentshield
"""

from .engine import SpendControlEngine
from .eval_gym import run_eval, SCENARIOS

__version__ = "1.0.0"
__author__ = "Maryan Kondratyuk"
__license__ = "MIT"
__all__ = ["SpendControlEngine", "run_eval", "SCENARIOS"]
PYEOF
```

### 1D. Copy engine and eval gym into the package

```bash
# Copy the engine, it's pure stdlib, no modifications needed
cp /Users/sipi/agentshield/core/engine.py /Users/sipi/agentshield/pkg/agentshield/engine.py

# Copy the eval gym
cp /Users/sipi/agentshield/tests/eval_gym.py /Users/sipi/agentshield/pkg/agentshield/eval_gym.py
```

### 1E. Fix the eval_gym import path

The eval gym currently imports `from core.engine import SpendControlEngine`. Inside the package it needs to be `from .engine import SpendControlEngine`.

Read the first few lines of the copied eval_gym.py:
```bash
head -25 /Users/sipi/agentshield/pkg/agentshield/eval_gym.py
```

Then patch the import line:
```bash
# Find the import line and fix it
sed -i '' 's/from core.engine import SpendControlEngine/from .engine import SpendControlEngine/' /Users/sipi/agentshield/pkg/agentshield/eval_gym.py 2>/dev/null || \
sed -i 's/from core.engine import SpendControlEngine/from .engine import SpendControlEngine/' /Users/sipi/agentshield/pkg/agentshield/eval_gym.py
```

Verify the fix:
```bash
head -25 /Users/sipi/agentshield/pkg/agentshield/eval_gym.py | grep "from"
```
Must show `from .engine import SpendControlEngine`.

### 1F. Create the package README

```bash
cat > /Users/sipi/agentshield/pkg/README.md << 'MDEOF'
# AgentShield, Firewall for AI Agent Spending

Stop runaway AI agents before they burn your budget. 9 composable rules evaluated per-transaction in under 1 millisecond. Pure Python 3.11 stdlib, zero dependencies.

## The $2,800 Wake-Up Call

At 3 AM, an AI agent made 21 API calls to a premium endpoint. Each cost $133. $2,800 gone in 60 seconds, while the developer slept.

AgentShield sits between your agent and the API. Every transaction is evaluated against your rules BEFORE it executes. First rule that matches wins. All in under 1ms.

## Install

```bash
pip install agentshield
```

## Quick Start

```python
from agentshield import SpendControlEngine

engine = SpendControlEngine()

# Define your spend-control rules
rules = [
    {"id": "r1", "type": "transaction_limit", "priority": 1,
     "params": {"max_amount": 500}, "action": "BLOCK"},
    {"id": "r2", "type": "daily_total", "priority": 2,
     "params": {"max_daily": 2000}, "action": "BLOCK"},
    {"id": "r3", "type": "velocity", "priority": 3,
     "params": {"window_minutes": 60, "max_count": 10}, "action": "FLAG"},
]

# Evaluate a transaction BEFORE the API call
result = engine.evaluate(
    transaction={
        "amount": 750.00,
        "merchant": "openai-api",
        "category": "llm_inference",
        "agent_id": "agent_1",
        "timestamp": "2026-08-11T10:00:00Z"
    },
    rules=rules,
    prior_transactions=[]
)

print(result["decision"])  # "BLOCKED", exceeds $500 limit
print(result["reason"])    # "Transaction amount $750.00 exceeds limit of $500.00"
```

## Rule Types (9)

| Rule | What it does |
|------|-------------|
| **Transaction Limit** | Block any single call over $X |
| **Daily Total** | Cap cumulative spend per agent per day |
| **Velocity** | Flag if N+ calls happen in a time window |
| **Merchant Allowlist** | Only allow approved API providers |
| **Category Block** | Block entire spending categories |
| **Session Budget** | Session-scoped spend cap with decay tightening |
| **Cascade Cost** | Pre-dispatch EV: call_cost + fail_probability × reversal_cost |
| **Edge Cases** | Boundary values, malformed inputs, empty rulesets |
| **Clean Approval** | Normal transactions that should pass |

## Eval Gym (56 Scenarios)

```python
from agentshield import run_eval

results = run_eval()
print(f"{results['passed']}/{results['total']} passed")
# 56/56 passed
```

## Tech Stack

- **Language:** Python 3.11+ (stdlib only, zero pip installs)
- **Monetary precision:** `decimal.Decimal` (never float)
- **Latency:** <1ms per evaluation
- **State:** Stateless engine, deterministic, testable, composable

## Links

- [GitHub](https://github.com/kindrat86/agentshield)
- [Live Demo + Risk Calculator](https://agentshield.fly.dev)
- [Eval Gym Spec (56 Scenarios)](https://agentshield.fly.dev/eval-gym-spec)
- [Full Architecture Deep-Dive](https://dev.to/maryan_k_bef6cf83fa64e809)

MIT Licensed. Built because budget alerts shouldn't arrive by email.
MDEOF
```

### 1G. Create LICENSE file

```bash
cp /Users/sipi/agentshield/LICENSE /Users/sipi/agentshield/pkg/LICENSE 2>/dev/null || \
cat > /Users/sipi/agentshield/pkg/LICENSE << 'LICEOF'
MIT License

Copyright (c) 2026 Maryan Kondratyuk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
LICEOF
```

### 1H. Build the package

```bash
cd /Users/sipi/agentshield/pkg
python3.11 -m pip install --user build 2>/dev/null || pip3 install build
python3.11 -m build
```

**Verify the build:**
```bash
ls -la /Users/sipi/agentshield/pkg/dist/
```
Must show:
- `agentshield-1.0.0-py3-none-any.whl`
- `agentshield-1.0.0.tar.gz`

### 1I. Test the built package in a clean venv

This is critical, it must work from a clean install with zero context.

```bash
# Create a test venv
python3.11 -m venv /tmp/as-test
source /tmp/as-test/bin/activate

# Install the built wheel
pip install /Users/sipi/agentshield/pkg/dist/agentshield-1.0.0-py3-none-any.whl

# Test the import
python -c "
from agentshield import SpendControlEngine, run_eval, SCENARIOS

# Test the engine
engine = SpendControlEngine()
result = engine.evaluate(
    {'amount': 10.00, 'merchant': 'openai-api', 'category': 'llm_inference',
     'agent_id': 'a1', 'timestamp': '2026-08-11T10:00:00Z'},
    [{'id': 'r1', 'type': 'transaction_limit', 'priority': 1, 'params': {'max_amount': 500}, 'action': 'BLOCK'}],
    []
)
assert result['decision'] == 'APPROVED', f'Expected APPROVED, got {result[\"decision\"]}'
print('Engine test: PASSED')

# Test the eval gym
results = run_eval()
assert results['passed'] == results['total'], f'{results[\"passed\"]}/{results[\"total\"]}'
print(f'Eval gym: {results[\"passed\"]}/{results[\"total\"]} PASSED')

print(f'Scenarios available: {len(SCENARIOS)}')
print('ALL TESTS PASSED')
"

deactivate
rm -rf /tmp/as-test
```

The output MUST show:
```
Engine test: PASSED
Eval gym: 56/56 PASSED
Scenarios available: 56
ALL TESTS PASSED
```

If it doesn't, fix the import paths, rebuild, and retest. Do NOT proceed to publishing until the clean-venv test passes.

### 1J. Publish to PyPI

Check for PyPI credentials:
```bash
# Check .pypirc
cat ~/.pypirc 2>/dev/null

# Check env
env | grep -i PYPI

# Check Hermes .env
grep -i pypi ~/.hermes/.env 2>/dev/null

# Check keychain
security find-generic-password -s "pypi" 2>/dev/null | head -5
security find-generic-password -s "PyPI" 2>/dev/null | head -5
```

**If a PyPI API token exists (starts with `pypi-`):**
```bash
cd /Users/sipi/agentshield/pkg
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-YOUR_TOKEN python3.11 -m twine upload dist/agentshield-1.0.0*
```

**If NO credentials exist:**
1. Try to register a PyPI account, this requires email verification, so it will likely fail autonomously. But try:
   ```bash
   # Check if we can use the requests/httpx to register
   python3.11 -c "
   import urllib.request, json
   # PyPI registration is through their web form, not a simple API
   print('PyPI registration requires web form + email verification')
   "
   ```

2. **If registration is blocked** (most likely): Build the package, verify it works in a clean venv, and document EXACTLY what Maryan needs to do:
   ```
   TO PUBLISH AGENTSHIELD TO PYPI (5 minutes):
   
   1. Go to https://pypi.org/account/register/
   2. Create account (email: sales@sipiteno.com)
   3. Verify email (check inbox)
   4. Go to Account Settings → API tokens → Add API token
   5. Scope: "Entire account"
   6. Copy the token (starts with pypi-)
   7. Run this command:
      cd /Users/sipi/agentshield/pkg && \
      TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-PASTE_TOKEN_HERE \
      python3.11 -m twine upload dist/agentshield-1.0.0*
   8. Verify: pip install agentshield
   ```

### 1K. Verify (if published)

```bash
pip install agentshield 2>&1
python3.11 -c "import agentshield; print(agentshield.__version__)"
```

Or verify the build exists (if not published):
```bash
ls -la /Users/sipi/agentshield/pkg/dist/
echo "Package built and tested. Awaiting PyPI credentials for publishing."
```

### 1L. Copy the package into the main repo

The package source should live in the repo alongside the core code:
```bash
cp -r /Users/sipi/agentshield/pkg/agentshield /Users/sipi/agentshield/agentshield_pkg
# Or add it to .gitignore if you don't want it in the repo
```

---

## TASK 2: AWESOME LIST SUBMISSIONS (15 min, PRIORITY #2)

### 2A. Add GitHub topics to the repo

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
  --add-topic python \
  --add-topic llm \
  --add-topic token-cost 2>&1
```

Verify:
```bash
gh repo view kindrat86/agentshield --json repositoryTopics --jq '.repositoryTopics[].name'
```

### 2B. Submit to awesome-ai-agents

Search for the repo and read its contribution guidelines:
```bash
gh search repos "awesome-ai-agents" --limit 5 --sort stars
```

For the top result (likely `e2b-dev/awesome-ai-agents` or similar with 50k+ stars):
```bash
# Read their README structure to find the right section
gh repo view OWNER/REPO --json description 2>/dev/null

# Create an issue requesting addition
gh issue create --repo OWNER/awesome-ai-agents \
  --title "Add AgentShield, AI Agent Spend Firewall (open source, MIT)" \
  --body "## AgentShield

**Description:** A per-transaction spend firewall for AI agents. Evaluates every API call against 9 composable rules in <1ms before it executes. Pure Python stdlib, zero dependencies.

**GitHub:** https://github.com/kindrat86/agentshield
**Website:** https://agentshield.fly.dev
**License:** MIT
**Stars:** Growing
**Eval Gym:** 56/56 test scenarios (MIT licensed)

**Why it belongs here:** AI agents make autonomous API calls with no budget awareness. AgentShield is the only open-source per-transaction enforcement layer (not observability, enforcement). Self-hostable in 60 seconds. Now available on PyPI: \`pip install agentshield\`.

**Category:** Open Source / Tools / Cost Management" 2>&1
```

Record the issue URL.

### 2C. Submit to 2-3 more lists

Search for other relevant awesome lists:
```bash
gh search repos "awesome langchain" --limit 3 --sort stars
gh search repos "awesome llm tools" --limit 3 --sort stars
gh search repos "awesome ai cost" --limit 3 --sort stars
```

For each relevant list, create an issue or PR following their contribution format.

---

## TASK 3: SHOW HN DRAFT + ATTEMPT (15 min, PRIORITY #3)

### 3A. Check HN karma

```bash
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'Karma: {d.get(\"karma\", 0)}')
    print(f'Items submitted: {len(d.get(\"submitted\", []))}')
except:
    print('User not found or API error')
" 2>/dev/null
```

### 3B. Write the Show HN post

Create `/Users/sipi/agentshield/content/show-hn-post.md`:

```markdown
Title: Show HN: AgentShield – A firewall for AI agent spending (56 eval scenarios, pure stdlib)

Body:
I built a per-transaction spend firewall for AI agents after one of my agents spent $2,800 in 60 seconds while I was asleep.

The problem: AI agents make autonomous API calls with zero budget awareness. A single infinite loop, retry storm, or context accumulation bug can drain your API budget before you wake up. Observability tools (Helicone, LangSmith) show you what happened AFTER the bill arrives. Nothing stops the transaction BEFORE it executes.

AgentShield sits between your agent and the API. Every transaction is evaluated against 9 composable rules in under 1ms. First rule that matches wins.

Rule types:
- Transaction limits (block any single call over $X)
- Daily totals (cap cumulative spend per agent per day)
- Velocity detection (flag if N+ calls happen in a time window)
- Merchant allowlists (only allow approved API providers)
- Category blocks (block entire spending categories)
- Session budgets (session-scoped spend cap with decay tightening)
- Cascade cost estimation (pre-dispatch EV: call_cost + fail_probability × reversal_cost)

The last two rule types were suggested by an engineer at HeartFlow who's building production cost-gating. We implemented them and added 6 new eval scenarios.

I wrote 56 labeled test scenarios for spend-control engines and open-sourced them (MIT). pip install agentshield.

Pure Python 3.11 standard library. Zero dependencies. Runs on 256MB RAM. Self-hostable in 60 seconds.

GitHub: https://github.com/kindrat86/agentshield
Live demo + risk calculator: https://agentshield.fly.dev
Eval gym (56/56): https://agentshield.fly.dev/eval

Happy to discuss the architecture, the cascade_cost EV model, or take feature requests.
```

### 3C. Attempt submission via Safari

```bash
open -a Safari "https://news.ycombinator.com/submit"
```
Capture. If logged in as SipitenoMK:
- Fill the title field via `type` (foreground mode): `Show HN: AgentShield – A firewall for AI agent spending (56 eval scenarios, pure stdlib)`
- Fill the text field with the body
- Submit

If karma is too low (< 5) or not logged in:
- Save the draft
- Note: "Show HN requires manual submission, karma may be too low"

---

## TASK 4: CHECK ACTIVE CONVERSATIONS (5 min)

```bash
for url in \
  "https://github.com/openclaw/openclaw/issues/42475" \
  "https://github.com/zeroclaw-labs/zeroclaw/issues/2269" \
  "https://github.com/langchain-ai/langchain/issues/31647"; do
  echo "=== $(basename $(dirname $url))/$(basename $url) ==="
  gh issue view "$url" --comments 2>&1 | tail -15
  echo ""
done
```

If @yun520-1 or @theonlyhennygod replied → respond immediately. That's worth more than everything else.

---

## TASK 5: VERIFY & COMMIT (5 min)

```bash
# Product health
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# Tests (core, the package doesn't affect the server)
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1 | tail -3

# Package build artifacts
ls -la /Users/sipi/agentshield/pkg/dist/ 2>/dev/null

# GitHub topics
gh repo view kindrat86/agentshield --json repositoryTopics --jq '[.repositoryTopics[].name]' 2>/dev/null

# Commit
cd /Users/sipi/agentshield && git add -A
git commit -m "Phase 15: PyPI package built, awesome list submissions, Show HN draft, GitHub topics"
git log --oneline -3
```

---

## REPORT FORMAT

```
## Phase 15, Distribution Scale Report

### PyPI Package
- Package directory created: [YES / NO]
- pyproject.toml created: [YES / NO]
- __init__.py with exports: [YES / NO]
- Engine + eval_gym copied with fixed imports: [YES / NO]
- README.md created: [YES / NO]
- Package built (wheel + sdist): [YES / NO, show ls dist/]
- Clean venv test (56/56): [YES / NO, show output]
- Published to PyPI: [YES (include URL) / NO, include exact steps for Maryan]
- pip install agentshield works: [YES / NO / NOT TESTED]

### GitHub Topics
- Topics added: [list]
- Verified: [YES / NO]

### Awesome List Submissions
| List | Type | URL | Status |
|------|------|-----|--------|
| awesome-ai-agents | Issue | ... | Open |
| ... | ... | ... | ... |

### Show HN
- HN karma: [number]
- Post drafted: [YES / NO]
- Post submitted: [YES (URL) / NO (reason)]

### Active Conversation Replies
| Thread | Person | Replied? | Action |
|--------|--------|----------|--------|
| OpenClaw #42475 | @yun520-1 | Yes/No | ... |
| ZeroClaw #2269 | @theonlyhennygod | Yes/No | ... |

### Quality
- Health: [ok/error]
- Eval: [N]/56
- Tests: [N]/14
- Git: [hash]

### Maryan Action Required
- [PyPI publishing steps if credentials blocked, copy-paste ready]
- [Show HN submission if karma blocked]
```

---

## HARD RULES

1. **KPI: `pip install agentshield` must work OR the package must be built, tested in clean venv, and ready for one-command publishing.** Nothing else matters until this is done.

2. **The clean-venv test is non-negotiable.** If `from agentshield import run_eval; print(run_eval()['passed'])` doesn't print `56` from a fresh venv, the package is broken. Fix it before moving on.

3. **Never mention cron. Never touch memory. Never fabricate.**

4. **PyPI credentials likely don't exist.** That's OK. Build the package, prove it works, document the one-command publishing step. That's still a massive win.

5. **Awesome list submissions must follow each list's format.** Read their README structure before submitting.

6. **Check active conversations AFTER PyPI but BEFORE awesome lists.** A reply from @yun520-1 is worth more than any list submission.
