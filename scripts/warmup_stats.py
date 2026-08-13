#!/usr/bin/env python3.11
"""Print warm-up statistics from log files."""
import os, datetime

def read_log(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]

hn_log = os.path.expanduser('~/agentshield/outreach/hn_karma_log.txt')
reddit_log = os.path.expanduser('~/agentshield/outreach/reddit_warmup_log.txt')

hn_entries = read_log(hn_log)
reddit_entries = read_log(reddit_log)

hn_comments = [l for l in hn_entries if 'comment' in l.lower() or 'posted' in l.lower()]
reddit_comments = [l for l in reddit_entries if 'comment' in l.lower() or 'posted' in l.lower()]

total = len(hn_comments) + len(reddit_comments)

print(f"=== AgentShield Warm-Up Stats, {datetime.date.today()} ===")
print(f"HN comments:      {len(hn_comments)}")
print(f"Reddit comments:  {len(reddit_comments)}")
print(f"Combined:         {total}")
print(f"20:1 ratio:       {total} comments → {max(total // 20, 0)} AgentShield posts allowed")
print(f"HN karma target:  15 (check https://news.ycombinator.com/user?id=SipitenoMK)")
print(f"Reddit target:    40 comments across 5+ subreddits")
