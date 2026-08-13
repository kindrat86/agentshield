"""AgentShield — session_budget `None`-session bypass regression tests (issue #7).

Verifies that a `session_id` equal to `None` is treated as a real "default" session:

  * prior transactions whose `session_id` is also `None` are summed into the same
    bucket, so the budget can no longer be bypassed by omitting the id;
  * named sessions stay isolated from the `None` ("unnamed") bucket and from each
    other;
  * all arithmetic stays on ``Decimal`` (never float), so cumulative amounts are
    exact;
  * ``evaluate_with_trace`` emits the correct ``actual``-vs-``limit`` detail even
    when ``session_id`` is ``None``;
  * the ``require_session_id`` strict guardrail blocks/flags a transaction whose
    ``session_id`` is missing.

Run with pytest  or with the project's unittest runner:
    python3 -m pytest tests/test_session_budget.py -v
    python3 -m unittest tests.test_session_budget -v
"""

import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentshield.engine import SpendControlEngine
from agentshield.emitter import SpendEvaluationEmitter


def _txn(amount="100.00", merchant="openai-api", category="llm_inference", **kw):
    txn = {"amount": amount, "merchant": merchant, "category": category}
    txn.update(kw)
    return txn


def _prior(amount, session_id, merchant="openai-api", category="llm_inference"):
    return {"amount": str(amount), "merchant": merchant, "category": category,
            "session_id": session_id}


def _session_rule(max_session, **extra_params):
    params = {"max_session": max_session}
    params.update(extra_params)
    return [{"id": "sb1", "type": "session_budget", "priority": 1,
             "params": params, "action": "BLOCK"}]


class TestSessionBudgetNoneBypass(unittest.TestCase):
    """Case 1 — the `session_id is None` bypass is closed."""

    def setUp(self):
        self.engine = SpendControlEngine()

    def test_prior_none_session_counts_toward_budget(self):
        """$450 of None-session priors + $100 None-session txn > $500 cap → BLOCKED."""
        txn = _txn(amount="100.00", session_id=None)
        prior = [
            _prior("200.00", None),
            _prior("250.00", None),
        ]
        rules = _session_rule(500)
        result = self.engine.evaluate(txn, rules, prior)
        self.assertEqual(result["decision"], "BLOCKED")

    def test_prior_absent_session_key_counts_toward_budget(self):
        """A prior lacking the session field entirely is also part of the default bucket."""
        txn = _txn(amount="100.00", session_id=None)
        prior = [{"amount": str(Decimal("450.00")), "merchant": "openai-api",
                  "category": "llm_inference"}]
        result = self.engine.evaluate(txn, rules=_session_rule(500), prior_transactions=prior)
        self.assertEqual(result["decision"], "BLOCKED")

    def test_none_session_under_limit_is_approved(self):
        """Within the cap, a None-session txn that stays under the limit is approved."""
        txn = _txn(amount="40.00", session_id=None)
        prior = [_prior("60.00", None)]
        # 40 + 60 = 100 <= 500 → approved
        result = self.engine.evaluate(txn, _session_rule(500), prior)
        self.assertEqual(result["decision"], "APPROVED")


class TestSessionBudgetIsolation(unittest.TestCase):
    """Case 2 — named sessions never bleed into the None bucket (or each other)."""

    def setUp(self):
        self.engine = SpendControlEngine()
        # A heavy sess_1 history that must NOT affect other sessions / None.
        self.heavy_prior = [
            _prior("400.00", "sess_1"),
            _prior("400.00", "sess_1"),
        ]

    def test_none_session_ignores_sess_1_prior(self):
        """None-session txn is NOT counted against sess_1's spend."""
        txn = _txn(amount="100.00", session_id=None)
        # 100 + (nothing) = 100 <= 500 → approved, despite $800 in sess_1.
        result = self.engine.evaluate(txn, _session_rule(500), self.heavy_prior)
        self.assertEqual(result["decision"], "APPROVED")

    def test_sess_2_ignores_sess_1_prior(self):
        """Different named sessions are isolated from each other."""
        txn = _txn(amount="100.00", session_id="sess_2")
        result = self.engine.evaluate(txn, _session_rule(500), self.heavy_prior)
        self.assertEqual(result["decision"], "APPROVED")

    def test_sess_1_counts_only_sess_1_prior(self):
        """sess_1 txn excludes None-session and sess_2 priors."""
        txn = _txn(amount="450.00", session_id="sess_1")
        prior = [
            _prior("100.00", None),       # default bucket — must NOT count
            _prior("100.00", "sess_2"),   # other session — must NOT count
            _prior("50.00", "sess_1"),    # same session — counts
        ]
        # 450 + 50 = 500 <= 500 → approved; were the others counted it would reach 700.
        result = self.engine.evaluate(txn, _session_rule(500), prior)
        self.assertEqual(result["decision"], "APPROVED")

    def test_named_txn_ignores_priors_with_missing_session_key(self):
        """A named session txn must not absorb priors lacking a session_id."""
        txn = _txn(amount="490.00", session_id="sess_1")
        prior = [{"amount": "100.00", "merchant": "openai-api", "category": "llm_inference"}]
        result = self.engine.evaluate(txn, _session_rule(500), prior)
        # 490 <= 500 → approved; the 100 with no session key must not count against sess_1.
        self.assertEqual(result["decision"], "APPROVED")


