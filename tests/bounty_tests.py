import unittest
from agentshield.engine import SpendControlEngine
from decimal import Decimal
from datetime import datetime, timezone

class TestBountyBypasses(unittest.TestCase):
    def setUp(self):
        self.engine = SpendControlEngine()

    def test_merchant_allowlist_empty_string_bypass(self):
        """Bypass 1: Empty merchant string bypasses allowlist."""
        rules = [{
            "id": "rule_1",
            "type": "merchant_allowlist",
            "priority": 1,
            "params": {"allowed": ["TrustedCorp"]},
            "action": "BLOCK"
        }]
        transaction = {
            "amount": "100.00",
            "merchant": "",  # Should be blocked, but is approved
            "category": "software"
        }
        result = self.engine.evaluate(transaction, rules, [])
        self.assertEqual(result['decision'], 'BLOCKED', "Empty merchant should be blocked by allowlist")

    def test_category_block_empty_string_bypass(self):
        """Bypass 2: Empty category string bypasses blocklist if explicitly blocked."""
        rules = [{
            "id": "rule_2",
            "type": "category_block",
            "priority": 1,
            "params": {"blocked": [""]},
            "action": "BLOCK"
        }]
        transaction = {
            "amount": "100.00",
            "merchant": "Casino",
            "category": "" 
        }
        result = self.engine.evaluate(transaction, rules, [])
        self.assertEqual(result['decision'], 'BLOCKED', "Empty category should be blocked if explicitly in blocklist")

    def test_daily_total_missing_timestamp_bypass(self):
        """Bypass 3: Missing timestamp bypasses daily total limits."""
        rules = [{
            "id": "rule_3",
            "type": "daily_total",
            "priority": 1,
            "params": {"max_daily": "100.00"},
            "action": "BLOCK"
        }]
        prior = [{"amount": "80.00", "merchant": "A", "category": "B", "timestamp": datetime.now(timezone.utc).isoformat()}]
        transaction = {
            "amount": "50.00",
            "merchant": "A",
            "category": "B"
            # Missing timestamp
        }
        result = self.engine.evaluate(transaction, rules, prior)
        self.assertEqual(result['decision'], 'BLOCKED', "Missing timestamp should not bypass daily total")

    def test_cascade_cost_negative_probability_bypass(self):
        """Bypass 4: Negative failure probability bypasses cascade cost limits."""
        rules = [{
            "id": "rule_4",
            "type": "cascade_cost",
            "priority": 1,
            "params": {"max_cascade_cost": "50.00", "reversal_cost": "100.00"},
            "action": "BLOCK"
        }]
        # Without fix, 60 + (-1.0 * 100) = -40 (Approved)
        # With fix, 60 + (0.0 * 100) = 60 (Blocked)
        transaction = {
            "amount": "60.00",
            "merchant": "A",
            "category": "B",
            "fail_probability": "-1.0" 
        }
        result = self.engine.evaluate(transaction, rules, [])
        self.assertEqual(result['decision'], 'BLOCKED', "Negative fail_probability should be clamped to 0")

    def test_session_reset_bypass(self):
        """Bypass 5: Missing session_id allows resetting session budget per call."""
        rules = [{
            "id": "rule_5",
            "type": "session_budget",
            "priority": 1,
            "params": {"max_session": "100.00"},
            "action": "BLOCK"
        }]
        prior = [{"amount": "80.00", "merchant": "A", "category": "B"}] # Missing session_id
        transaction = {
            "amount": "50.00",
            "merchant": "A",
            "category": "B"
            # Missing session_id
        }
        result = self.engine.evaluate(transaction, rules, prior)
        self.assertEqual(result['decision'], 'BLOCKED', "Missing session_id should not reset budget")

if __name__ == '__main__':
    unittest.main()
