"""
Test for decimal precision overflow fix (GitHub issue #5).

The bug: float 1.0000000000000001 == 1.0 in Python, so when passed as a float
to the engine, it was treated as exactly 1.0 and APPROVED against a max_amount=1
limit. The fix ensures that string amounts preserve full precision, and documents
that float inputs lose precision at assignment time (caller responsibility).
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agentshield.engine import SpendControlEngine


class TestDecimalPrecisionOverflow(unittest.TestCase):
    """Regression tests for decimal precision overflow bypass."""

    def setUp(self):
        self.engine = SpendControlEngine()
        self.rules = [
            {'id': 'r1', 'type': 'transaction_limit', 'priority': 1,
             'params': {'max_amount': 1}, 'action': 'BLOCK'},
        ]

    def test_string_amount_exceeding_limit_is_blocked(self):
        """String amount '1.0000000000000001' must be BLOCKED (preserves precision)."""
        txn = {
            'amount': '1.0000000000000001',
            'merchant': 'openai-api',
            'category': 'llm_inference',
        }
        result = self.engine.evaluate(txn, self.rules, [])
        self.assertEqual(result['decision'], 'BLOCKED')
        self.assertIn('exceeds limit', result['reason'])

    def test_float_amount_at_limit_is_approved(self):
        """Float 1.0000000000000001 == 1.0 in Python, so it's APPROVED (float limitation)."""
        txn = {
            'amount': 1.0000000000000001,
            'merchant': 'openai-api',
            'category': 'llm_inference',
        }
        result = self.engine.evaluate(txn, self.rules, [])
        # Float precision loss means this IS 1.0, which equals the limit
        self.assertEqual(result['decision'], 'APPROVED')

    def test_float_amount_clearly_exceeding_limit_is_blocked(self):
        """Float 1.000000000000001 has enough precision to be distinct from 1.0."""
        txn = {
            'amount': 1.000000000000001,
            'merchant': 'openai-api',
            'category': 'llm_inference',
        }
        result = self.engine.evaluate(txn, self.rules, [])
        self.assertEqual(result['decision'], 'BLOCKED')

    def test_exact_limit_is_approved(self):
        """Amount exactly equal to max_amount should be APPROVED."""
        txn = {'amount': 1.0, 'merchant': 'x', 'category': 'y'}
        result = self.engine.evaluate(txn, self.rules, [])
        self.assertEqual(result['decision'], 'APPROVED')

    def test_below_limit_is_approved(self):
        """Amount below max_amount should be APPROVED."""
        txn = {'amount': 0.99, 'merchant': 'x', 'category': 'y'}
        result = self.engine.evaluate(txn, self.rules, [])
        self.assertEqual(result['decision'], 'APPROVED')

    def test_extreme_precision_string_is_blocked(self):
        """Extremely high precision string amount exceeding limit is BLOCKED."""
        txn = {
            'amount': '1.' + '0' * 50 + '1',
            'merchant': 'x',
            'category': 'y',
        }
        result = self.engine.evaluate(txn, self.rules, [])
        self.assertEqual(result['decision'], 'BLOCKED')

    def test_decimal_amount_preserves_precision(self):
        """Decimal input preserves full precision."""
        from decimal import Decimal
        txn = {
            'amount': Decimal('1.0000000000000001'),
            'merchant': 'x',
            'category': 'y',
        }
        result = self.engine.evaluate(txn, self.rules, [])
        self.assertEqual(result['decision'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
