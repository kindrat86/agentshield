# SESSION REPORT, 2026-08-11, Cron Profile Split, Duplicate Removal, Telegram Fix

**Audience:** the next Hermes Agent session working on AgentShield.
**Status of this document:** every claim below is backed by tool output produced in-session. Where a prior belief was wrong, including beliefs formed earlier *in this same session*, it is marked **CORRECTED** with the evidence.

**Read §1 before touching any cron job.** It explains a trap that has now burned five consecutive sessions, including this one.

---

## 1. THE HEADLINE FINDING, `hermes cron list` IS PROFILE-SCOPED

### 1.1 What is true

There are **two independent Hermes cron stores** on this Mac. Each has its own `jobs.json`, `executions.db`, ticker process, and `output/` directory:

| Store | Path | Scheduled jobs |
|---|---|---|
| `default` (**active**) | `~/.hermes/cron/` | 22 |
| `architector` | `~/.hermes/profiles/architector/cron/` | 8 |

- `hermes profile` prints the active profile. It is currently `default`.
- `hermes cron list`, `hermes cron remove`, and `hermes cron edit` operate on the **active profile only**.
- **There is no `--profile` flag on `hermes cron`.** Verified against `hermes cron --help` and `hermes --help`.
- **Both tickers run simultaneously.** Verified: `~/.hermes/cron/ticker_heartbeat` and `~/.hermes/profiles/architector/cron/ticker_heartbeat` were both within 6 seconds of wall-clock at 15:49:29.

### 1.2 Why this matters, the five-session failure loop

Between 2026-08-06 and 2026-08-11, sessions repeatedly accused each other of hallucinating cron IDs. The mechanism:

1. A session runs `hermes cron list`, which silently shows only the active profile.
2. It finds the other session's IDs absent, absent from `jobs.json`, absent from 1,000 rows of `executions.db`, absent from `output/`. Every check agrees.
3. It concludes the other IDs were **fabricated**, and writes a blocklist into the PHASE prompts telling future sessions to purge them from memory.
4. The next session, running under the other profile, does exactly the same thing in reverse.

**Both ID sets were always real.** No model fabricated them. The verification method was profile-blind, and the resulting accusations were themselves the error, then got hardcoded into the prompt files as instructions.

**This session reproduced the same mistake.** My first verdict declared all 8 architector IDs nonexistent, citing three independent sources. All three were scoped to the default profile. See §6.1.

### 1.3 The only correct verification

Do **not** use `hermes cron list` to prove a job's absence. Run this, the heredoc body must stay at column 0, indenting it causes `IndentationError`:

```bash
python3 - <<'EOF'
import json, glob, os
paths = ['/Users/sipi/.hermes/cron/jobs.json'] + sorted(glob.glob('/Users/sipi/.hermes/profiles/*/cron/jobs.json'))
for p in paths:
    if not os.path.exists(p): continue
    prof = p.split('/')[-3] if '/profiles/' in p else 'default'
    d = json.load(open(p))
    jobs = d if isinstance(d, list) else d.get('jobs', d)
    if isinstance(jobs, dict): jobs = list(jobs.values())
    for j in jobs:
        n = j.get('name') or ''
        if any(k in n for k in ('agentshield', 'karma', 'warmup')):
            print(f"{j.get('id')}  {n:30} {(j.get('schedule_display') or ''):12} last={j.get('last_status')}  [profile: {prof}]")
EOF
```

**Absence from `hermes cron list` is not absence from the system.**

---

## 2. CURRENT TRUE CRON STATE

All 8 AgentShield jobs live in the **architector** profile. These are the only ones. They are invisible to `hermes cron list`.

```
6f33fb6cd459, agentshield-market-scout , 0 9 * * * , last: ok
707dd2d06308, agentshield-nurture      , 0 9 * * * , last: ok  (ran 15:06)
5a5a7d42e61a, agentshield-lead-processor, 0 10 * * *, last: ok
73198eb477c9, hn-karma-warmup          , 0 11 * * *, last: ok
490d890b0e6a, agentshield-github-monitor, 0 12 * * *, last: ok
c52aa796f78f, agentshield-spend-radar  , 0 12 * * *, last: ok  (ran 15:09)
a0c2caef4e81, reddit-karma-warmup      , 0 14 * * *, last: ok
1861dbcffbaf, warmup-weekly-report     , 0 10 * * 1, never fired (created Tue; Monday-only schedule; next 08-17)
```

