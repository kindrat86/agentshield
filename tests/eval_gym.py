"""
AgentShield Eval Gym — 51 Scenarios
=====================================
51 labeled test cases spanning 7 categories, testing the SpendControlEngine
against real-world agent spending patterns.

Categories (51 total):
  - clean_approval (10):        Normal transactions that should pass
  - transaction_limit_block (8): Single transactions exceeding max amount
  - daily_total_block (7):       Cumulative daily spend exceeding cap
  - velocity_flag (7):           Rapid-fire transactions triggering velocity cap
  - merchant_allowlist_block (7): Transactions to unlisted merchants
  - category_block (7):          Transactions in blocked categories
  - edge_cases (5):              Boundary values, malformed inputs, empty rules
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import SpendControlEngine

def _txn(txn_id, amount=10.00, merchant="openai-api", category="llm_inference",
         agent_id="agent_a", timestamp="2026-08-10T10:00:00Z"):
    return {
        "id": txn_id, "agent_id": agent_id, "amount": amount,
        "merchant": merchant, "category": category,
        "timestamp": timestamp, "metadata": {}
    }

def _prior(agent_id, amount, timestamp):
    return {"agent_id": agent_id, "amount": amount, "timestamp": timestamp}

SCENARIOS = [

    # ═══ CLEAN APPROVAL (10) ═══
    {"id": 1, "category": "clean_approval",
     "transaction": _txn("t001", amount=10.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Small transaction under all limits"},

    {"id": 2, "category": "clean_approval",
     "transaction": _txn("t002", amount=50.00, merchant="anthropic-api"),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"},
               {"id": "r2", "type": "merchant_allowlist", "priority": 2, "params": {"allowed": ["openai-api", "anthropic-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Normal Anthropic API call"},

    {"id": 3, "category": "clean_approval",
     "transaction": _txn("t003", amount=5.00, category="embedding"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["crypto_exchange"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Embedding call in non-blocked category"},

    {"id": 4, "category": "clean_approval",
     "transaction": _txn("t004", amount=100.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 2000}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 200, "2026-08-10T09:00:00Z")],
     "expected": "APPROVED",
     "description": "Within daily total (300 < 2000)"},

    {"id": 5, "category": "clean_approval",
     "transaction": _txn("t005", amount=25.00, timestamp="2026-08-10T10:00:00Z"),
     "rules": [{"id": "r1", "type": "velocity", "priority": 1, "params": {"window_minutes": 60, "max_count": 10}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 10, f"2026-08-10T09:5{i}:00Z") for i in range(3)],
     "expected": "APPROVED",
     "description": "4 total in window, under limit of 10"},

    {"id": 6, "category": "clean_approval",
     "transaction": _txn("t006", amount=0.01),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Minimum viable transaction"},

    {"id": 7, "category": "clean_approval",
     "transaction": _txn("t007", amount=300.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "High but under single-transaction limit"},

    {"id": 8, "category": "clean_approval",
     "transaction": _txn("t008", amount=15.00, merchant="stripe-api"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api", "anthropic-api", "stripe-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Allowed merchant"},

    {"id": 9, "category": "clean_approval",
     "transaction": _txn("t009", amount=42.50, category="data_storage"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["crypto_exchange", "adult_content"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Standard category not in blocklist"},

    {"id": 10, "category": "clean_approval",
     "transaction": _txn("t010", amount=250.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 2000}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 500, "2026-08-10T08:00:0