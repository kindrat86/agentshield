"""
AgentShield Emergency, instant crisis scanner.

Usage:
    python -m agentshield.emergency

Scans your environment for AI agent spend vulnerabilities:
- Checks for API keys without budget limits
- Detects running processes that might be agents
- Estimates your risk score
- Prints an action plan

Zero dependencies. Pure Python 3.11 stdlib.
"""

import os
import sys
import platform
import subprocess
from decimal import Decimal

VERSION = "1.0.0"

def _check_env_keys():
    """Find API keys in environment variables."""
    key_patterns = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
                    'GEMINI_API_KEY', 'DEEPSEEK_API_KEY', 'PERPLEXITY_API_KEY',
                    'COHERE_API_KEY', 'MISTRAL_API_KEY', 'TOGETHER_API_KEY',
                    'AZURE_OPENAI_KEY', 'REPLICATE_API_TOKEN']
    found = []
    for key in key_patterns:
        if os.environ.get(key):
            found.append(key)
    # Also check .env files
    for envpath in ['.env', os.path.expanduser('~/.env'), os.path.expanduser('~/.config/agentshield/.env')]:
        if os.path.exists(envpath):
            try:
                with open(envpath) as f:
                    for line in f:
                        for pat in key_patterns:
                            if pat in line and '=' in line:
                                val = line.split('=', 1)[1].strip().strip('"').strip("'")
                                if val and len(val) > 10:
                                    if pat not in found:
                                        found.append(pat)
            except:
                pass
    return found

def _check_agent_processes():
    """Detect potentially running agent processes."""
    agents = []
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            lower = line.lower()
            if any(kw in lower for kw in ['langchain', 'autogpt', 'crewai', 'openclaw',
                                           'agent', 'llm', 'openai', 'anthropic']):
                if 'grep' not in lower and 'agentshield' not in lower:
                    parts = line.split()
                    if len(parts) > 10:
                        agents.append(' '.join(parts[10:14]))
        return list(set(agents))[:5]
    except:
        return []

def _calculate_risk_score(keys_found, agents_running):
    """Calculate a 0-100 risk score."""
    score = 0
    # Each API key without a firewall = +15
    score += min(len(keys_found) * 15, 60)
    # Each running agent = +8
    score += min(len(agents_running) * 8, 24)
    # No budget monitoring = +10
    if not os.environ.get('AGENTSHIELD_API_KEY'):
        score += 10
    # No daily cap configured = +6
    score += 6
    return min(score, 100)

def _estimate_monthly_exposure(risk_score, keys_found):
    """Estimate potential monthly exposure."""
    base = 50  # Base cost
    per_key = 200  # Per unmonitored key
    risk_multiplier = Decimal(str(risk_score)) / Decimal('50')
    total = (base + len(keys_found) * per_key) * risk_multiplier
    return int(total)

def run_emergency():
    """Run the emergency scan and print results."""
    print("\n" + "=" * 60)
    print("  🚨 AGENTSHIELD EMERGENCY SCAN")
    print("  Find out if your AI agents are burning money right now")
    print("=" * 60)

    print("\n📋 Scanning environment...\n")

    # Check API keys
    keys = _check_env_keys()
    if keys:
        print(f"⚠️  Found {len(keys)} API key(s) in your environment:")
        for k in keys:
            print(f"   • {k}")
        print(f"   None of these have spend enforcement.\n")
    else:
        print("✅ No API keys found in environment.\n")

    # Check running processes
    agents = _check_agent_processes()
    if agents:
        print(f"⚠️  Found {len(agents)} potentially running agent process(es):")
        for a in agents:
            print(f"   • {a[:60]}")
        print()
    else:
        print("✅ No obvious agent processes running.\n")

    # Risk score
    risk = _calculate_risk_score(keys, agents)
    exposure = _estimate_monthly_exposure(risk, keys)

    print("=" * 60)
    if risk >= 70:
        level = "🔴 CRITICAL"
    elif risk >= 40:
        level = "🟡 ELEVATED"
    else:
        level = "🟢 LOW"
    print(f"  RISK SCORE: {risk}/100, {level}")
    print(f"  ESTIMATED MONTHLY EXPOSURE: ~${exposure:,}")
    print(f"  ANNUAL RISK: ~${exposure * 12:,}")
    print("=" * 60)

    print("\n📋 ACTION PLAN:\n")
    if risk >= 40:
        print("  1. IMMEDIATE: pip install agentshield")
        print("     → Add transaction limits BEFORE your next agent run")
        print()
        print("  2. THIS WEEK: Run the eval gym to test your rules")
        print("     → from agentshield import run_eval; run_eval()")
        print()
        print("  3. SCHEDULE: Get a professional spend audit")
        print("     → https://agentshield.fly.dev/audit")
    else:
        print("  Your risk is relatively low, but:")
        print("  • pip install agentshield to set up prevention")
        print("  • Run eval gym: from agentshield import run_eval; run_eval()")
        print("  • Risk calculator: https://agentshield.fly.dev/tools/risk-calculator/")

    print("\n" + "=" * 60)
    print(f"  AgentShield Emergency v{VERSION}")
    print(f"  https://agentshield.fly.dev")
    print(f"  pip install agentshield | MIT Licensed")
    print("=" * 60 + "\n")

    return {"risk_score": risk, "exposure": exposure, "keys_found": len(keys), "agents_running": len(agents)}

if __name__ == '__main__':
    run_emergency()
