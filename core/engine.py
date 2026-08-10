"""
AgentShield Spend Control Engine
================================
A deterministic, stateless spend-control rule evaluator for AI agent transactions.

The engine evaluates an incoming transaction against a prioritized list of rules
and returns a decision: APPROVED, BLOCKED, or FLAGGED. It is:
  - Stateless: no file I/O, no network calls, no global mutable state.
  - Deterministic: same inputs always produce the same output.
  - Composable: rules can be combined arbitrarily; first match (by priority) wins.
  - Monetary-safe: uses decimal.Decimal for all amount arithmetic (never float).

Rule Types (7):
  1. transaction_limit   — block if a single transaction exceeds max_amount
  2. daily_total         — block if cumulative daily spend exceeds max_daily
  3. velocity            — flag if transaction count in rolling window exceeds max_count
  4. merchant_allowlist  — block if merchant is NOT in the allowed list
  5. category_block      — block if category IS in the blocked list
"""

from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone


class SpendControlEngine:
    """
    Evaluates transactions against spend-control rules.

    All monetary arithmetic uses Decimal for exact precision. Timestamps are
    parsed with datetime.fromisoformat() with graceful fallback. The engine
    handles malformed input by returning FLAGGED.
    """

    def evaluate(self, transaction: dict, rules: list, prior_transactions: list) -> dict:
        """
        Evaluate a transaction against rules, considering prior transactions.

        Args:
            transaction: The transaction to evaluate. Must contain 'amount',
                         'merchant', and 'category'. Optionally 'agent_id',
                         'timestamp', 'id', 'metadata'.
            rules: List of rule dicts, each with 'id', 'type', 'priority',
                   'params', and 'action'.
            prior_transactions: List of prior transaction dicts for the same agent,
                                used by daily_total and velocity rules.

        Returns:
            A dict with 'decision', 'reason', 'rule_triggered', 'severity'.
        """
        # Validate transaction has required fields
        required_fields = ['amount', 'merchant', 'category']
        if not transaction or not all(k in transaction for k in required_fields):
            return {
                "decision": "FLAGGED",
                "reason": "Invalid transaction format: missing required fields",
                "rule_triggered": None,
                "severity": "medium"
            }

        # Validate amount is parseable as a number
        try:
            txn_amount = self._to_decimal(transaction['amount'])
        except (InvalidOperation, TypeError, ValueError):
            return {
                "decision": "FLAGGED",
                "reason": "Invalid transaction format: amount is not a valid number",
                "rule_triggered": None,
                "severity": "medium"
            }

        # Sort rules by priority (lowest number = highest priority).
        # When priorities are equal, preserve original list order (stable sort).
        sorted_rules = sorted(
            enumerate(rules),
            key=lambda pair: (pair[1].get('priority', 999), pair[0])
        )

        for _original_index, rule in sorted_rules:
            result = self._evaluate_rule(rule, transaction, txn_amount, prior_transactions)
            if result is not None:
                return result

        # No rule matched — approve
        return {
            "decision": "APPROVED",
            "reason": "All rules passed",
            "rule_triggered": None,
            "severity": "none"
        }

    def _evaluate_rule(self, rule: dict, transaction: dict, txn_amount: Decimal,
                       prior_transactions: list) -> dict | None:
        """Evaluate a single rule. Returns a result dict if triggered, None otherwise."""
        rule_type = rule.get('type')
        params = rule.get('params', {})
        action = rule.get('action', 'BLOCK')
        rule_id = rule.get('id', 'unknown')

        if rule_type == 'transaction_limit':
            return self._check_transaction_limit(rule_id, txn_amount, params, action)
        elif rule_type == 'daily_total':
            return self._check_daily_total(rule_id, transaction, txn_amount, prior_transactions, params, action)
        elif rule_type == 'velocity':
            return self._check_velocity(rule_id, transaction, prior_transactions, params, action)
        elif rule_type == 'merchant_allowlist':
            return self._check_merchant_allowlist(rule_id, transaction, params, action)
        elif rule_type == 'category_block':
            return self._check_category_block(rule_id, transaction, params, action)
        else:
            # Unknown rule type — skip silently
            return None

    def _check_transaction_limit(self, rule_id: str, txn_amount: Decimal, params: dict, action: str):
        max_amount = self._to_decimal_safe(params.get('max_amount'))
        if max_amount is None:
            return None
        if txn_amount > max_amount:
            return self._make_result(action, rule_id,
                f"Transaction amount ${self._fmt(txn_amount)} exceeds limit of ${self._fmt(max_amount)}")
        return None

    def _check_daily_total(self, rule_id: str, transaction: dict, txn_amount: Decimal,
                           prior_transactions: list, params: dict, action: str):
        max_daily = self._to_decimal_safe(params.get('max_daily'))
        if max_daily is None:
            return None

        txn_date = self._extract_date(transaction.get('timestamp'))
        agent_id = transaction.get('agent_id')

        daily_total = txn_amount  # Start with current transaction
        for prior in prior_transactions:
            if agent_id and prior.get('agent_id') != agent_id:
                continue
            prior_date = self._extract_date(prior.get('timestamp'))
            if txn_date and prior_date and prior_date == txn_date:
                prior_amount = self._to_decimal_safe(prior.get('amount'))
                if prior_amount is not None:
                    daily_total += prior_amount

        if daily_total > max_daily:
            return self._make_result(action, rule_id,
                f"Daily spend ${self._fmt(daily_total)} exceeds limit of ${self._fmt(max_daily)}")
        return None

    def _check_velocity(self, rule_id: str, transaction: dict, prior_transactions: list,
                        params: dict, action: str):
        window_minutes = params.get('window_minutes')
        max_count = params.get('max_count')
        if window_minutes is None or max_count is None:
            return None

        txn_ts = self._parse_ts(transaction.get('timestamp'))
        if txn_ts is None:
            return None

        window_start = txn_ts - timedelta(minutes=window_minutes)
        agent_id = transaction.get('agent_id')

        count_in_window = 0
        for prior in prior_transactions:
            if agent_id and prior.get('agent_id') != agent_id:
                continue
            prior_ts = self._parse_ts(prior.get('timestamp'))
            if prior_ts and window_start <= prior_ts <= txn_ts:
                count_in_window += 1

        # count + 1 (the current transaction) vs max_count
        if (count_in_window + 1) > max_count:
            return self._make_result(action, rule_id,
                f"Velocity exceeded: {count_in_window + 1} transactions in {window_minutes}min window "
                f"(limit: {max_count})")
        return None

    def _check_merchant_allowlist(self, rule_id: str, transaction: dict, params: dict, action: str):
        allowed = params.get('allowed', [])
        merchant = transaction.get('merchant')
        if merchant and merchant not in allowed:
            return self._make_result(action, rule_id,
                f"Merchant '{merchant}' is not in the allowlist")
        return None

    def _check_category_block(self, rule_id: str, transaction: dict, params: dict, action: str):
        blocked = params.get('blocked', [])
        category = transaction.get('category')
        if category and category in blocked:
            return self._make_result(action, rule_id,
                f"Category '{category}' is blocked")
        return None

    # ─── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _to_decimal(value) -> Decimal:
        """Convert a value to Decimal. Raises on failure."""
        if isinstance(value, Decimal):
            return value
        if isinstance(value, float):
            return Decimal(str(value))
        return Decimal(value)

    @staticmethod
    def _to_decimal_safe(value) -> Decimal | None:
        """Convert to Decimal, return None on failure."""
        try:
            return SpendControlEngine._to_decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None

    @staticmethod
    def _fmt(d: Decimal) -> str:
        """Format a Decimal as a 2-decimal-place string."""
        quantized = d.quantize(Decimal('0.01'))
        return f"{quantized}"

    @staticmethod
    def _make_result(action: str, rule_id: str, reason: str) -> dict:
        """Build the result dict from an action string."""
        severity_map = {
            'BLOCK': 'high',
            'BLOCKED': 'high',
            'FLAG': 'medium',
            'FLAGGED': 'medium',
        }
        decision = action.upper()
        if decision == 'BLOCK':
            decision = 'BLOCKED'
        elif decision == 'FLAG':
            decision = 'FLAGGED'
        return {
            "decision": decision,
            "reason": reason,
            "rule_triggered": rule_id,
            "severity": severity_map.get(decision, 'medium')
        }

    @staticmethod
    def _parse_ts(ts_str: str | None) -> datetime | None:
        """Parse an ISO timestamp string into a datetime object."""
        if not ts_str:
            return None
        try:
            ts = ts_str
            # Handle 'Z' suffix
            if ts.endswith('Z'):
                ts = ts[:-1] + '+00:00'
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_date(ts_str: str | None) -> str | None:
        """Extract the date portion (YYYY-MM-DD) from a timestamp string."""
        if not ts_str:
            return None
        try:
            return ts_str[:10]
        except (TypeError, IndexError):
            return None
