#!/usr/bin/env python3
"""
AgentShield Show HN Auto-Poster
Checks HN karma and rate-limit cooldown every run.
Posts Show HN via Safari do JavaScript when conditions are met.

Trigger: cron every 30 minutes
"""
import json
import subprocess
import time
import urllib.request
import os

HN_USER = "SipitenoMK"
SHOW_HN_TITLE = "Show HN: AgentShield – A firewall for AI agent spending (56 eval scenarios, pure stdlib)"
SHOW_HN_URL = "https://agentshield.sipiteno.com"
MIN_KARMA = 2  # Minimum karma to attempt Show HN
COOLDOWN_HOURS = 3  # Hours to wait after last submission

def get_hn_karma():
    """Fetch current karma from HN Firebase API."""
    try:
        url = f"https://hacker-news.firebaseio.com/v0/user/{HN_USER}.json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("karma", 0), data.get("submitted", [])
    except Exception as e:
        return None, []

def get_last_submission_time(submitted_ids):
    """Get the timestamp of the most recent submission."""
    if not submitted_ids:
        return 0
    # Check the most recent submission
    try:
        item_id = submitted_ids[0]
        url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("time", 0)
    except:
        return 0

def check_already_posted_show_hn(submitted_ids):
    """Check if Show HN was already successfully posted."""
    for item_id in (submitted_ids or []):
        try:
            url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                title = data.get("title", "")
                if "agentshield" in title.lower() and "show hn" in title.lower():
                    return True, f"https://news.ycombinator.com/item?id={item_id}"
        except:
            continue
    return False, None

def post_show_hn():
    """Post Show HN via Safari do JavaScript."""
    title = SHOW_HN_TITLE
    url = SHOW_HN_URL

    # Escape for AppleScript
    title_escaped = title.replace('"', '\\"').replace("'", "\\'")
    url_escaped = url.replace('"', '\\"')

    js_fill = f"""
    var titleInput = document.querySelector('input[name="title"]');
    var urlInput = document.querySelector('input[name="url"]');
    if (titleInput && urlInput) {{
        titleInput.value = "{title_escaped}";
        urlInput.value = "{url_escaped}";
        var form = document.querySelector('form');
        if (form) {{
            form.submit();
            "SUBMITTED: " + titleInput.value;
        }} else {{
            "ERROR: form not found";
        }}
    }} else {{
        "ERROR: inputs not found";
    }}
    """

    # First navigate to submit page
    nav_result = subprocess.run(
        ["osascript", "-e", f'tell application "Safari" to open location "https://news.ycombinator.com/submit"'],
        capture_output=True, text=True, timeout=10
    )

    # Wait for page load
    time.sleep(4)

    # Fill and submit
    applescript = f'tell application "Safari" to do JavaScript "{js_fill.strip()}" in document 1'
    # Escape the inner JS for AppleScript string
    applescript = applescript.replace('\n', '\\n').replace('"', '\\"')

    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True, text=True, timeout=15
    )

    return result.stdout.strip() or result.stderr.strip()

def main():
    print(f"=== AgentShield Show HN Monitor, {time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    # Check karma
    karma, submitted = get_hn_karma()
    if karma is None:
        print("RESULT: [BLOCKED], HN API unreachable")
        print("[SILENT]")
        return

    print(f"Karma: {karma}")

    # Check if Show HN already posted
    already_posted, post_url = check_already_posted_show_hn(submitted)
    if already_posted:
        print(f"RESULT: [ALREADY POSTED], Show HN is live at {post_url}")
        print(f"SHOWHN_LIVE:{post_url}")
        return

    # Check cooldown
    last_time = get_last_submission_time(submitted)
    if last_time > 0:
        hours_since = (int(time.time()) - last_time) / 3600
        print(f"Last submission: {hours_since:.1f} hours ago")
        if hours_since < COOLDOWN_HOURS:
            remaining = COOLDOWN_HOURS - hours_since
            print(f"RESULT: [COOLDOWN], {remaining:.1f} hours remaining until Show HN can be posted")
            print(f"COOLDOWN:{remaining:.1f}")
            return

    # Check minimum karma
    if karma < MIN_KARMA:
        print(f"RESULT: [LOW_KARMA], karma {karma} < {MIN_KARMA} required")
        print(f"LOWKARMA:{karma}")
        return

    # All conditions met, POST SHOW HN
    print(f"RESULT: [ATTEMPTING], karma {karma} >= {MIN_KARMA}, cooldown expired")
    print("Posting Show HN via Safari do JavaScript...")

    result = post_show_hn()
    print(f"Safari JS result: {result}")

    # Verify after 5 seconds
    time.sleep(5)
    karma_after, submitted_after = get_hn_karma()
    posted_after, post_url_after = check_already_posted_show_hn(submitted_after)

    if posted_after:
        print(f"RESULT: [SUCCESS], Show HN posted at {post_url_after}")
        print(f"SHOWHN_LIVE:{post_url_after}")
    else:
        # Check if we got rate limited
        verify_result = subprocess.run(
            ["osascript", "-e", 'tell application "Safari" to do JavaScript "document.body.innerText.substring(0, 300);" in document 1'],
            capture_output=True, text=True, timeout=10
        )
        body = verify_result.stdout.strip()
        if "too fast" in body.lower() or "slow down" in body.lower():
            print("RESULT: [RATE_LIMITED], HN anti-spam triggered. Try again later.")
            print("RATE_LIMITED")
        else:
            print(f"RESULT: [UNCERTAIN], Submission attempted. Page content: {body[:200]}")
            print(f"UNCERTAIN:{body[:200]}")

if __name__ == "__main__":
    main()