Their run output is under `~/.hermes/profiles/architector/cron/output/<job_id>/<timestamp>.md`, **not** under `~/.hermes/cron/output/`.

### 2.1 IDs that NO LONGER EXIST, do not recreate

These nine were duplicates in the `default` profile. **Deleted this session** (§3.1). If you see them referenced anywhere, the reference is stale:

```
8ed8a7d6126e  f10ab4dfbb8f  6316254fafcc  9d312b9723ad  a0af17ac3b08
81a667e2e65e  5a5c1e22533b  479eebbfdef6  82cf0728442c
```

---

## 3. CHANGES MADE TO THE CRON SYSTEM

### 3.1 Deleted 9 duplicate jobs from the `default` profile

**Why.** Every AgentShield job existed twice at identical schedules, one copy per profile, with two tickers driving them. Consequences observed:

- **Lock contention, already fatal.** Nine default-profile jobs shared `workdir: /Users/sipi/agentshield`. `agentshield-market-scout` (`8ed8a7d6126e`) died on 08-11 with:
  > `TimeoutError: Timed out waiting for the TERMINAL_CWD read lock after 660s, another cron job (a workdir writer, or long-running readers) has held it for longer than the cron inactivity limit.`
- **Duplicate pairs demonstrably both ran**, minutes apart: hn-karma 11:01/11:05, reddit-karma 14:02/14:01, lead-processor 10:39/10:43, github-monitor 12:00/12:01.
- **Pending double-send on email.** Both `nurture` jobs were due to fire at 09:00 on 08-12 against the same `agentshield.db`. `nurture_sequence.py` guards with `PRIMARY KEY (email, day)` + `INSERT OR REPLACE`, but `get_pending_emails()` is check-then-send with no lock, a TOCTOU race that can double-send via Resend. Blast radius was 1 test address; it grows with `email_captures`.
- **`market-scout-v2` was not unique.** It wrote to the *same* `outreach/leads_$(date +%Y-%m-%d).json` as architector's market-scout, on the same 09:00 schedule. The two clobbered each other daily. Deleting it lost no capability.

**Command used:** `hermes cron remove <id>` × 9. Note: this **hard-deletes**, the entries are gone from `jobs.json`, not tombstoned.

**Verification (before/after diff of `hermes cron list`):** active profile went **31 → 22** jobs. Exactly the 9 intended IDs disappeared; `comm -13` confirmed **nothing was added or altered**. Architector's 8 confirmed intact afterward.

### 3.2 Staggered two jobs off contended minutes

| Job | Before | After | Reason |
|---|---|---|---|
| `a3091661a791` weekly-startups-to-watch (default) | `0 9 * * 1` | `20 9 * * 1` | `workdir: ~/Downloads/gitdealflow/landing`; collided Mondays with architector's two 09:00 workdir jobs |
| `0ca81089ffcf` invisibleexit-review-bucket-prune (default) | once `2026-08-22 10:00` | once `2026-08-22 10:15` | `workdir: ~/invisible-exit`; collided with architector `lead-processor` at 10:00 |

For the one-shot, `--schedule "2026-08-22 10:15"` was verified to **preserve `kind: once`**, `{"kind": "once", "run_at": "2026-08-22T10:15:00+03:00"}`, `repeat: {"times": 1, "completed": 0}`. It did not convert to a recurring cron.

### 3.3 Resulting contention state

Cross-profile `TERMINAL_CWD` contention is **fully cleared**. Zero default-profile jobs now touch `/Users/sipi/agentshield`. The two remaining same-minute pairs (09:00 market-scout+nurture, 12:00 github-monitor+spend-radar) are both **inside architector**, driven by one ticker, so they serialize rather than contend.

Six other default jobs still sit on Mon 09:00 (`Momentum Index`, `InvisibleExit IndexNow`, `weekly-startup-signal-report`, `regenerate-leaderboard`, `hirenika rank check`, plus daily `InvisibleExit Agent Check`), all have `workdir: None`, so they are **not** lock candidates. Left alone deliberately.

