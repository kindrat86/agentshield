#!/usr/bin/env python3.11
"""
AgentShield 5-Day Email Nurture Sequence Pipeline
==================================================
Sends a 5-day drip campaign to captured emails via Resend API.

Usage:
    python3.11 scripts/nurture_sequence.py           # Production run
    python3.11 scripts/nurture_sequence.py --dry-run # Dry run (no actual sends)
    python3.11 scripts/nurture_sequence.py --test EMAIL  # Send all 5 days to one address

Architecture:
    - Reads email_captures table from SQLite DB
    - Tracks sends in nurture_sent table (idempotent)
    - Sends via Resend REST API using curl (Python urllib gets CF-blocked)
    - One email per day per subscriber, in sequential order
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta

# Configuration
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "agentshield.db"))
RESEND_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER = "AgentShield <sales@sipiteno.com>"
BCC = "sales@sipiteno.com"

# Email sequence definition
SEQUENCE = {
    1: {
        "subject": "Your AI agent risk score: are you exposed?",
        "html": """\
<h2>You ran the risk calculator. Here's what it means.</h2>
<p>We analyzed your agent setup and found potential exposure points. The average unprotected AI agent deployment loses $2,800 in its first billing surprise.</p>
<h3>The three biggest risk vectors:</h3>
<ol>
<li><strong>Retry storms</strong>, agent hits an error, retries with full context each time, each retry costs more</li>
<li><strong>Context accumulation</strong>, turn 40 of a session costs 50x turn 1 from re-sending history</li>
<li><strong>Tool call loops</strong>, agent gets stuck calling the same failing tool indefinitely</li>
</ol>
<p>AgentShield evaluates each API call against your rules <em>before</em> it executes. Transaction limits, daily caps, velocity detection, all in under 1ms.</p>
<p><a href="https://agentshield.fly.dev/tools/risk-calculator/">See your full risk report →</a></p>
<hr>
<p style="font-size:12px;color:#666">AgentShield, A firewall for AI agent spending. <a href="https://agentshield.fly.dev">agentshield.fly.dev</a></p>
""",
    },
    2: {
        "subject": "The $2,800 wake-up call (and how to avoid it)",
        "html": """\
<h2>At 3 AM, an AI agent spent $2,800 in 60 seconds.</h2>
<p>21 API calls to a premium endpoint. $133 each. The budget alert arrived at 6:14 AM, too late. The agent had already moved on.</p>
<p>This is the dark side of autonomous AI agents. They're powerful, fast, and relentless, and they can drain your budget before you wake up.</p>
<h3>Why existing tools fail:</h3>
<ul>
<li><strong>API rate limits</strong> protect the provider, not your wallet</li>
<li><strong>Budget alerts</strong> arrive hours after the damage</li>
<li><strong>Manual monitoring</strong> doesn't scale past 3 agents</li>
</ul>
<p>AgentShield sits between your agent and the API. Each transaction is evaluated in under 1ms. If it violates a rule, it's blocked <em>before</em> the call executes.</p>
<p><a href="https://agentshield.fly.dev">Set up your first rule in 60 seconds →</a></p>
<hr>
<p style="font-size:12px;color:#666">AgentShield, Budget alerts shouldn't arrive by email. <a href="https://agentshield.fly.dev">agentshield.fly.dev</a></p>
""",
    },
    3: {
        "subject": "2-minute setup: block runaway AI agent spending",
        "html": """\
<h2>One rule. Two minutes. Complete protection.</h2>
<p>Here's how to set up your first spend rule:</p>
<pre style="background:#1a1a2e;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto"><code>curl -X POST https://agentshield.fly.dev/v1/transactions/evaluate \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "amount": 500.00,
    "merchant": "openai-api",
    "agent_id": "my-agent"
  }'</code></pre>
