# PyPI Publish — One Command Left (2 minutes)

**Status (2026-08-11, updated after fixup commit 19efdb6):**
- ✅ Package renamed to **`agentshield-spend`** in pyproject.toml (the names `agentshield` and `agentshield-firewall` are both taken on PyPI by unrelated projects)
- ✅ Rebuilt: `dist/agentshield_spend-1.0.0-py3-none-any.whl` + `.tar.gz`
- ✅ `twine check` PASSED on both artifacts
- ✅ Clean-venv install test: **56/56 passed, v1.0.0, 56 scenarios**
- ❌ Not published — PyPI account creation requires human email verification + 2FA

**Import name is unchanged** — only the pip install name differs:

```python
pip install agentshield-spend
from agentshield import SpendControlEngine, run_eval
```

## Steps for Maryan

1. Go to https://pypi.org/account/register/ — create account (suggest username `sipiteno` or `kindrat86`, email sales@sipiteno.com)
2. Verify email, enable 2FA (required)
3. Account Settings → API tokens → Add API token (scope: "Entire account")
4. Copy the token (starts with `pypi-`)
5. Run:

```bash
cd /Users/sipi/agentshield
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE /tmp/asbuild/bin/twine upload dist/agentshield_spend-1.0.0*
```

(If `/tmp/asbuild` was cleaned up: `python3.11 -m venv /tmp/asbuild && /tmp/asbuild/bin/pip install build twine`)

6. Verify:

```bash
pip install agentshield-spend
python3.11 -c "import agentshield; print(agentshield.__version__)"
```

Package page will be: https://pypi.org/project/agentshield-spend/