### 3.4 Backups

```
~/.hermes/cron/backups/jobs.json.bak-predupe-20260811-1552          (default, pre-deletion)
~/.hermes/cron/backups/architector-jobs.json.bak-predupe-20260811-1552
~/.hermes/cron/backups/jobs.json.bak-prestagger-20260811-1604
~/.hermes/cron/backups/jobs.json.bak-prenudge-20260811-1608
```

---

## 4. CODE FIX, `scripts/spend_radar.py` TELEGRAM DELIVERY

### 4.1 CORRECTED: there was never a 401, and the token was never masked

The 08-11 15:09 radar report claimed:
> *"Telegram delivery: ❌ Failed, bot token in `.env` is masked; 401 Unauthorized"*

**Both halves of that are false.** The cron agent invented them; the script never made a Telegram request.

Evidence, `getMe` against the token in `~/.hermes/.env`:
```
ok: True
bot: mk_hermes_personal_bot | id: 8880703702
```
Token is 46 chars, `<10-digit bot id>:<35-char secret>`, contains no `*` / `REDACTED` / `MASK`. It is valid and live.

### 4.2 The actual defect, a lookup miss, twice over

1. `os.environ.get("TELEGRAM_BOT_TOKEN", "")` returned `""`. Cron invokes the script as a plain subprocess (`cd /Users/sipi/agentshield && python3.11 scripts/spend_radar.py`), so Hermes' own environment is **not inherited**. Confirmed: `env | grep -c TELEGRAM_BOT_TOKEN` → `0`.
2. The fallback searched `~/.hermes/config.yaml` for `telegram_bot_token`. **That key does not exist there**, `grep -ic 'telegram_bot_token' ~/.hermes/config.yaml` → `0`. The token lives in `~/.hermes/.env`.

Result: `TELEGRAM_TOKEN` was `""`, `send_telegram()` hit its `if not TELEGRAM_TOKEN` guard, printed *"No bot token found, skipping delivery"*, and returned. **Silent skip. No HTTP call. No 401.**

### 4.3 Latent second bug, also fixed

The old fallback did `line.split(":", 1)[1]`. A Telegram token **is** `<bot_id>:<secret>`, so splitting on the first colon discards the bot id. Had anyone simply repointed the fallback at `.env` without changing the delimiter, it would have produced a **genuine** 401:

```
old split(":") -> AAHexample_secret_...   (bot id LOST -> 401)
new split("=") -> 8880703702:AAHexam...   (bot id intact)
```

### 4.4 The fix

[`scripts/spend_radar.py:24`](scripts/spend_radar.py), `_load_hermes_token()` now: env var first → `~/.hermes/.env` parsed as `KEY=value` splitting on the **first `=`** → `config.yaml` fallback via `partition(":")` keyed on the field name (for older layouts).

**Verified:**
- Loader resolves the token with `TELEGRAM_BOT_TOKEN` unset (exactly how cron runs it): 46 chars, bot-id prefix `8880703702` intact.
- `getChat?chat_id=369633431` → `ok: True`, `type: private`. **Bot can deliver to that chat.** Read-only; no message sent.
- `python3.11 -m py_compile` clean.

**Not done:** no live test message was sent (outbound action). The next natural delivery is the 12:00 `c52aa796f78f` run. Both halves of the path are already proven read-only.

**Scope check:** only `spend_radar.py` had this pattern. `nurture_sequence.py` and `send_pipeline.py` read `RESEND_API_KEY` via `os.environ.get` and are worked around by hardcoding the key in the cron prompt, see §7.1.

---

## 5. PROMPT FILES CORRECTED

The blocklists were inverted, and after §3.1 they were wrong **twice over**: they named the now-deleted default IDs as "the real ones" and the only-surviving architector IDs as "fabricated, never reference these." A session following them would have purged correct memory and recreated the exact duplicates that caused the lock timeout.

