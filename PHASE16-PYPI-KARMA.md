# MISSION: Publish to PyPI + Build HN Karma Through Value

## YOUR TWO KPIS
1. `pip install agentshield` returns successfully from PyPI
2. Post 2+ genuinely valuable comments on Hacker News to build karma toward Show HN

---

## RULE ZERO
Zero fabrication. Every claim backed by tool output. Never mention cron. Never touch memory.

---

## TASK 1: PUBLISH TO PyPI (10 min)

The package is built and tested. It works (56/56 in clean venv under Python 3.11). The only missing piece is a PyPI API token.

### 1A. Check for token one more time
```bash
grep -i "pypi" ~/.hermes/.env 2>/dev/null
grep -i "pypi-" ~/.hermes/ -r 2>/dev/null | head -5
cat ~/.pypirc 2>/dev/null
```

If found → skip to 1C.

### 1B. If no token exists (expected)

You cannot create a PyPI account autonomously (requires email verification + 2FA setup). This is a genuine human-only action. Document it for Maryan:

```
PUBLISH AGENTSHIELD TO PYPI (3 minutes):

1. Go to: https://pypi.org/account/register/
2. Username: sipiteno (or kindrat86)
3. Email: sales@sipiteno.com
4. Password: [your choice]
5. Verify email (check inbox)
6. Enable 2FA (required for new accounts)
7. Go to: Account Settings → API tokens → Add API token
8. Token name: "agentshield-publish"
9. Scope: "Entire account"
10. Copy the token (starts with pypi-)

Then run this ONE command:
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-PASTE_TOKEN_HERE \
  python3.11 -m twine upload /Users/sipi/agentshield/dist/agentshield-1.0.0*

Verify it worked:
  pip install agentshield
  python3.11 -c "from agentshield import run_eval; print(run_eval()['passed'])"
  # Should print: 56
```

### 1C. If a token IS found
```bash
cd /Users/sipi/agentshield
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-FOUND_TOKEN python3.11 -m twine upload dist/agentshield-1.0.0* 2>&1
```

Verify:
```bash
pip install agentshield 2>&1 | tail -3
python3.11 -c "import agentshield; print(agentshield.__version__)"
```

---

## TASK 2: BUILD HN KARMA THROUGH VALUE (30 min)

### Context
HN account `SipitenoMK` has karma=1. Show HN requires karma ≥ 2. The account is also rate-limited for low-karma users.

### Strategy
Find active HN threads about AI agents, API costs, or developer tools. Post **genuinely valuable comments** that add to the discussion. Do NOT mention AgentShield. Do NOT link to our product. The goal is karma, not distribution.

A valuable HN comment is one where:
- You share a real technical insight from building the same thing
- You correct a misconception with evidence
- You provide a useful data point from experience
- You ask a thoughtful question that advances the discussion

### 2A. Find active HN threads

Use the HN Algolia search API to find recent, active threads:

```bash
# Search for AI agent / cost threads (last 7 days, sorted by relevance)
curl -s "https://hn.algolia.com/api/v1/search?query=AI%20agent%20cost&tags=story&numericFilters=created_at_i>$(python3 -c 'import time; print(int(time.time()) - 604800)')" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for hit in d.get('hits', [])[:10]:
    print(f'{hit[\"objectID\"]:12} {hit.get(\"points\",0):4}pts  {hit[\"title\"][:80]}')
    print(f'             {hit[\"url\"][:80]}')
" 2>/dev/null

# Search for API billing / pricing threads
curl -s "https://hn.algolia.com/api/v1/search?query=API%20billing%20cost%20expensive&tags=story&numericFilters=created_at_i>$(python3 -c 'import time; print(int(time.time()) - 604800)')" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for hit in d.get('hits', [])[:10]:
    print(f'{hit[\"objectID\"]:12} {hit.get(\"points\",0):4}pts  {hit[\"title\"][:80]}')
" 2>/dev/null

# Search for LLM / agent development threads  
curl -s "https://hn.algolia.com/api/v1/search?query=LLM%20agent%20development&tags=story&numericFilters=created_at_i>$(python3 -c 'import time; print(int(time.time()) - 604800)')" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for hit in d.get('hits', [])[:10]:
    print(f'{hit[\"objectID\"]:12} {hit.get(\"points\",0):4}pts  {hit[\"title\"][:80]}')
" 2>/dev/null
```

### 2B. Read the top 3 threads

For the most promising threads (highest points, most comments, most relevant):
```bash
curl -s "https://hn.algolia.com/api/v1/items/ITEM_ID" | python3 -c "
import sys, json
def print_tree(item, depth=0):
    if depth > 2: return
    text = (item.get('text') or '')[:200]
    print(f'{'  '*depth}[{item.get(\"points\",\"?\")}pt] {item.get(\"author\",\"?\")}: {text}')
    for child in item.get('children', [])[:3]:
        print_tree(child, depth+1)
d = json.load(sys.stdin)
print_tree(d)
" 2>/dev/null
```

### 2C. Draft comments for the best 2 threads

For each thread, draft a comment that:
1. **Adds technical value**, shares a real insight, data point, or correction
2. **Is conversational**, responds to the thread's specific content
3. **Does NOT mention AgentShield, GitHub, or any link to our project**
4. **Is 3-8 sentences**, long enough to be substantive, short enough to be read

Save drafts to `/Users/sipi/agentshield/content/hn-karma-comments.md`.

### 2D. Post comments via Safari

