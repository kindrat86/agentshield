"""
AgentShield → Agent-Devtools emitter tests
===========================================
Verifies the emitter produces the v1 event schema correctly and that the
per-rule trace is consistent with the engine's authoritative decision.

Run: python3.11 -m unittest tests.test_emitter -v
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agentshield.engine import SpendControlEngine
from agentshield.emitter import SpendEvaluationEmitter


def _txn(amount="500.00", merchant="openai-api", category="llm_inference", **kw):
    txn = {"amount": amount, "merchant": merchant, "category": category}
    txn.update(kw)
    return txn


class TestEmitter(unittest.TestCase):

    def setUp(self):
        self.engine = SpendControlEngine()
        self.emitter = SpendEvaluationEmitter(self.engine)

    def test_blocked_event_matches_schema_and_decision(self):
        rules = [
            {"id": "r1", "type": "transaction_limit", "priority": 1,
             "params": {"max_amount": 250}, "action": "BLOCK"},
            {"id": "r2", "type": "velocity", "priority": 2,
             "params": {"window_minutes": 60, "max_count": 10}, "action": "FLAG"},
        ]
        txn = _txn(amount="500.00", agent_id="agent_7", session_id="sess_9",
                   timestamp="2026-08-13T10:29:59Z")
        event = self.emitter.build_event(txn, rules, trace_id="trace_42")

        # envelope
        self.assertEqual(event["schema_version"], "1.0")
        self.assertEqual(event["event_type"], "agentshield.spend.evaluation")
        self.assertEqual(event["trace_id"], "trace_42")
        self.assertEqual(event["agent_id"], "agent_7")
        self.assertEqual(event["session_id"], "sess_9")

        # transaction echo
        self.assertEqual(event["transaction"]["amount"], "500.00")
        self.assertEqual(event["transaction"]["merchant"], "openai-api")

        # decision is identical to the engine's authoritative result
        self.assertEqual(event["decision"], self.engine.evaluate(txn, rules, []))

        # per-rule trace
        evals = event["evaluation"]
        self.assertEqual(evals[0]["rule_id"], "r1")
        self.assertEqual(evals[0]["outcome"], "triggered")
        self.assertEqual(evals[0]["detail"]["actual"], "500.00")
        self.assertEqual(evals[0]["detail"]["limit"], "250.00")
        self.assertEqual(evals[1]["outcome"], "not_reached")

    def test_approved_event_all_rules_passed(self):
        rules = [
            {"id": "r1", "type": "transaction_limit", "priority": 1,
             "params": {"max_amount": 1000}, "action": "BLOCK"},
            {"id": "r2", "type": "merchant_allowlist", "priority": 2,
             "params": {"allowed": ["openai-api"]}, "action": "BLOCK"},
        ]
        event = self.emitter.build_event(_txn(amount="10.00"), rules)
        self.assertEqual(event["decision"]["decision"], "APPROVED")
        for e in event["evaluation"]:
            self.assertEqual(e["outcome"], "passed")

    def test_skipped_rule_missing_params(self):
        rules = [
            {"id": "r1", "type": "transaction_limit", "priority": 1,
             "params": {}, "action": "BLOCK"},
            {"id": "r2", "type": "merchant_allowlist", "priority": 2,
             "params": {"allowed": ["openai-api"]}, "action": "BLOCK"},
        ]
        event = self.emitter.build_event(_txn(amount="10.00"), rules)
        evals = event["evaluation"]
        self.assertEqual(evals[0]["outcome"], "skipped")
        self.assertEqual(evals[1]["outcome"], "passed")

    def test_ndjson_serializable_and_decodable(self):
        rules = [
            {"id": "r1", "type": "transaction_limit", "priority": 1,
             "params": {"max_amount": 250}, "action": "BLOCK"},
        ]
        event = self.emitter.build_event(_txn(amount="500.00"), rules)
        line = self.emitter.to_ndjson(event)
        decoded = json.loads(line)
        self.assertEqual(decoded["decision"]["decision"], "BLOCKED")
        self.assertEqual(decoded["evaluation"][0]["detail"]["limit"], "250.00")

    def test_callback_emit(self):
        rules = [
            {"id": "r1", "type": "transaction_limit", "priority": 1,
             "params": {"max_amount": 250}, "action": "BLOCK"},
        ]
        captured = []
        event = self.emitter.emit(_txn(amount="500.00"), rules, on_event=captured.append)
        self.assertEqual(captured[0], event)

    def test_daily_total_detail_matches_reason(self):
        rules = [
            {"id": "r1", "type": "daily_total", "priority": 1,
             "params": {"max_daily": 2000}, "action": "BLOCK"},
        ]
        prior = [
            {"amount": "1900.00", "merchant": "openai-api", "category": "llm",
             "timestamp": "2026-08-13T09:00:00Z", "agent_id": "a1"},
        ]
        txn = _txn(amount="150.00", timestamp="2026-08-13T10:00:00Z", agent_id="a1")
        event = self.emitter.build_event(txn, rules, prior)
        self.assertEqual(event["decision"]["decision"], "BLOCKED")
        detail = event["evaluation"][0]["detail"]
        self.assertEqual(detail["daily_total"], "2050.00")
        self.assertEqual(detail["max_daily"], "2000.00")

    def test_invalid_transaction_empty_trace(self):
        event = self.emitter.build_event({"amount": "abc"}, [])
        self.assertEqual(event["decision"]["decision"], "FLAGGED")
        self.assertEqual(event["evaluation"], [])

    def test_parity_with_core_engine(self):
        from core.engine import SpendControlEngine as CoreEngine
        rules = [
            {"id": "r1", "type": "transaction_limit", "priority": 1,
             "params": {"max_amount": 250}, "action": "BLOCK"},
        ]
        txn = _txn(amount="500.00")
        pub = self.engine.evaluate_with_trace(txn, rules, [])
        core = CoreEngine().evaluate_with_trace(txn, rules, [])
        self.assertEqual(pub, core)


if __name__ == "__main__":
    unittest.main()