| File | Changes |
|---|---|
| `PHASE6-EXECUTION-PROMPT.md` | "TOTAL: 6 jobs. The nurture and spend-radar jobs DO NOT EXIST" → correct 8 + profile note. Removed "were FABRICATED" framing from the CONTEXT paragraph. |
| `PHASE7-AUTONOMOUS-EXECUTION.md` | Two separate stale ID lists replaced; §1B "delete these from memory" instruction inverted into an explicit warning; spend-radar output path repointed to architector. |
| `PHASE7-COMPLETE-AUTONOMOUS.md` | Phase-1 block rewritten around the cross-profile check; blocklist removed; spend-radar output path repointed. |
| `PHASE8-EXECUTE-REMAINING.md` | **Untouched.** Its `c52aa796f78f` path was correct all along, see §6.2. |

Each file now carries the live 8-job list, a `⚠️` that `hermes cron list` is profile-blind, and a dated *"Corrected 2026-08-11"* note. **Blocklists were replaced with a runnable enumeration, not a better list**, the failure mode was trusting a list, so handing the next session another list would not fix it.

**Verification:** the nine deleted IDs survive only inside the explicit correction notes (which warn against recreating them); no operational references remain. Every `cron/output/<id>` path across all four files resolves to a real directory. All bash fences in all four files pass `bash -n`. The enumeration snippet was executed verbatim as embedded in both PHASE7 files and returns exactly the 8 live jobs.

---

## 6. CORRECTIONS TO CLAIMS MADE EARLIER IN THIS SESSION

Recorded so they are not re-propagated.

### 6.1 "The 8 architector IDs do not exist", WRONG
My first verdict cited `hermes cron list`, `jobs.json`, and 1,000 rows of `executions.db`, all agreeing. **All three were scoped to the default profile.** This is the identical mistake described in §1.2. Corrected on discovering `~/.hermes/profiles/architector/cron/`.

### 6.2 "`PHASE8-EXECUTE-REMAINING.md:302` is a defect", WRONG
I reported that its `profiles/architector/cron/output/c52aa796f78f/` path pointed at a nonexistent ID and proposed repointing it at `5a5c1e22533b`. **The line was correct as written** and returns a real 8.7 KB report from 15:09. The proposed "fix" would have pointed it at an empty directory and broken a working line. **The edit was not made.**

### 6.3 Self-inflicted `IndentationError`, introduced and fixed
My first rewrite of PHASE7-COMPLETE placed the verification heredoc inside a numbered list at 3-space indentation. Copy-pasted verbatim this fails with `IndentationError: unexpected indent`. Caught by executing the snippet exactly as embedded. Now at column 0, with the surrounding list converted to bold steps so it is not re-indented, plus an inline warning.

### 6.4 "Two crons never fired, something is broken", BENIGN, and superseded
`81a667e2e65e` and `5a5c1e22533b` had never fired simply because they were created **after** their daily slots had passed (created 14:32 and 14:51; slots 09:00 and 12:00). Not broken. Both have since been deleted as duplicates; their architector twins had already done the work that day.

---

## 7. OPEN ITEMS, NOT DONE

### 7.1 Resend API key in plaintext (highest value)
The live Resend key (prefix `re_jCM6…`) is hardcoded **inside architector's nurture cron prompt**. Enumerated by `grep -rl` on 2026-08-11, it sits in cleartext in **8 locations**:

```
~/.hermes/profiles/architector/cron/jobs.json
~/.hermes/profiles/architector/cron/output/707dd2d06308/2026-08-11_15-06-28.md
/Users/sipi/agentshield/PHASE6-EXECUTION-PROMPT.md          (line 30)
/Users/sipi/agentshield/PHASE7-AUTONOMOUS-EXECUTION.md
/Users/sipi/agentshield/AGENTSHIELD-MONETISATION-PROMPT.md
/Users/sipi/agentshield/MONETISATION_PLAN.md
/Users/sipi/agentshield/outreach/state.json
/Users/sipi/agentshield/SESSION-REPORT-2026-08-11-CRON-PROFILE-FIX.md   (this file, prefix only)
```

**Five of those are git-tracked** in `kindrat86/agentshield` (`git ls-files` cross-check: the four `.md` prompt/plan files plus `outreach/state.json`; this report is untracked). Every future architector nurture run appends another `output/*.md` copy, because the job prompt is echoed verbatim into each run's report, so the count grows daily until the key is removed from the prompt.