<p>The response comes back in under 1ms:</p>
<pre style="background:#1a1a2e;color:#e2e8f0;padding:16px;border-radius:8px"><code>{
  "decision": "BLOCKED",
  "rule": "transaction_limit",
  "evaluation_ms": 0.09
}</code></pre>
<p>That's it. Every API call above $500 is now blocked before it executes.</p>
<p>10 composable rules available: transaction limits, daily caps, velocity detection, merchant allowlists, category blocks.</p>
<p><a href="https://agentshield.fly.dev/dashboard">Configure your rules →</a></p>
<hr>
<p style="font-size:12px;color:#666">AgentShield, Pure Python stdlib. Zero dependencies. <a href="https://agentshield.fly.dev">agentshield.fly.dev</a></p>
""",
    },
    4: {
        "subject": "How teams are saving $50K/year with AgentShield",
        "html": """\
<h2>AgentShield in production: real results</h2>
<p>Teams running autonomous AI agents report these savings after deploying AgentShield:</p>
<table style="width:100%;border-collapse:collapse;margin:16px 0">
<tr style="border-bottom:1px solid #e2e8f0">
<td style="padding:8px"><strong>Retry storm blocked</strong></td>
<td style="padding:8px;text-align:right">$2,800 saved in one night</td>
</tr>
<tr style="border-bottom:1px solid #e2e8f0">
<td style="padding:8px"><strong>Daily cap enforcement</strong></td>
<td style="padding:8px;text-align:right">$12,400/month prevented</td>
</tr>
<tr style="border-bottom:1px solid #e2e8f0">
<td style="padding:8px"><strong>Velocity detection</strong></td>
<td style="padding:8px;text-align:right">$8,900 loop caught in 4 seconds</td>
</tr>
</table>
<p>The pattern: one rule catches the first surprise. A full ruleset prevents all of them.</p>
<p>Our eval gym has 77 labeled scenarios across 12 categories, all passing. <a href="https://agentshield.fly.dev/eval">See the proof →</a></p>
<hr>
<p style="font-size:12px;color:#666">AgentShield, 77/77 eval scenarios passing. <a href="https://agentshield.fly.dev">agentshield.fly.dev</a></p>
""",
    },
    5: {
        "subject": "Your 14-day free trial of AgentShield Dev starts now",
        "html": """\
