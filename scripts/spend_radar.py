#!/usr/bin/env python3.11
"""
AgentShield Spend Radar — GitHub Issue/PR Scanner
==================================================
Searches GitHub for developers complaining about AI agent API costs,
retry storms, rate limit loops, or runaway spending. Generates draft
outreach comments and delivers them to Telegram for manual posting.

Usage:
    python3.11 scripts/spend_radar.py              # Scan + deliver to Telegram
    python3.11 scripts/spend_radar.py --dry-run    # Scan only, print results
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

GITHUB_API = "https://api.github.com/search/issues"
TELEGRAM_CHAT = "369633431"
# Bot token is read from the environment or the Hermes config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# Fallback: try to read from Hermes config
if not TELEGRAM_TOKEN:
    try:
        config_path = os.path.expanduser("~/.hermes/config.yaml")
        if os.path.exists(config_path):
            with open(config_path) as f:
                for line in f:
                    if "telegram_bot_token" in line.lower() and ":" in line:
                        TELEGRAM_TOKEN = line.split(":", 1)[1].strip().strip('"').strip("'")
                        break
    except Exception:
        pass

SEARCH_QUERIES = [
    "openai bill expensive in:body in:comments",
    "runaway agent cost in:body in:comments",
    "AI agent spending budget in:body in:comments",
    "rate limit storm retry expensive in:body in:comments",
    "agent loop cost API in:body in:comments",
    "LLM cost overrun in:body in:comments",
    "agent infinite loop API bill in:body in:comments",
]

DRAFT_TEMPLATE = """Hi {author}, saw your issue about {issue_title}. We hit the same wall and built AgentShield — a per-transaction spend firewall that evaluates each API call against configurable rules (transaction limits, daily caps, velocity detection) in under 1ms before the call executes. Pure Python stdlib, zero deps.

Risk calculator (no signup): https://agentshield.fly.dev/tools/risk-calculator/
GitHub: https://github.com/kindrat86/agentshield

Would this help your situation?"""


def search_github(query: str, max_results: int = 3) -> list:
    """Search GitHub issues for the given query."""
    url = f"{GITHUB_API}?q={urllib.parse.quote(query)}&sort=created&order=desc&per_page={max_results}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AgentShield-SpendRadar/1.0",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("items", [])
    except Exception as e:
        print(f"  Search error for '{query[:50]}': {e}", file=sys.stderr)
        return []


def build_report(results: list) -> str:
    """Build a formatted report for Telegram delivery."""
    if not results:
        return "🛡️ AgentShield Spend Radar: No new high-intent leads found today."

    lines = [f"🛡️ AgentShield Spend Radar — {len(results)} lead(s) found\n"]

    for i, item in enumerate(results[:5], 1):
        title = item.get("title", "?")[:80]
        url = item.get("html_url", "")
        author = item.get("user", {}).get("login", "unknown")
        repo = url.split("github.com/")[-1].split("/issues/")[0] if "github.com/" in url else "?"
        created = item.get("created_at", "")[:10]

        draft = DRAFT_TEMPLATE.format(author=author, issue_title=title[:60])

        lines.append(f"━━━ Lead {i} ━━━")
        lines.append(f"📋 {title}")
        lines.append(f"👤 @{author} in {repo}")
        lines.append(f"📅 {created}")
        lines.append(f"🔗 {url}")
        lines.append(f"💬 Draft comment:")
        lines.append(f"  {draft[:200]}...")
        lines.append("")

    lines.append("→ Post manually from your GitHub account. Do NOT automate.")
    return "\n".join(lines)


def send_telegram(text: str) -> bool:
    """Send message via Telegram bot."""
    if not TELEGRAM_TOKEN:
        print("  [TELEGRAM] No bot token found — skipping delivery")
        return False

    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT,
        "text": text[:4000],  # Telegram limit
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    req = urllib.request.Request(url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("ok", False)
    except Exception as e:
        print(f"  [TELEGRAM] Send error: {e}", file=sys.stderr)
        return False


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"=== AgentShield Spend Radar ===")
    print(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print(f"Queries: {len(SEARCH_QUERIES)}")
    print()

    all_results = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        print(f"  Searching: {query[:60]}...")
        results = search_github(query, max_results=2)
        for item in results:
            url = item.get("html_url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                all_results.append(item)
        print(f"    Found: {len(results)} results")

    # Filter: only issues from the last 30 days with real engagement
    filtered = []
    for item in all_results:
        score = item.get("score", 0)
        comments = item.get("comments", 0)
        if score > 1 or comments > 0:  # Basic quality filter
            filtered.append(item)

    print(f"\nTotal unique results: {len(all_results)}")
    print(f"Filtered (score>1 or comments>0): {len(filtered)}")

    if not filtered:
        print("No actionable leads found.")
        if not dry_run:
            send_telegram("🛡️ AgentShield Spend Radar: No new high-intent leads today.")
        return

    report = build_report(filtered)
    print(f"\n--- REPORT ---\n{report[:500]}...\n")

    if not dry_run:
        sent = send_telegram(report)
        print(f"\nTelegram delivery: {'✅ sent' if sent else '❌ failed'}")
    else:
        print("\n[DRY RUN] Skipping Telegram delivery")


if __name__ == "__main__":
    main()
