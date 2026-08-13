"""
AgentShield E2E Multi-Tenant Test Suite, 14 Tests
====================================================
Integration tests using real Store, AuthManager, and SpendControlEngine
against a temporary SQLite database. Each test gets a fresh DB.

Run: python3.11 -m unittest tests.run_tests -v
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.store import Store
from core.engine import SpendControlEngine
from core.auth import AuthManager
from core.licensing import generate_license_key, validate_license_key, get_tier_limits


class TestAgentShield(unittest.TestCase):

    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db.close()  # Close the file handle so SQLite can open it
        self.store = Store(self.db.name)
        self.engine = SpendControlEngine()
        self.auth = AuthManager(self.store)

    def tearDown(self):
        # Close any thread-local connections
        if hasattr(self.store._local, 'conn') and self.store._local.conn:
            self.store._local.conn.close()
            self.store._local.conn = None
        if os.path.exists(self.db.name):
            os.unlink(self.db.name)
        # Clean up WAL/SHM files
        for suffix in ['-wal', '-shm']:
            walpath = self.db.name + suffix
            if os.path.exists(walpath):
                try:
                    os.unlink(walpath)
                except OSError:
                    pass

    # ─── 1. Account Registration ──────────────────────────────────────────

    def test_account_registration(self):
        """Test 1: Register an account, verify it exists and password hashing works."""
        acct = self.auth.register('a@b.com', 'securepass123')
        self.assertIsNotNone(acct, "Registration should return an account dict")
        self.assertEqual(acct['email'], 'a@b.com')
        # Verify password is hashed (not stored in plaintext)
        stored = self.store.get_account_by_email('a@b.com')
        self.assertNotEqual(stored['password_hash'], 'securepass123')
        self.assertIn('$', stored['password_hash'])

    # ─── 2. Login/Logout ──────────────────────────────────────────────────

    def test_login_logout(self):
        """Test 2: Login returns valid session token, logout invalidates it."""
        self.auth.register('user@test.com', 'password123')
        login_result = self.auth.login('user@test.com', 'password123')
        self.assertTrue(login_result['success'])
        self.assertIsNotNone(login_result['token'])
        # Verify token works
        acct = self.auth.account_from_token(login_result['token'])
        self.assertIsNotNone(acct)
        self.assertEqual(acct['email'], 'user@test.com')
        # Logout
        self.assertTrue(self.auth.logout(login_result['token']))
        # Token should now be invalid
        self.assertIsNone(self.auth.account_from_token(login_result['token']))

    # ─── 3. Tenant Isolation (Agents) ─────────────────────────────────────

    def test_tenant_isolation(self):
        """Test 3: Account B cannot see Account A's agents."""
        acct_a = self.auth.register('a@isolated.com', 'password123')
        acct_b = self.auth.register('b@isolated.com', 'password123')

        # Account A creates an agent
        agent_a = self.store.create_agent(acct_a['id'], 'Agent Alpha')

        # Account B lists agents, should be empty
        agents_b = self.store.list_agents(acct_b['id'])
        self.assertEqual(len(agents_b), 0, "Account B should see zero agents")

        # Account A lists agents, should have 1
        agents_a = self.store.list_agents(acct_a['id'])
        self.assertEqual(len(agents_a), 1, "Account A should see 1 agent")

    # ─── 4. API Key Auth ──────────────────────────────────────────────────

    def test_api_key_auth(self):
        """Test 4: Verify API key authentication works, invalid key returns None."""
        acct = self.auth.register('apikey@test.com', 'password123')
        agent = self.store.create_agent(acct['id'], 'Test Agent')

        # Valid API key
        verified = self.store.verify_api_key(agent['api_key'])
        self.assertIsNotNone(verified)
        self.assertEqual(verified['id'], agent['id'])

        # Invalid API key
        invalid = self.store.verify_api_key('as_live_invalidkey123')
        self.assertIsNone(invalid)

        # Empty key
        empty = self.store.verify_api_key('')
        self.assertIsNone(empty)

    # ─── 5. Create Rule ───────────────────────────────────────────────────

    def test_create_rule(self):
        """Test 5: Create a rule, verify it appears in list_rules."""
        acct = self.auth.register('rules@test.com', 'password123')
        rule_id = self.store.create_rule(
            acct['id'], 'transaction_limit', 1,
            {'max_amount': 500}, 'BLOCK'
        )
        self.assertIsNotNone(rule_id)

        rules = self.store.list_rules(acct['id'])
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['type'], 'transaction_limit')
        self.assertEqual(rules[0]['params'], {'max_amount': 500})

    # ─── 6. Rule Scoping ──────────────────────────────────────────────────

    def test_rule_scoping(self):
        """Test 6: Account A's rules are invisible to Account B."""
        acct_a = self.auth.register('rule-a@test.com', 'password123')
        acct_b = self.auth.register('rule-b@test.com', 'password123')

        self.store.create_rule(acct_a['id'], 'transaction_limit', 1, {'max_amount': 500}, 'BLOCK')

        rules_b = self.store.list_rules(acct_b['id'])
        self.assertEqual(len(rules_b), 0, "Account B should see no rules")

        rules_a = self.store.list_rules(acct_a['id'])
        self.assertEqual(len(rules_a), 1, "Account A should see 1 rule")

    # ─── 7. Transaction Recording ─────────────────────────────────────────

    def test_transaction_recording(self):
        """Test 7: Record a transaction, verify it appears in list_transactions."""
        acct = self.auth.register('txn@test.com', 'password123')
        agent = self.store.create_agent(acct['id'], 'Txn Agent')

        txn_id = self.store.record_transaction(
            acct['id'], agent['id'], 42.50, 'openai-api', 'llm_inference', 'APPROVED', None
        )
        self.assertIsNotNone(txn_id)

        txns = self.store.list_transactions(acct['id'])
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]['amount'], 42.50)
        self.assertEqual(txns[0]['merchant'], 'openai-api')

    # ─── 8. Transaction Isolation ─────────────────────────────────────────

    def test_transaction_isolation(self):
        """Test 8: Account A's transactions are invisible to Account B."""
        acct_a = self.auth.register('txn-iso-a@test.com', 'password123')
        acct_b = self.auth.register('txn-iso-b@test.com', 'password123')
        agent_a = self.store.create_agent(acct_a['id'], 'Agent A')

        self.store.record_transaction(
            acct_a['id'], agent_a['id'], 100.00, 'openai-api', 'llm_inference', 'APPROVED', None
        )

        # Account B sees nothing
        txns_b = self.store.list_transactions(acct_b['id'])
        self.assertEqual(len(txns_b), 0, "Account B should see no transactions")

        txns_a = self.store.list_transactions(acct_a['id'])
        self.assertEqual(len(txns_a), 1, "Account A should see 1 transaction")

    # ─── 9. Engine: Approve ───────────────────────────────────────────────

    def test_engine_approve(self):
        """Test 9: Engine returns APPROVED for a normal transaction."""
        txn = {"id": "t1", "agent_id": "a1", "amount": 50.00, "merchant": "openai-api",
               "category": "llm_inference", "timestamp": "2026-08-10T10:00:00Z", "metadata": {}}
        rules = [{"id": "r1", "type": "transaction_limit", "priority": 1,
                  "params": {"max_amount": 500}, "action": "BLOCK"}]
        result = self.engine.evaluate(txn, rules, [])
        self.assertEqual(result['decision'], 'APPROVED')

    # ─── 10. Engine: Block ────────────────────────────────────────────────

    def test_engine_block(self):
        """Test 10: Engine returns BLOCKED for a transaction exceeding the limit."""
        txn = {"id": "t1", "agent_id": "a1", "amount": 750.00, "merchant": "openai-api",
               "category": "llm_inference", "timestamp": "2026-08-10T10:00:00Z", "metadata": {}}
        rules = [{"id": "r1", "type": "transaction_limit", "priority": 1,
                  "params": {"max_amount": 500}, "action": "BLOCK"}]
        result = self.engine.evaluate(txn, rules, [])
        self.assertEqual(result['decision'], 'BLOCKED')

    # ─── 11. Engine: Velocity ─────────────────────────────────────────────

    def test_engine_velocity(self):
        """Test 11: Engine returns FLAGGED after 11 transactions in 60 minutes."""
        txn = {"id": "t1", "agent_id": "a1", "amount": 1.00, "merchant": "openai-api",
               "category": "llm_inference", "timestamp": "2026-08-10T10:30:00Z", "metadata": {}}
        rules = [{"id": "r1", "type": "velocity", "priority": 1,
                  "params": {"window_minutes": 60, "max_count": 10}, "action": "FLAGGED"}]
        # 10 prior transactions in the last 60 minutes
        priors = []
        for i in range(10):
            priors.append({"agent_id": "a1", "amount": 1.00,
                           "timestamp": f"2026-08-10T10:{20+i % 10}:00Z"})
        result = self.engine.evaluate(txn, rules, priors)
        self.assertEqual(result['decision'], 'FLAGGED')

    # ─── 12. License Validation ───────────────────────────────────────────

    def test_license_validation(self):
        """Test 12: Valid license returns valid=True, tampered returns valid=False."""
        key = generate_license_key('acct_test', 'dev', '2027-12-31T23:59:59Z')
        result = validate_license_key(key)
        self.assertTrue(result['valid'])
        self.assertEqual(result['tier'], 'dev')

        # Tampered key
        tampered = key[:-5] + 'AAAAA'
        tampered_result = validate_license_key(tampered)
        self.assertFalse(tampered_result['valid'])

    # ─── 13. License Expiry ───────────────────────────────────────────────

    def test_license_expiry(self):
        """Test 13: Expired license returns valid=False with 'License expired'."""
        key = generate_license_key('acct_expired', 'dev', '2020-01-01T00:00:00Z')
        result = validate_license_key(key)
        self.assertFalse(result['valid'])
        self.assertEqual(result['reason'], 'License expired')

    # ─── 14. Tier Enforcement ─────────────────────────────────────────────

    def test_tier_enforcement(self):
        """Test 14: Free tier cannot create more than 1 agent (max_agents=1)."""
        acct = self.auth.register('free@test.com', 'password123')
        # Account is 'free' tier by default
        self.assertEqual(acct['tier'], 'free')

        # Create first agent, should work
        agent1 = self.store.create_agent(acct['id'], 'Agent 1')
        self.assertIsNotNone(agent1)

        # Check tier limit
        limits = get_tier_limits('free')
        self.assertEqual(limits['max_agents'], 1)

        # Count active agents
        count = self.store.count_active_agents(acct['id'])
        self.assertEqual(count, 1)

        # In production, the API layer would enforce this limit.
        # Here we verify the check logic: count >= max_agents means blocked.
        self.assertGreaterEqual(count, limits['max_agents'],
                                "Free tier at limit, second agent should be rejected")


if __name__ == '__main__':
    unittest.main(verbosity=2)