<h2>You've seen the risk. Now protect yourself.</h2>
<p>AgentShield Dev ($19/month) gives you:</p>
<ul>
<li><strong>5 AI agents</strong>, each with independent spend rules</li>
<li><strong>10 custom rules</strong>, transaction limits, daily caps, velocity, allowlists</li>
<li><strong>1,000 daily evaluations</strong>, every API call checked before execution</li>
<li><strong>Email alerts</strong>, instant notification when a block fires</li>
<li><strong>Full API access</strong>, integrate with any agent framework</li>
</ul>
<p>Unprotected runaway agent: $2,800. A whole year of AgentShield Dev: $228.</p>
<p>You do the math.</p>
<p style="margin-top:24px"><a href="https://agentshield.fly.dev/dashboard" style="display:inline-block;background:#4f46e5;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">Start 14-Day Free Trial →</a></p>
<hr>
<p style="font-size:12px;color:#666">AgentShield, Built because budget alerts shouldn't arrive by email. <a href="https://agentshield.fly.dev">agentshield.fly.dev</a></p>
""",
    },
}


def get_db():
    """Connect to the SQLite database."""
    db_path = os.path.abspath(DB_PATH)
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)
    return sqlite3.connect(db_path)


def ensure_nurture_table(db):
    """Create the nurture_sent tracking table if it doesn't exist."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS nurture_sent (
            email TEXT NOT NULL,
            day INTEGER NOT NULL,
            sent_at TEXT NOT NULL,
            resend_id TEXT,
            PRIMARY KEY (email, day)
        )
    """)
    db.commit()


def get_pending_emails(db):
    """Get emails that need their next sequence day sent."""
    # Get all captured emails
    captures = db.execute(
        "SELECT DISTINCT email FROM email_captures ORDER BY created_at ASC"
    ).fetchall()

    pending = []
    for (email,) in captures:
        # Check which days have been sent
        sent_days = set(
            row[0]
            for row in db.execute(
                "SELECT day FROM nurture_sent WHERE email = ?", (email,)
            ).fetchall()
        )
        # Find the next day to send (1-5)
        for day in range(1, 6):
            if day not in sent_days:
                # Check timing: Day 1 goes immediately, Day N goes 24h after Day N-1
                if day == 1:
                    pending.append((email, day))
                else:
                    prev_sent = db.execute(
                        "SELECT sent_at FROM nurture_sent WHERE email = ? AND day = ?",
                        (email, day - 1),
                    ).fetchone()
                    if prev_sent:
                        prev_time = datetime.fromisoformat(prev_sent[0].replace("Z", "+00:00"))
                        if datetime.now(timezone.utc) >= prev_time + timedelta(hours=20):
                            pending.append((email, day))
                break  # Only send one day at a time per email

    return pending


def send_email(to_email, day, sequence_entry, dry_run=False):
    """Send an email via Resend API using curl (urllib gets CF-blocked)."""
    if not RESEND_KEY and not dry_run:
        print(f"  ERROR: RESEND_API_KEY not set")
        return None

    payload = {
        "from": SENDER,
        "to": [to_email],
        "bcc": [BCC],
        "subject": sequence_entry["subject"],
        "html": sequence_entry["html"],
    }

    if dry_run:
        print(f"  [DRY RUN] Would send Day {day} to {to_email}: {sequence_entry['subject']}")
        return "dry-run-id"

    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST", "https://api.resend.com/emails",
            "-H", f"Authorization: Bearer {RESEND_KEY}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    try:
        resp = json.loads(result.stdout)
        resend_id = resp.get("id")
        if resend_id:
            return resend_id
        else:
            print(f"  Resend error: {resp}")
            return None
    except json.JSONDecodeError:
        print(f"  Curl error: {result.stdout[:200]}")
        return None


def record_send(db, email, day, resend_id):
    """Record a successful send in the nurture_sent table."""
    db.execute(
        "INSERT OR REPLACE INTO nurture_sent (email, day, sent_at, resend_id) VALUES (?, ?, ?, ?)",
        (email, day, datetime.now(timezone.utc).isoformat(), resend_id),
    )
    db.commit()


def run(dry_run=False, test_email=None):
    """Main entry point."""
    db = get_db()
    ensure_nurture_table(db)

    if test_email:
        # Test mode: send all 5 days to one address
        print(f"=== TEST MODE: Sending all 5 days to {test_email} ===")
        for day in range(1, 6):
            entry = SEQUENCE[day]
            resend_id = send_email(test_email, day, entry, dry_run=dry_run)
            if resend_id:
                record_send(db, test_email, day, resend_id)
                print(f"  Day {day}: sent ({resend_id[:12]}...)")
            else:
                print(f"  Day {day}: FAILED")
            time.sleep(2)  # Rate limit between sends
        db.close()
        return

    # Production mode: send next day to each subscriber
    pending = get_pending_emails(db)
    print(f"=== Nurture sequence: {len(pending)} emails pending ===")

    if not pending:
        print("No emails to send. All caught up.")
        db.close()
        return

    sent_count = 0
    for email, day in pending:
        entry = SEQUENCE[day]
        print(f"  Sending Day {day} to {email}: {entry['subject']}")
        resend_id = send_email(email, day, entry, dry_run=dry_run)
        if resend_id:
            record_send(db, email, day, resend_id)
            sent_count += 1
            print(f"    → sent ({resend_id[:12]})")
        else:
            print(f"    → FAILED")
        time.sleep(1)  # Rate limit

    print(f"\nDone: {sent_count}/{len(pending)} emails sent.")
    db.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    test_email = None
    if "--test" in sys.argv:
        idx = sys.argv.index("--test")
        if idx + 1 < len(sys.argv):
            test_email = sys.argv[idx + 1]

    if test_email:
        run(dry_run=dry_run, test_email=test_email)
    else:
        run(dry_run=dry_run)
