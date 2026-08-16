# SHACKLE SP/1.0 Conformance

This documents the result of running AgentShield's engine against the 15
published conformance vectors from
[github.com/Fame510/SHACKLE](https://github.com/Fame510/SHACKLE), as
challenged by @Fame510 on
[AutoGPT #12700](https://github.com/Significant-Gravitas/AutoGPT/issues/12700).

The SP/1.0 fixtures are (C) 2026 Dante Bullock, CC-BY-4.0
(see `LICENSE-SPEC.md` in the SHACKLE repo). The runnable harness is
`scripts/conformance_shackle_sp1.py`; it writes `conformance-shackle-sp1.json`
alongside this file.

## Verdict mapping

| AgentShield decision | SHACKLE verdict |
| --- | --- |
| `APPROVED` | `ALLOW` |
| `BLOCKED` | `DENY` |
| `REVIEW` | `HITL` |
| `FLAGGED` | (no SHACKLE equivalent; a medium-severity signal) |

AgentShield mediates **money** (`{amount, merchant, category}`); SHACKLE
mediates **tool calls** (`{tool_name, params, nonce}`). The two surfaces only
overlap on budget, nonce, circuit, and review escalation, so the mapping is
partial by construction. Vectors with no AgentShield surface are reported as
`NO_EQUIVALENT`, not as a failure.

## Results

| Status | Vector | SHACKLE | AgentShield |
| --- | --- | --- | --- |
| MATCH | `allow_within_thresholds` | ALLOW | ALLOW |
| MATCH | `deny_budget_exhausted` | DENY | DENY |
| PARTIAL | `deny_max_repeat` | DENY | FLAG |
| MATCH | `deny_circuit_open` | DENY | DENY |
| MATCH | `deny_duplicate_nonce` | DENY | DENY |
| MATCH | `hitl_threshold` | HITL | HITL |
| MATCH | `hitl_always` | HITL | HITL |
| MATCH | `malformed_non_canonical_input` | DENY | DENY |
| NO_EQUIVALENT | `untestable_opaque_context` | HITL | - |
| NO_EQUIVALENT | `hitl_transition_approve` | ALLOW | - |
| NO_EQUIVALENT | `hitl_transition_reject` | DENY | - |
| NO_EQUIVALENT | `hitl_transition_modify` | ALLOW | - |
| NO_EQUIVALENT | `hitl_transition_defer_escalate` | HITL | - |
| NO_EQUIVALENT | `hitl_transition_duplicate_resume` | DENY | - |
| MATCH | `concurrent_budget_overrun` | DENY | DENY |

Summary: **8 MATCH, 1 PARTIAL, 6 NO_EQUIVALENT**.

Before the envelope work in this PR, the same run produced **3 MATCH, 1 DIVERGE,
1 PARTIAL, 10 NO_EQUIVALENT**. The four changes below moved five vectors from
DIVERGE/NO_EQUIVALENT to MATCH.

## What closed the gap

Four changes to the engine (`core/engine.py` and the `agentshield/engine.py`
PyPI twin), each mirrored by an eval-gym scenario:

1. **HITL verdict tier.** `_make_result` now accepts `REVIEW` (and `HITL` as an
   alias), and a new `hitl_threshold` rule type escalates to REVIEW either on a
   budget fraction (`mode: on_threshold`, `threshold`, `max_budget`) or
   unconditionally (`mode: always`). Closes `hitl_threshold` and `hitl_always`.
2. **Fail-closed malformed input.** Non-canonicalizable transactions
   (missing `amount`/`merchant`/`category`, or an unparseable amount) now return
   `BLOCKED` with high severity instead of `FLAGGED`. Closes
   `malformed_non_canonical_input`.
3. **Nonce / replay protection.** A `replay` rule type rejects a transaction
   whose `nonce` (configurable field) already appears in `prior_transactions`.
   Closes `deny_duplicate_nonce`.
4. **Circuit breaker.** A `circuit` rule type denies all calls while a
   `circuit_tripped` flag (stamped by the runtime) is set. The engine holds the
   deterministic enforcement; the runtime owns the latch, mirroring SHACKLE's
   `decide()` (pure) vs `ExecutionState.trip_circuit()` (runtime) split. Closes
   `deny_circuit_open`.

The `concurrent_budget_overrun` vector already matched: `session_budget` sums
the call plus prior session spend and blocks when the total exceeds the cap,
which is the pre-mutation "would push it negative" guarantee under a
read-modify-write.

## Remaining gaps (structural, not bugs)

- **`untestable_opaque_context` (1 vector).** AgentShield is a spend firewall;
  its transaction has no agent "context" field to evaluate deterministically.
  Adding one would mean importing an evaluable-context concept that is outside
  the spend-control surface.
- **The five HITL transition vectors.** SHACKLE's `pending_transition` is a
  single-use capability bound to `(nonce, args_digest)` with `terminal_status`
  semantics (approve / reject / modify / defer / duplicate-resume). AgentShield
  has no equivalent authorization object, and building one is a product-model
  decision, not a portability fix.
- **`deny_max_repeat` (partial).** AgentShield's `velocity` rule counts calls in
  a rolling time window; SHACKLE's `max_repeat` guards against the same tool
  called with the same input. Both catch runaway loops, but they are not the
  same predicate, and `velocity` flags rather than denies by default.

## Reason vocabulary

AgentShield verdicts now align with the SP/1.0 envelope, but its `reason`
strings remain human-readable prose, not the stable SHACKLE vocabulary
(`budget_exhausted`, `budget_overrun`, `policy_violation:duplicate_nonce`,
...). This is the portability gap Fame510 named and is the honest next step for
full reason-level conformance.

## Reproduce

```
~/.local/bin/python3.11 scripts/conformance_shackle_sp1.py
```