```bash
open -a Safari "https://news.ycombinator.com/item?id=ITEM_ID"
```
Capture. If logged in as SipitenoMK:
- Find the comment textarea
- Use foreground `type` to enter the comment
- Click "add comment"

**Per the macos-browser-driving skill:** 
- Safari JS bridge needs the "Allow JavaScript from Apple Events" flag
- Foreground `type` is more reliable than `set_value` for textareas in Safari
- Verify with a capture after posting

### 2E. Check if comments posted

After posting each comment:
```bash
curl -s "https://hn.algolia.com/api/v1/items/ITEM_ID" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('children', []):
    if c.get('author') == 'SipitenoMK':
        print(f'Found our comment: {c[\"id\"]}')
        print(f'Text: {c[\"text\"][:100]}...')
" 2>/dev/null
```

---

## TASK 3: CHECK ACTIVE GITHUB CONVERSATIONS (5 min)

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

If @yun520-1 or @theonlyhennygod replied → respond immediately.

---

## TASK 4: UPDATE GITHUB README WITH PyPI BADGE (10 min)

Once the package is built (even before PyPI publishing), add a PyPI badge to the repo README:

Read `/Users/sipi/agentshield/README.md` and add near the top badges:

```markdown
[![PyPI version](https://img.shields.io/pypi/v/agentshield.svg)](https://pypi.org/project/agentshield/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

Also add a Quick Start section:
```markdown
## Install

```bash
pip install agentshield
```

## Quick Start

```python
from agentshield import SpendControlEngine

engine = SpendControlEngine()
result = engine.evaluate(
    transaction={"amount": 750.00, "merchant": "openai-api", "category": "llm_inference"},
    rules=[{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
    prior_transactions=[]
)
print(result["decision"])  # BLOCKED
```
```

Push to GitHub:
```bash
cd /Users/sipi/agentshield && git add -A && git commit -m "Add PyPI badge + install instructions to README" && git push
```

---

## TASK 5: AWESOME LIST FOLLOW-UP (5 min)

PR #1377 is open on `e2b-dev/awesome-ai-agents`. Check for maintainer feedback:

```bash
gh pr view 1377 --repo e2b-dev/awesome-ai-agents --json comments 2>&1 | head -20
```

If a maintainer requested changes → make them immediately.
If no feedback → leave it. Maintainers process these in batches.

Also check if PR #811 and #640 (older AgentShield submissions from April) can be closed to clean up:
```bash
gh pr close 811 --repo e2b-dev/awesome-ai-agents --comment "Closing old PR, superseded by #1377 with updated project details (spend firewall, 56 eval scenarios, PyPI package)." 2>&1
gh pr close 640 --repo e2b-dev/awesome-ai-agents --comment "Closing old PR, superseded by #1377." 2>&1
```

---

## TASK 6: VERIFY & COMMIT (5 min)

```bash
# Product health
curl -s https://agentshield.fly.dev/health
curl -s https://agentshield.fly.dev/eval | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"passed\"]}/{d[\"total\"]}')"

# Tests
cd /Users/sipi/agentshield && LICENSING_MASTER_SECRET=test python3.11 tests/run_tests.py 2>&1 | tail -3

# Package still works
python3.11 -c "from agentshield import run_eval; print(run_eval()['passed'])"

# HN karma check
curl -s "https://hacker-news.firebaseio.com/v0/user/SipitenoMK.json" | python3 -c "import sys,json; print(f'Karma: {json.load(sys.stdin).get(\"karma\",0)}')" 2>/dev/null

# Commit
cd /Users/sipi/agentshield && git add -A && git commit -m "Phase 16: PyPI ready, HN karma building, README badges, awesome-list cleanup"
git log --oneline -3
```

---

## REPORT FORMAT

```
## Phase 16, PyPI + Karma Report

### PyPI
- Token found: [YES / NO]
- Package published: [YES (URL) / NO, exact steps for Maryan]
- pip install works: [YES / NO / NOT TESTED]
- README badges added: [YES / NO]

### Hacker News Karma
- Starting karma: 1
- Comments drafted: [count]
- Comments posted: [count, include HN comment URLs]
- Ending karma: [number]
- Rate-limited: [YES / NO]

### GitHub Conversations
- @yun520-1 replied: [YES / NO]
- @theonlyhennygod replied: [YES / NO]
- Action taken: [Responded / Waiting]

### Awesome List
- PR #1377 status: [Open / Merged / Closed]
- Old PRs cleaned: [YES / NO]

### Quality
- Health: [ok/error]
- Eval: [N]/56
- Tests: [N]/14
- Git: [hash]

### Maryan Actions Required
- [PyPI registration if token not found, copy-paste ready]
- [Other items]
```

---

## HARD RULES

1. **KPI 1: `pip install agentshield` works from PyPI.** If token blocks, document exact steps. The package is already built and tested.

2. **KPI 2: Post 2+ valuable HN comments.** Genuinely valuable. No AgentShield mentions. No product links. Pure value to earn karma.

3. **Never mention AgentShield in HN comments.** The purpose is karma, not distribution. Mentioning the product will get downvoted and hurt karma.

4. **Check active GitHub conversations FIRST.** A reply from @yun520-1 is worth more than PyPI + HN combined.

5. **Never mention cron. Never touch memory. Never fabricate.**

6. **If PyPI token genuinely doesn't exist, say so honestly.** Don't fabricate a token or claim publishing worked. Document the 3-minute manual step.