Root cause is identical to §4.2: the scripts read `os.environ.get("RESEND_API_KEY")`, cron does not inherit Hermes' environment, so the key was inlined into the prompt as a workaround. Fixing `nurture_sequence.py` / `send_pipeline.py` the way `spend_radar.py` was fixed (§4.4) lets the key move to `~/.hermes/.env` and be stripped from all prompts.

**Rotate the key after cleanup.** It has been in cleartext on disk, in git-tracked markdown, and in cron output for an extended period. Re-run `grep -rl 'REDACTED' ~/agentshield ~/.hermes` to confirm zero hits before rotating, and check whether the six tracked files ever reached a remote.

### 7.2 The three original PHASE8 tasks, all still undone
Verified this session:

| Task | Verified state | Evidence |
|---|---|---|
| DNS `agentshield.sipiteno.com` | **Not done.** Does not resolve. | `dig +short A` and `AAAA` both empty; `curl` → "could not resolve host". Zone NS = `malcolm/paityn.ns.cloudflare.com` |
| Product Hunt | **Not submitted.** Draft copy only. | `content/producthunt-listing.md` exists; no submission record anywhere |
| Reddit posts | **Blocked at network layer.** | `outreach/reddit_warmup_log.txt`: *"API BLOCKED, Reddit network security blocked all API requests from this IP"* |

Additional: HN is rate-limited (`needs_24h_cooloff`, karma=1). GitHub outreach has **2** verifiable posts in `outreach/state.json` (agentbudget#29, openclaw#42475), **not the 6** the prompts assert.
`agentshield.fly.dev` is healthy: **HTTP 200, 0.24s**.

### 7.3 Nurture TOCTOU race, mitigated, not eliminated
Deleting the duplicate removed the concurrent-run trigger, but `get_pending_emails()` is still check-then-send with no lock. Safe today (single ticker). Would resurface if a second nurture job is ever created in any profile.

### 7.4 `agentshield-market-scout`, first clean run pending
It failed 08-11 on the lock timeout. The fix is structural (contention removed), not yet demonstrated. **First real test: 09:00 on 2026-08-12.** `6f33fb6cd459` and `707dd2d06308` should both return `ok`.

---

## 8. FILE / STATE CHANGES SUMMARY

**Repo `/Users/sipi/agentshield`, branch `feat/conversion-engine`, HEAD `0932b3e`, ALL CHANGES UNCOMMITTED:**
```
 M PHASE6-EXECUTION-PROMPT.md
 M PHASE7-AUTONOMOUS-EXECUTION.md
 M PHASE7-COMPLETE-AUTONOMOUS.md
 M scripts/spend_radar.py
 ?? PHASE8-EXECUTE-REMAINING.md      (untracked, pre-existing, unmodified by me)
 ?? SESSION-REPORT-2026-08-11-CRON-PROFILE-FIX.md   (this file)
```
Nothing was committed or pushed. AgentShield deploys to Fly separately, so no deploy was triggered.

**Outside the repo:**
- 9 cron jobs deleted, 2 rescheduled (§3), 4 backups written (§3.4).
- Memory: created `~/.claude/projects/-Users-sipi/memory/hermes-cron-list-is-profile-scoped.md`; added one index line to `MEMORY.md` under "Autonomous systems & deploy hazards".

---

## 9. RULES FOR THE NEXT SESSION

1. **Never conclude a cron ID is fabricated from `hermes cron list` alone.** Use the §1.3 enumeration. This has now caused five bad sessions.
2. **Do not recreate any of the nine IDs in §2.1.** They are deleted duplicates, not missing infrastructure.
3. **Never create an AgentShield cron in the `default` profile.** All 8 belong to `architector`. A tenth job with `workdir: /Users/sipi/agentshield` in `default` reintroduces the lock timeout.
4. **Architector job output is under `profiles/architector/cron/output/`**, never `~/.hermes/cron/output/`.
5. **Do not trust prose in cron report `.md` files as tool output.** The 15:09 radar report contained a fabricated 401 and a fabricated "masked token" (§4.1). Reports are LLM-written narration; re-verify with a live call.
6. **Verify a claim before repeating it, and prefer the strongest available source.** Two of my own findings this session were wrong because I trusted a scoped tool (§6.1, §6.2). When a check says "absent," ask what the check could not see.