class TestSessionBudgetDecimalPrecision(unittest.TestCase):
    """Case 3 — Decimal-exact arithmetic; never float."""

    def setUp(self):
        self.engine = SpendControlEngine()

    def test_0_10_plus_0_20_is_exactly_0_30(self):
        """float(0.1)+float(0.2)=0.30000...4 would wrongly BLOCK; Decimal keeps it exact."""
        txn = _txn(amount="0.20", session_id=None)
        prior = [_prior("0.10", None)]
        rules = _session_rule("0.30")
        # 0.30 is NOT > 0.30 → approved. Under float math this would exceed and BLOCK.
        result = self.engine.evaluate(txn, rules, prior)
        self.assertEqual(result["decision"], "APPROVED")

    def test_0_31_does_exceed_0_30(self):
        """Sub-penny precision is preserved: 0.31 > 0.30 → BLOCKED."""
        txn = _txn(amount="0.21", session_id=None)
        prior = [_prior("0.10", None)]
        result = self.engine.evaluate(txn, _session_rule("0.30"), prior)
        self.assertEqual(result["decision"], "BLOCKED")

    def test_trace_reports_exact_decimal_session_total(self):
        """The trace session_total carries full Decimal precision on a trigger."""
        txn = _txn(amount="0.20", session_id=None)
        prior = [_prior("0.11", None)]
        traced = self.engine.evaluate_with_trace(txn, _session_rule("0.30"), prior)
        self.assertEqual(traced["decision"]["decision"], "BLOCKED")
        entry = traced["evaluation"][0]
        self.assertEqual(entry["outcome"], "triggered")
        self.assertEqual(entry["detail"]["session_total"], "0.31")  # not 0.31000...4005
        self.assertEqual(Decimal(entry["detail"]["session_total"]), Decimal("0.31"))


class TestSessionBudgetTrace(unittest.TestCase):
    """evaluate_with_trace emits actual-vs-limit detail with a None session_id."""

    def setUp(self):
        self.engine = SpendControlEngine()
        self.emitter = SpendEvaluationEmitter(self.engine)

    def test_trace_detail_when_none_session_blocked(self):
        txn = _txn(amount="100.00", session_id=None)
        prior = [_prior("200.00", None), _prior("250.00", None)]
        traced = self.engine.evaluate_with_trace(txn, _session_rule(500), prior)
        self.assertEqual(traced["decision"]["decision"], "BLOCKED")
        entry = traced["evaluation"][0]
        self.assertEqual(entry["type"], "session_budget")
        self.assertEqual(entry["outcome"], "triggered")
        # actual (session_total) vs limit (max_session) as Decimal-safe strings.
        self.assertEqual(entry["detail"]["session_total"], "550.00")
        self.assertEqual(entry["detail"]["max_session"], "500.00")
        self.assertIsNone(entry["detail"]["session_id"])

    def test_emitter_event_detail_when_none_session(self):
        rules = _session_rule(500)
        txn = _txn(amount="150.00", session_id=None)
        prior = [_prior("400.00", None), _prior("300.00", "sess_2")]
        event = self.emitter.build_event(txn, rules, prior)
        self.assertEqual(event["decision"]["decision"], "BLOCKED")
        entry = event["evaluation"][0]
        self.assertEqual(entry["detail"]["session_total"], "550.00")  # 150 + only the None prior
        self.assertEqual(entry["detail"]["max_session"], "500.00")

    def test_trace_parity_between_public_and_core_engines(self):
        from core.engine import SpendControlEngine as CoreEngine
        txn = _txn(amount="100.00", session_id=None)
        prior = [_prior("450.00", None)]
        rules = _session_rule(500)
        pub = self.engine.evaluate_with_trace(txn, rules, prior)
        core = CoreEngine().evaluate_with_trace(txn, rules, prior)
        self.assertEqual(pub, core)
        self.assertEqual(pub["decision"]["decision"], "BLOCKED")


class TestSessionBudgetStrictGuardrail(unittest.TestCase):
    """require_session_id — strict mode blocks/flags a None session_id."""

    def setUp(self):
        self.engine = SpendControlEngine()

    def test_require_session_id_blocks_none(self):
        """With require_session_id=True, a None-session txn is blocked up-front."""
        txn = _txn(amount="1.00", session_id=None)
        prior = [_prior("10.00", None)]
        rules = _session_rule(500, require_session_id=True)
        result = self.engine.evaluate(txn, rules, prior)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(result["rule_triggered"], "sb1")
        self.assertIn("session_id is required", result["reason"])

    def test_require_session_id_flags_when_action_flag(self):
        txn = _txn(amount="1.00", session_id=None)
        rules = [{"id": "sb1", "type": "session_budget", "priority": 1,
                  "params": {"max_session": 500, "require_session_id": True},
                  "action": "FLAG"}]
        result = self.engine.evaluate(txn, rules, [])
        self.assertEqual(result["decision"], "FLAGGED")

    def test_require_session_id_allows_present_session(self):
        """A present session_id is not penalised by the strict guardrail."""
        txn = _txn(amount="10.00", session_id="sess_1")
        result = self.engine.evaluate(txn, _session_rule(500, require_session_id=True), [])
        self.assertEqual(result["decision"], "APPROVED")

    def test_guardrail_not_active_by_default(self):
        """Without require_session_id, None sessions are summed (not blocked)."""
        txn = _txn(amount="10.00", session_id=None)
        prior = [_prior("10.00", None)]
        result = self.engine.evaluate(txn, _session_rule(500), prior)
        # 20 <= 500 → approved, NOT blocked by a guardrail.
        self.assertEqual(result["decision"], "APPROVED")


if __name__ == "__main__":
    unittest.main()
