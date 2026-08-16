#!/usr/bin/env python3
"""Run the SHACKLE SP/1.0 conformance vectors against the AgentShield engine.

Fame510's challenge (AutoGPT #12700) was to run AgentShield against the 15
published conformance vectors from github.com/Fame510/SHACKLE and diff the
outcomes. This harness maps each vector onto AgentShield's decision surface
(engine.evaluate) and reports MATCH / DIVERGE / PARTIAL / NO_EQUIVALENT.

Verdict mapping: APPROVED -> ALLOW, BLOCKED -> DENY, REVIEW -> HITL, FLAGGED -> FLAG.
The SP/1.0 vectors are (C) 2026 Dante Bullock, CC-BY-4.0 (see LICENSE-SPEC.md
in the SHACKLE repo). Only the semantic inputs needed to reproduce each verdict
are encoded here, not the fixtures' canonical hashes.

Usage:
    ~/.local/bin/python3.11 scripts/conformance_shackle_sp1.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.engine import SpendControlEngine

engine = SpendControlEngine()
VERDICT_MAP = {"APPROVED": "ALLOW", "BLOCKED": "DENY", "REVIEW": "HITL", "FLAGGED": "FLAG"}


def _txn(**kw):
    t = {"id": "t", "agent_id": "agent_a", "amount": 10.0, "merchant": "openai-api",
         "category": "llm_inference", "timestamp": "2026-08-10T10:00:00Z"}
    t.update(kw)
    return t


def _sb(max_session, action="BLOCK"):
    return {"id": "sb", "type": "session_budget", "priority": 1,
            "params": {"max_session": max_session}, "action": action}


# Each vector: (name, SHACKLE verdict, SHACKLE reason, builder -> (rules, txn, priors)).
# NO_EQUIVALENT vectors have no builder (None): AgentShield has no matching surface.
VECTORS = [
    ("allow_within_thresholds", "ALLOW", "within_thresholds",
     lambda: ([_sb(1)], _txn(amount=0.01), [])),
    ("deny_budget_exhausted", "DENY", "budget_exhausted",
     lambda: ([_sb(1)], _txn(amount=0.02), [_txn(amount=1.0)])),
    ("deny_max_repeat", "DENY", "max_repeat_exceeded",
     lambda: ([{"id": "v", "type": "velocity", "priority": 1,
                "params": {"window_minutes": 60, "max_count": 2}, "action": "FLAG"}],
              _txn(amount=0.01), [_txn(amount=0.01), _txn(amount=0.01)])),
    ("deny_circuit_open", "DENY", "circuit_open",
     lambda: ([{"id": "c", "type": "circuit", "priority": 1, "params": {}, "action": "BLOCK"}],
              _txn(circuit_tripped=True), [])),
    ("deny_duplicate_nonce", "DENY", "policy_violation:duplicate_nonce",
     lambda: ([{"id": "r", "type": "replay", "priority": 1, "params": {}, "action": "BLOCK"}],
              _txn(nonce=7), [_txn(nonce=7)])),
    ("hitl_threshold", "HITL", "budget_threshold",
     lambda: ([{"id": "h", "type": "hitl_threshold", "priority": 1,
                "params": {"max_budget": 1, "threshold": 0.15}, "action": "BLOCK"}],
              _txn(amount=0.01), [_txn(amount=0.9)])),
    ("hitl_always", "HITL", "hitl_all_calls",
     lambda: ([{"id": "h", "type": "hitl_threshold", "priority": 1,
                "params": {"mode": "always"}, "action": "BLOCK"}],
              _txn(amount=0.0), [])),
    ("malformed_non_canonical_input", "DENY", "policy_violation:malformed_input",
     lambda: ([], {"id": "t", "merchant": "m", "category": "c"}, [])),
    ("untestable_opaque_context", "HITL", "fail_closed:opaque_context", None),
    ("hitl_transition_approve", "ALLOW", "hitl_transition:approve", None),
    ("hitl_transition_reject", "DENY", "hitl_transition:reject", None),
    ("hitl_transition_modify", "ALLOW", "hitl_transition:modify_successor", None),
    ("hitl_transition_defer_escalate", "HITL", "hitl_transition:defer_escalate", None),
    ("hitl_transition_duplicate_resume", "DENY", "policy_violation:duplicate_resume_no_effect", None),
    ("concurrent_budget_overrun", "DENY", "budget_overrun",
     lambda: ([_sb(1)], _txn(amount=0.15), [_txn(amount=0.9)])),
]


def main():
    rows = []
    for name, expected_verdict, expected_reason, builder in VECTORS:
        if builder is None:
            rows.append({"name": name, "expected": expected_verdict,
                         "got": None, "status": "NO_EQUIVALENT",
                         "note": "no AgentShield surface for this vector"})
            continue
        rules, txn, priors = builder()
        result = engine.evaluate(txn, rules, priors)
        got = VERDICT_MAP[result["decision"]]
        if got == expected_verdict:
            status = "MATCH"
        elif name == "deny_max_repeat":
            # velocity is a time-window counter, not a same-tool+same-input guard;
            # it flags rather than denies, and the semantics are not equivalent.
            status = "PARTIAL"
        else:
            status = "DIVERGE"
        rows.append({"name": name, "expected": expected_verdict, "got": got,
                     "status": status, "agent_reason": result.get("reason")})

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    print("SHACKLE SP/1.0 x AgentShield conformance")
    print("verdict map: APPROVED->ALLOW, BLOCKED->DENY, REVIEW->HITL\n")
    print(f"{'STATUS':<12} {'VECTOR':<34} {'SHACKLE':<8} {'AGENTSHIELD':<10}")
    print("-" * 66)
    for r in rows:
        got = r["got"] or "-"
        print(f"{r['status']:<12} {r['name']:<34} {r['expected']:<8} {got:<10}")
    print("-" * 66)
    print(f"summary: {counts}")

    out = {"summary": counts, "rows": rows}
    with open(os.path.join(os.path.dirname(__file__), '..', 'docs',
                           'conformance-shackle-sp1.json'), 'w') as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("wrote docs/conformance-shackle-sp1.json")


if __name__ == '__main__':
    main()
