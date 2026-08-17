"""
AgentShield Eval Gym, 74 Scenarios
=====================================
74 labeled test cases spanning 12 categories, testing the
SpendControlEngine against real-world agent spending patterns plus the
SHACKLE SP/1.0 conformance envelope (HITL review, replay, circuit).

Categories (74 total):
  - cascade_cost (5)
  - category_block (7)
  - circuit_breaker (2)
  - clean_approval (10)
  - daily_total_block (9)
  - edge_cases (8)
  - hitl_review (3)
  - merchant_allowlist_block (7)
  - replay_nonce (2)
  - session_budget (4)
  - transaction_limit_block (10)
  - velocity_flag (7)
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
     "prior_transactions": [_prior("agent_a", 500, "2026-08-10T08:00:00Z"),
                            _prior("agent_a", 300, "2026-08-10T09:00:00Z")],
     "expected": "APPROVED",
     "description": "Daily total 1050 < 2000"},

    # ═══ TRANSACTION LIMIT BLOCK (8) ═══
    {"id": 11, "category": "transaction_limit_block",
     "transaction": _txn("t011", amount=750.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "$750 exceeds $500 limit"},

    {"id": 12, "category": "transaction_limit_block",
     "transaction": _txn("t012", amount=500.01),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Limit + $0.01 triggers block"},

    {"id": 13, "category": "transaction_limit_block",
     "transaction": _txn("t013", amount=10000.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Extreme amount blocked"},

    {"id": 14, "category": "transaction_limit_block",
     "transaction": _txn("t014", amount=600.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"},
               {"id": "r2", "type": "merchant_allowlist", "priority": 2, "params": {"allowed": ["openai-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Over limit, transaction_limit fires first (priority 1)"},

    {"id": 15, "category": "transaction_limit_block",
     "transaction": _txn("t015", amount=501.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "$501 over $500 limit"},

    {"id": 16, "category": "transaction_limit_block",
     "transaction": _txn("t016", amount=1500.00, merchant="anthropic-api"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api", "anthropic-api"]}, "action": "BLOCK"},
               {"id": "r2", "type": "transaction_limit", "priority": 2, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Merchant passes allowlist but amount triggers limit at priority 2"},

    {"id": 17, "category": "transaction_limit_block",
     "transaction": _txn("t017", amount=999.99),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 999.98}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "$999.99 over $999.98 limit"},

    {"id": 18, "category": "transaction_limit_block",
     "transaction": _txn("t018", amount=1000000.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Million-dollar runaway blocked"},

    # ═══ DAILY TOTAL BLOCK (7) ═══
    {"id": 19, "category": "daily_total_block",
     "transaction": _txn("t019", amount=100.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 2000}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 2000, "2026-08-10T01:00:00Z")],
     "expected": "BLOCKED",
     "description": "Daily total 2100 > 2000"},

    {"id": 20, "category": "daily_total_block",
     "transaction": _txn("t020", amount=1.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 100}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 100, "2026-08-10T01:00:00Z")],
     "expected": "BLOCKED",
     "description": "Already at cap, any amount overflows"},

    {"id": 21, "category": "daily_total_block",
     "transaction": _txn("t021", amount=500.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 2000}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 1000, "2026-08-10T06:00:00Z"),
                            _prior("agent_a", 600, "2026-08-10T07:00:00Z")],
     "expected": "BLOCKED",
     "description": "Daily total 2100 > 2000"},

    {"id": 22, "category": "daily_total_block",
     "transaction": _txn("t022", amount=100.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 100}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 1, "2026-08-10T01:00:00Z")],
     "expected": "BLOCKED",
     "description": "Daily total 101 > 100"},

    {"id": 23, "category": "daily_total_block",
     "transaction": _txn("t023", amount=250.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 500}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 300, "2026-08-10T01:00:00Z")],
     "expected": "BLOCKED",
     "description": "Daily total 550 > 500"},

    {"id": 24, "category": "daily_total_block",
     "transaction": _txn("t024", amount=500.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 500}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 1, "2026-08-10T01:00:00Z")],
     "expected": "BLOCKED",
     "description": "501 > 500 cap"},

    {"id": 25, "category": "daily_total_block",
     "transaction": _txn("t025", amount=200.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 2000}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 1850, "2026-08-10T01:00:00Z")],
     "expected": "BLOCKED",
     "description": "Daily total 2050 > 2000"},

    # ═══ VELOCITY FLAG (6) ═══
    {"id": 26, "category": "velocity_flag",
     "transaction": _txn("t026", amount=10.00, timestamp="2026-08-10T10:30:00Z"),
     "rules": [{"id": "r1", "type": "velocity", "priority": 1, "params": {"window_minutes": 60, "max_count": 5}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 10, f"2026-08-10T10:2{i}:00Z") for i in range(5)],
     "expected": "FLAGGED",
     "description": "6 transactions in 60min window (limit 5)"},

    {"id": 27, "category": "velocity_flag",
     "transaction": _txn("t027", amount=5.00, timestamp="2026-08-10T10:30:00Z"),
     "rules": [{"id": "r1", "type": "velocity", "priority": 1, "params": {"window_minutes": 60, "max_count": 10}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 5, f"2026-08-10T10:2{i}:00Z") for i in range(10)],
     "expected": "FLAGGED",
     "description": "11 transactions in window (limit 10)"},

    {"id": 28, "category": "velocity_flag",
     "transaction": _txn("t028", amount=1.00, timestamp="2026-08-10T10:30:00Z"),
     "rules": [{"id": "r1", "type": "velocity", "priority": 1, "params": {"window_minutes": 60, "max_count": 3}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 1, "2026-08-10T10:29:00Z"),
                            _prior("agent_a", 1, "2026-08-10T10:28:00Z"),
                            _prior("agent_a", 1, "2026-08-10T10:27:00Z")],
     "expected": "FLAGGED",
     "description": "4 transactions in 60min window (limit 3)"},

    {"id": 29, "category": "velocity_flag",
     "transaction": _txn("t029", amount=2.00, timestamp="2026-08-10T10:30:00Z"),
     "rules": [{"id": "r1", "type": "velocity", "priority": 1, "params": {"window_minutes": 60, "max_count": 2}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 2, "2026-08-10T10:00:00Z"),
                            _prior("agent_a", 2, "2026-08-10T10:15:00Z")],
     "expected": "FLAGGED",
     "description": "3 transactions in 60min window (limit 2)"},

    {"id": 30, "category": "velocity_flag",
     "transaction": _txn("t030", amount=5.00, timestamp="2026-08-10T12:00:00Z"),
     "rules": [{"id": "r1", "type": "velocity", "priority": 1, "params": {"window_minutes": 60, "max_count": 5}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 5, f"2026-08-10T11:5{i}:00Z") for i in range(5)],
     "expected": "FLAGGED",
     "description": "6 transactions in 60min window (limit 5)"},

    {"id": 31, "category": "velocity_flag",
     "transaction": _txn("t031", amount=3.00, timestamp="2026-08-10T12:00:00Z"),
     "rules": [{"id": "r1", "type": "velocity", "priority": 1, "params": {"window_minutes": 30, "max_count": 3}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 3, "2026-08-10T11:40:00Z"),
                            _prior("agent_a", 3, "2026-08-10T11:45:00Z"),
                            _prior("agent_a", 3, "2026-08-10T11:50:00Z")],
     "expected": "FLAGGED",
     "description": "4 transactions in 30min window (limit 3)"},

    # ═══ MERCHANT ALLOWLIST BLOCK (7) ═══
    {"id": 32, "category": "merchant_allowlist_block",
     "transaction": _txn("t032", amount=10.00, merchant="unknown-api"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api", "anthropic-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Unknown merchant blocked"},

    {"id": 33, "category": "merchant_allowlist_block",
     "transaction": _txn("t033", amount=50.00, merchant="unauthorized-vendor"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Unauthorized vendor blocked"},

    {"id": 34, "category": "merchant_allowlist_block",
     "transaction": _txn("t034", amount=100.00, merchant="suspicious-api"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api", "anthropic-api", "stripe-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Suspicious merchant blocked"},

    {"id": 35, "category": "merchant_allowlist_block",
     "transaction": _txn("t035", amount=25.00, merchant="random-llm-proxy"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api", "anthropic-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Random LLM proxy blocked"},

    {"id": 36, "category": "merchant_allowlist_block",
     "transaction": _txn("t036", amount=15.00, merchant="dark-market"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Dark market merchant blocked"},

    {"id": 37, "category": "merchant_allowlist_block",
     "transaction": _txn("t037", amount=500.00, merchant="unknown-api"),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 1000}, "action": "BLOCK"},
               {"id": "r2", "type": "merchant_allowlist", "priority": 2, "params": {"allowed": ["openai-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Under tx limit, but merchant not allowed"},

    {"id": 38, "category": "merchant_allowlist_block",
     "transaction": _txn("t038", amount=20.00, merchant="new-vendor"),
     "rules": [{"id": "r1", "type": "merchant_allowlist", "priority": 1, "params": {"allowed": ["openai-api"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "New merchant not in allowlist"},

    # ═══ CATEGORY BLOCK (7) ═══
    {"id": 39, "category": "category_block",
     "transaction": _txn("t039", amount=100.00, category="crypto_exchange"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["crypto_exchange", "adult_content"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Crypto exchange blocked"},

    {"id": 40, "category": "category_block",
     "transaction": _txn("t040", amount=50.00, category="adult_content"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["crypto_exchange", "adult_content"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Adult content blocked"},

    {"id": 41, "category": "category_block",
     "transaction": _txn("t041", amount=200.00, category="gambling"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["gambling"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Gambling category blocked"},

    {"id": 42, "category": "category_block",
     "transaction": _txn("t042", amount=75.00, category="luxury_purchase"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["luxury_purchase"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Luxury purchase blocked"},

    {"id": 43, "category": "category_block",
     "transaction": _txn("t043", amount=10.00, category="unauthorized_purchase"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["unauthorized_purchase"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Unauthorized purchase blocked"},

    {"id": 44, "category": "category_block",
     "transaction": _txn("t044", amount=300.00, category="crypto_exchange"),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"},
               {"id": "r2", "type": "category_block", "priority": 2, "params": {"blocked": ["crypto_exchange"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Under tx limit, crypto category blocked at priority 2"},

    {"id": 45, "category": "category_block",
     "transaction": _txn("t045", amount=10.00, category="unauthorized_service"),
     "rules": [{"id": "r1", "type": "category_block", "priority": 1, "params": {"blocked": ["unauthorized_service"]}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Unauthorized service blocked"},


    {"id": 51, "category": "daily_total_block",
     "transaction": _txn("t051", amount=50.00, agent_id="agent_b", timestamp="2026-08-10T10:00:00Z"),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 300}, "action": "BLOCK"}],
     "prior_transactions": [
         {"agent_id": "agent_b", "amount": 1000.0, "timestamp": "2026-08-10T09:00:00Z", "decision": "BLOCKED"},
         {"agent_id": "agent_b", "amount": 200.0, "timestamp": "2026-08-10T09:30:00Z", "decision": "APPROVED"}
     ],
     "expected": "APPROVED",
     "description": "BLOCKED prior transaction is excluded from daily total cumulative sum"},

    {"id": 52, "category": "daily_total_block",
     "transaction": _txn("t052", amount=100.00, agent_id="agent_c", timestamp="2026-08-10T23:30:00-05:00"),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1, "params": {"max_daily": 500}, "action": "BLOCK"}],
     "prior_transactions": [
         {"agent_id": "agent_c", "amount": 450.0, "timestamp": "2026-08-11T01:00:00Z", "decision": "APPROVED"}
     ],
     "expected": "BLOCKED",
     "description": "ISO timestamp timezone offsets correctly parsed into UTC date for daily calculation"},

    # ═══ EDGE CASES (5) ═══
    {"id": 46, "category": "edge_cases",
     "transaction": _txn("t046", amount=500.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Amount EXACTLY at limit should APPROVE (not strictly greater)"},

    {"id": 47, "category": "edge_cases",
     "transaction": {"id": "t047", "agent_id": "agent_a", "merchant": "openai-api",
                     "category": "llm_inference", "timestamp": "2026-08-10T10:00:00Z"},
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Missing amount field yields BLOCKED (fail-closed)"},

    {"id": 48, "category": "edge_cases",
     "transaction": _txn("t048", amount=10.00),
     "rules": [],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Empty rules list yields APPROVED"},

    {"id": 49, "category": "edge_cases",
     "transaction": _txn("t049", amount=10.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 5, "params": {"max_amount": 100}, "action": "BLOCK"},
               {"id": "r2", "type": "transaction_limit", "priority": 5, "params": {"max_amount": 5000}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "APPROVED",
     "description": "Two rules at same priority, neither triggers"},

    {"id": 50, "category": "edge_cases",
     "transaction": _txn("t050", amount=10.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 5}, "action": "BLOCK"},
               {"id": "r2", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 5000}, "action": "BLOCK"}],
     "prior_transactions": [], "expected": "BLOCKED",
     "description": "Same priority, first rule (max_amount=5) blocks $10"},

    # ─── Session Budget (inspired by HeartFlow / @yun520-1) ───
    {"id": 51, "category": "session_budget",
     "transaction": {**_txn("t051", amount=150.00), "session_id": "sess_1"},
     "rules": [{"id": "sb1", "type": "session_budget", "priority": 1,
                "params": {"max_session": 500}, "action": "BLOCK"}],
     "prior_transactions": [
         {**_txn("t050a", amount=400.00), "session_id": "sess_1"},
     ],
     "expected": "BLOCKED",
     "description": "Session total $550 exceeds $500 session budget"},

    {"id": 52, "category": "session_budget",
     "transaction": {**_txn("t052", amount=100.00), "session_id": "sess_2"},
     "rules": [{"id": "sb2", "type": "session_budget", "priority": 1,
                "params": {"max_session": 500}, "action": "BLOCK"}],
     "prior_transactions": [
         {**_txn("t052a", amount=200.00), "session_id": "sess_2"},
     ],
     "expected": "APPROVED",
     "description": "Session total $300 under $500 session budget, approved"},

    {"id": 53, "category": "session_budget",
     "transaction": {**_txn("t053", amount=50.00), "session_id": "sess_3"},
     "rules": [{"id": "sb3", "type": "session_budget", "priority": 1,
                "params": {"max_session": 500}, "action": "BLOCK"}],
     "prior_transactions": [
         {**_txn("t053a", amount=200.00), "session_id": "sess_4"},  # Different session
     ],
     "expected": "APPROVED",
     "description": "Prior transaction in different session, not counted"},

    # ─── Cascade Cost (inspired by HeartFlow / @yun520-1) ───
    {"id": 54, "category": "cascade_cost",
     "transaction": {**_txn("t054", amount=50.00), "fail_probability": 0.3, "reversal_cost": 200},
     "rules": [{"id": "cc1", "type": "cascade_cost", "priority": 1,
                "params": {"max_cascade_cost": 100}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Cascade cost $110 ($50 + 30% × $200) exceeds $100 limit"},

    {"id": 55, "category": "cascade_cost",
     "transaction": {**_txn("t055", amount=10.00), "fail_probability": 0.1, "reversal_cost": 50},
     "rules": [{"id": "cc2", "type": "cascade_cost", "priority": 1,
                "params": {"max_cascade_cost": 100}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "APPROVED",
     "description": "Cascade cost $15 ($10 + 10% × $50) under $100 limit"},

    {"id": 56, "category": "cascade_cost",
     "transaction": {**_txn("t056", amount=10.00), "estimated_cascade_cost": 150},
     "rules": [{"id": "cc3", "type": "cascade_cost", "priority": 1,
                "params": {"max_cascade_cost": 100}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Pre-computed cascade cost $150 exceeds $100 limit"},

    # ─── Non-Negativity Validation (reported by @sharkwon) ───
    {"id": 57, "category": "daily_total_block",
     "transaction": _txn("t057", amount=500.00),
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1,
                "params": {"max_daily": 100}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", -1000.00, "2026-08-10T09:00:00Z")],
     "expected": "BLOCKED",
     "description": "Negative prior amount ($-1000) should not reduce daily total, $500 > $100 cap → BLOCKED"},

    {"id": 58, "category": "session_budget",
     "transaction": {**_txn("t058", amount=190.00), "session_id": "s1"},
     "rules": [{"id": "r1", "type": "session_budget", "priority": 1,
                "params": {"max_session": 100}, "action": "BLOCK"}],
     "prior_transactions": [
         {**_prior("a", -95.00, "2026-08-10T09:00:00Z"), "session_id": "s1"}
     ],
     "expected": "BLOCKED",
     "description": "Negative prior session amount ($-95) should not reduce session total, $190 > $100 → BLOCKED"},

    {"id": 59, "category": "transaction_limit_block",
     "transaction": _txn("t059", amount=-1000000.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1,
                "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Negative amount should be rejected by transaction_limit"},

    {"id": 60, "category": "transaction_limit_block",
     "transaction": _txn("t060", amount=0.00),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1,
                "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Zero amount transaction should be rejected"},

    {"id": 61, "category": "cascade_cost",
     "transaction": {**_txn("t061", amount=50.00), "estimated_cascade_cost": -10},
     "rules": [{"id": "cc4", "type": "cascade_cost", "priority": 1,
                "params": {"max_cascade_cost": 100}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Negative pre-computed cascade cost should be rejected"},

    {"id": 62, "category": "cascade_cost",
     "transaction": {**_txn("t062", amount=50.00), "reversal_cost": -100, "fail_probability": 0.5},
     "rules": [{"id": "cc5", "type": "cascade_cost", "priority": 1,
                "params": {"max_cascade_cost": 100}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Negative reversal cost should be rejected in cascade calculation"},

    # === SP/1.0 envelope: HITL review, replay, circuit (Fame510/SHACKLE conformance) ===
    {"id": 63, "category": "hitl_review",
     "transaction": _txn("t063", amount=10.00),
     "rules": [{"id": "hr1", "type": "hitl_threshold", "priority": 1,
                "params": {"mode": "always"}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "REVIEW",
     "description": "hitl_mode=always escalates every call to REVIEW"},

    {"id": 64, "category": "hitl_review",
     "transaction": {**_txn("t064", amount=50.00), "session_id": "s_hitl_1"},
     "rules": [{"id": "hr2", "type": "hitl_threshold", "priority": 1,
                "params": {"max_budget": 100, "threshold": 0.15}, "action": "BLOCK"}],
     "prior_transactions": [{**_txn("t064a", amount=40.00), "session_id": "s_hitl_1"}],
     "expected": "REVIEW",
     "description": "Remaining budget ($10 of $100) under 15% threshold escalates to REVIEW"},

    {"id": 65, "category": "hitl_review",
     "transaction": {**_txn("t065", amount=5.00), "session_id": "s_hitl_2"},
     "rules": [{"id": "hr3", "type": "hitl_threshold", "priority": 1,
                "params": {"max_budget": 100, "threshold": 0.15}, "action": "BLOCK"}],
     "prior_transactions": [{**_txn("t065a", amount=10.00), "session_id": "s_hitl_2"}],
     "expected": "APPROVED",
     "description": "Remaining budget ($85 of $100) above 15% threshold stays APPROVED"},

    {"id": 66, "category": "replay_nonce",
     "transaction": {**_txn("t066"), "nonce": 7},
     "rules": [{"id": "rp1", "type": "replay", "priority": 1, "params": {}, "action": "BLOCK"}],
     "prior_transactions": [{**_txn("t066a"), "nonce": 7}],
     "expected": "BLOCKED",
     "description": "Replayed nonce (7 already seen) is blocked"},

    {"id": 67, "category": "replay_nonce",
     "transaction": {**_txn("t067"), "nonce": 9},
     "rules": [{"id": "rp2", "type": "replay", "priority": 1, "params": {}, "action": "BLOCK"}],
     "prior_transactions": [{**_txn("t067a"), "nonce": 8}],
     "expected": "APPROVED",
     "description": "Fresh nonce (9, never seen) is not replayed"},

    {"id": 68, "category": "circuit_breaker",
     "transaction": {**_txn("t068"), "circuit_tripped": True},
     "rules": [{"id": "cb1", "type": "circuit", "priority": 1, "params": {}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Tripped circuit blocks all calls (fail-closed latch)"},

    {"id": 69, "category": "circuit_breaker",
     "transaction": _txn("t069"),
     "rules": [{"id": "cb2", "type": "circuit", "priority": 1, "params": {}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "APPROVED",
     "description": "Circuit closed (no flag) does not block"},

    {"id": 70, "category": "edge_cases",
     "transaction": {"id": "t070", "agent_id": "agent_a", "amount": "not_a_number",
                     "merchant": "openai-api", "category": "llm_inference",
                     "timestamp": "2026-08-10T10:00:00Z"},
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Unparseable amount is BLOCKED (fail-closed), not FLAGGED"},

    # === Decimal Overflow DoS (reported by @LinWang312, bug #3) ===
    {"id": 71, "category": "edge_cases",
     "transaction": _txn("t071", amount=1e50),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Absurd amount (1e50) should BLOCK not crash _fmt quantize (DoS fix)"},

    {"id": 72, "category": "edge_cases",
     "transaction": _txn("t072", amount=1e27),
     "rules": [{"id": "r1", "type": "transaction_limit", "priority": 1, "params": {"max_amount": 500}, "action": "BLOCK"}],
     "prior_transactions": [],
     "expected": "BLOCKED",
     "description": "Amount at 28-digit precision boundary (1e27) should BLOCK not crash"},

    # === Cross-Agent False Positive: falsy None (reported by @LinWang312, bug #5) ===
    {"id": 73, "category": "velocity_flag",
     "transaction": {"id": "t073", "amount": 10.00, "merchant": "openai-api",
                     "category": "llm_inference", "timestamp": "2026-08-10T10:00:00Z"},
     "rules": [{"id": "r1", "type": "velocity", "priority": 1,
                "params": {"window_minutes": 60, "max_count": 5}, "action": "FLAGGED"}],
     "prior_transactions": [_prior("agent_a", 5, f"2026-08-10T09:3{i}:00Z") for i in range(7)],
     "expected": "APPROVED",
     "description": "Txn without agent_id must not aggregate with agent_a priors (cross-agent FP fix)"},

    {"id": 74, "category": "daily_total_block",
     "transaction": {"id": "t074", "amount": 10.00, "merchant": "openai-api",
                     "category": "llm_inference", "timestamp": "2026-08-10T10:00:00Z"},
     "rules": [{"id": "r1", "type": "daily_total", "priority": 1,
                "params": {"max_daily": 100}, "action": "BLOCK"}],
     "prior_transactions": [_prior("agent_a", 200, "2026-08-10T09:00:00Z")],
     "expected": "APPROVED",
     "description": "Txn without agent_id must not aggregate agent_a daily total (cross-agent fix)"},
]


def run_eval() -> dict:
    """Run all scenarios and return results dict."""
    engine = SpendControlEngine()
    results = {"total": 0, "passed": 0, "failed": 0, "by_category": {}, "failures": []}

    for scenario in SCENARIOS:
        result = engine.evaluate(
            scenario["transaction"],
            scenario["rules"],
            scenario["prior_transactions"]
        )
        cat = scenario["category"]
        results["by_category"].setdefault(cat, {"total": 0, "passed": 0})
        results["by_category"][cat]["total"] += 1
        results["total"] += 1

        if result["decision"] == scenario["expected"]:
            results["passed"] += 1
            results["by_category"][cat]["passed"] += 1
        else:
            results["failed"] += 1
            results["failures"].append({
                "scenario": scenario["id"],
                "expected": scenario["expected"],
                "got": result["decision"],
                "reason": result.get("reason"),
                "description": scenario["description"]
            })

    return results


def generate_report(results: dict) -> str:
    """Generate a markdown report from eval results."""
    total = results['total']
    passed = results['passed']
    pct = passed / total * 100 if total else 0

    md = f"# AgentShield Eval Gym Report\n\n"
    md += f"**Overall:** {passed}/{total} ({pct:.1f}%)\n\n"
    md += "## By Category\n\n"
    md += "| Category | Passed | Total | Rate |\n"
    md += "|----------|--------|-------|------|\n"
    for cat, data in sorted(results["by_category"].items()):
        rate = data['passed'] / data['total'] * 100 if data['total'] else 0
        md += f"| {cat} | {data['passed']} | {data['total']} | {rate:.0f}% |\n"

    if results['failures']:
        md += "\n## Failures\n\n"
        for f in results['failures']:
            md += f"- **Scenario {f['scenario']}**: Expected `{f['expected']}`, got `{f['got']}`, {f['description']}\n"

    return md


if __name__ == '__main__':
    results = run_eval()
    print(f"{results['passed']}/{results['total']} passed")
    if results['failed']:
        print("FAILURES:")
        for f in results['failures']:
            print(f"  Scenario {f['scenario']}: expected {f['expected']} got {f['got']}")
    else:
        print("ALL PASSED")
    report = generate_report(results)
    report_path = os.path.join('/tmp', 'agentshield-eval-report.md')
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report: {report_path}")
