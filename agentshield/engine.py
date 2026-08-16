"""
AgentShield Spend Control Engine
================================
A deterministic, stateless spend-control rule evaluator for AI agent transactions.

The engine evaluates an incoming transaction against a prioritized list of rules
and returns a decision: APPROVED, BLOCKED, FLAGGED, or REVIEW. It is:
  - Stateless: no file I/O, no network calls, no global mutable state.
  - Deterministic: same inputs always produce the same output.
  - Composable: rules can be combined arbitrarily; first match (by priority) wins.
  - Monetary-safe: uses decimal.Decimal for all amount arithmetic (never float).

Rule Types (10):
  1. transaction_limit  , block if a single transaction exceeds max_amount
  2. daily_total        , block if cumulative daily spend exceeds max_daily
  3. velocity           , flag if transaction count in rolling window exceeds max_count
  4. merchant_allowlist , block if merchant is NOT in the allowed list
  5. category_block     , block if category IS in the blocked list
  6. session_budget     , block if cumulative session spend exceeds max_session (resets per session)
  7. cascade_cost       , block if estimated cascade cost (call + retry probability × reversal) exceeds threshold
  8. hitl_threshold     , escalate to REVIEW when spend crosses a human-review threshold (or always)
  9. replay             , block if the transaction nonce was already seen (replay protection)
 10. circuit            , block all calls while the circuit is tripped (fail-closed latch)
"""

from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone


class SpendControlEngine:
    """
    Evaluates transactions against spend-control rules.

    All monetary arithmetic uses Decimal for exact precision. Timestamps are
    parsed with datetime.fromisoformat() with graceful fallback. The engine
    handles malformed input by returning BLOCKED (fail-closed).
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
                "decision": "BLOCKED",
                "reason": "Invalid transaction format: missing required fields (fail-closed)",
                "rule_triggered": None,
                "severity": "high"
            }

        # Validate amount is parseable as a number
        try:
            txn_amount = self._to_decimal(transaction['amount'])
        except (InvalidOperation, TypeError, ValueError):
            return {
                "decision": "BLOCKED",
                "reason": "Invalid transaction format: amount is not a valid number (fail-closed)",
                "rule_triggered": None,
                "severity": "high"
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

        # No rule matched, approve
        return {
            "decision": "APPROVED",
            "reason": "All rules passed",
            "rule_triggered": None,
            "severity": "none"
        }

    def evaluate_with_trace(self, transaction: dict, rules: list, prior_transactions: list) -> dict:
        """
        Evaluate a transaction and additionally return a per-rule evaluation trace.

        Returns:
            {
              "decision": {decision, reason, rule_triggered, severity},
              "evaluation": [{"rule_id", "type", "priority", "outcome", "detail"}, ...]
            }

        `outcome` is one of:
          - "triggered"  , rule produced the decision
          - "passed"     , rule evaluated and did not fire
          - "skipped"    , rule could not be evaluated (missing/invalid params)
          - "not_reached", lower priority than the winning rule, never evaluated

        `detail` carries the actual-vs-threshold values for the triggered rule
        (rule-type specific) and is None otherwise.
        """
        decision = self.evaluate(transaction, rules, prior_transactions)
        evaluation = self._build_evaluation_trace(transaction, rules, prior_transactions)
        return {"decision": decision, "evaluation": evaluation}

    def _build_evaluation_trace(self, transaction: dict, rules: list, prior_transactions: list) -> list:
        """Build the per-rule evaluation trace (used by evaluate_with_trace)."""
        # If the transaction itself was invalid, no rule was meaningfully evaluated.
        if not transaction or not all(k in transaction for k in ('amount', 'merchant', 'category')):
            return []
        try:
            txn_amount = self._to_decimal(transaction['amount'])
        except (InvalidOperation, TypeError, ValueError):
            return []

        sorted_rules = sorted(
            enumerate(rules),
            key=lambda pair: (pair[1].get('priority', 999), pair[0])
        )

        triggered_seen = False
        trace = []
        for _original_index, rule in sorted_rules:
            entry = {
                "rule_id": rule.get('id', 'unknown'),
                "type": rule.get('type'),
                "priority": rule.get('priority', 999),
                "outcome": None,
                "detail": None,
            }

            if triggered_seen:
                entry["outcome"] = "not_reached"
            elif not self._rule_applicable(rule, transaction):
                entry["outcome"] = "skipped"
            else:
                result = self._evaluate_rule(rule, transaction, txn_amount, prior_transactions)
                if result is not None:
                    entry["outcome"] = "triggered"
                    entry["detail"] = self._trace_detail(rule, transaction, txn_amount, prior_transactions)
                    triggered_seen = True
                else:
                    entry["outcome"] = "passed"

            trace.append(entry)
        return trace

    def _rule_applicable(self, rule: dict, transaction: dict) -> bool:
        """Whether a rule has the params it needs to actually evaluate."""
        rule_type = rule.get('type')
        params = rule.get('params', {})
        if rule_type == 'transaction_limit':
            return self._to_decimal_safe(params.get('max_amount')) is not None
        if rule_type == 'daily_total':
            return self._to_decimal_safe(params.get('max_daily')) is not None
        if rule_type == 'velocity':
            if params.get('window_minutes') is None or params.get('max_count') is None:
                return False
            return self._parse_ts(transaction.get('timestamp')) is not None
        if rule_type == 'merchant_allowlist':
            return 'allowed' in params
        if rule_type == 'category_block':
            return 'blocked' in params
        if rule_type == 'session_budget':
            return self._to_decimal_safe(params.get('max_session')) is not None
        if rule_type == 'cascade_cost':
            return self._to_decimal_safe(params.get('max_cascade_cost')) is not None
        if rule_type == 'hitl_threshold':
            if params.get('mode') == 'always':
                return True
            return self._to_decimal_safe(params.get('max_budget')) is not None
        if rule_type == 'replay':
            return True
        if rule_type == 'circuit':
            return True
        return False  # unknown rule type, the engine skips it silently

    def _trace_detail(self, rule: dict, transaction: dict, txn_amount: Decimal,
                      prior_transactions: list) -> dict | None:
        """Compute the actual-vs-threshold detail for a triggered rule."""
        rule_type = rule.get('type')
        params = rule.get('params', {})
        agent_id = transaction.get('agent_id')

        if rule_type == 'transaction_limit':
            return {
                "actual": self._fmt(txn_amount),
                "limit": self._fmt(self._to_decimal_safe(params.get('max_amount'))),
            }

        if rule_type == 'daily_total':
            max_daily = self._to_decimal_safe(params.get('max_daily'))
            daily_total = txn_amount
            txn_date = self._extract_date(transaction.get('timestamp'))
            for prior in prior_transactions:
                if agent_id and prior.get('agent_id') != agent_id:
                    continue
                prior_date = self._extract_date(prior.get('timestamp'))
                if txn_date and prior_date and prior_date == txn_date:
                    prior_amount = self._to_decimal_safe(prior.get('amount'))
                    if prior_amount is not None and prior_amount > 0:
                        daily_total += prior_amount
            return {
                "daily_total": self._fmt(daily_total),
                "max_daily": self._fmt(max_daily),
                "date": txn_date,
            }

        if rule_type == 'velocity':
            window_minutes = params.get('window_minutes')
            max_count = params.get('max_count')
            txn_ts = self._parse_ts(transaction.get('timestamp'))
            window_start = txn_ts - timedelta(minutes=window_minutes)
            count_in_window = 0
            for prior in prior_transactions:
                if agent_id and prior.get('agent_id') != agent_id:
                    continue
                prior_ts = self._parse_ts(prior.get('timestamp'))
                if prior_ts and window_start <= prior_ts <= txn_ts:
                    count_in_window += 1
            return {
                "count_in_window": count_in_window + 1,
                "window_minutes": window_minutes,
                "max_count": max_count,
            }

        if rule_type == 'merchant_allowlist':
            return {
                "merchant": transaction.get('merchant'),
                "allowed": params.get('allowed', []),
            }

        if rule_type == 'category_block':
            return {
                "category": transaction.get('category'),
                "blocked": params.get('blocked', []),
            }

        if rule_type == 'session_budget':
            max_session = self._to_decimal_safe(params.get('max_session'))
            session_field = params.get('session_id', 'session_id')
            session_id = transaction.get(session_field)
            session_total = txn_amount
            for prior in prior_transactions:
                if agent_id and prior.get('agent_id') != agent_id:
                    continue
                if prior.get(session_field) == session_id:
                    prior_amount = self._to_decimal_safe(prior.get('amount'))
                    if prior_amount is not None and prior_amount > 0:
                        session_total += prior_amount
            return {
                "session_total": self._fmt(session_total),
                "max_session": self._fmt(max_session),
                "session_id": session_id,
            }

        if rule_type == 'cascade_cost':
            max_cascade = self._to_decimal_safe(params.get('max_cascade_cost'))
            pre_computed = self._to_decimal_safe(transaction.get('estimated_cascade_cost'))
            if pre_computed is not None:
                cascade_cost = pre_computed
                fail_probability = None
                reversal_cost = None
            else:
                fail_probability = params.get('fail_probability', transaction.get('fail_probability'))
                reversal_cost = self._to_decimal_safe(
                    params.get('reversal_cost', transaction.get('reversal_cost'))
                )
                if fail_probability is not None and reversal_cost is not None:
                    fp = Decimal(str(fail_probability))
                    cascade_cost = txn_amount + (fp * reversal_cost)
                else:
                    cascade_cost = txn_amount
            detail = {
                "cascade_cost": self._fmt(cascade_cost),
                "max_cascade_cost": self._fmt(max_cascade),
            }
            if fail_probability is not None:
                detail["fail_probability"] = fail_probability
            if reversal_cost is not None:
                detail["reversal_cost"] = self._fmt(reversal_cost)
            return detail

        if rule_type == 'hitl_threshold':
            max_budget = self._to_decimal_safe(params.get('max_budget'))
            session_field = params.get('session_id', 'session_id')
            session_id = transaction.get(session_field)
            session_total = txn_amount
            for prior in prior_transactions:
                if prior.get('agent_id') != agent_id:
                    continue
                if prior.get(session_field) == session_id:
                    prior_amount = self._to_decimal_safe(prior.get('amount'))
                    if prior_amount is not None and prior_amount > 0:
                        session_total += prior_amount
            remaining = max_budget - session_total if max_budget is not None else None
            return {
                "session_total": self._fmt(session_total),
                "max_budget": self._fmt(max_budget) if max_budget is not None else None,
                "remaining": self._fmt(remaining) if remaining is not None else None,
            }

        if rule_type == 'replay':
            return {"nonce": transaction.get(params.get('field', 'nonce'))}

        if rule_type == 'circuit':
            return {"circuit_tripped": transaction.get(params.get('state_field', 'circuit_tripped')) is True}

        return None

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
        elif rule_type == 'session_budget':
            return self._check_session_budget(rule_id, transaction, txn_amount, prior_transactions, params, action)
        elif rule_type == 'cascade_cost':
            return self._check_cascade_cost(rule_id, txn_amount, transaction, params, action)
        elif rule_type == 'hitl_threshold':
            return self._check_hitl_threshold(rule_id, transaction, txn_amount, prior_transactions, params, action)
        elif rule_type == 'replay':
            return self._check_replay(rule_id, transaction, prior_transactions, params, action)
        elif rule_type == 'circuit':
            return self._check_circuit(rule_id, transaction, params, action)
        else:
            # Unknown rule type, skip silently
            return None

    def _check_transaction_limit(self, rule_id: str, txn_amount: Decimal, params: dict, action: str):
        max_amount = self._to_decimal_safe(params.get('max_amount'))
        if max_amount is None:
            return None
        if txn_amount <= 0:
            return self._make_result(action, rule_id,
                f"Transaction amount ${self._fmt(txn_amount)} is not a positive value")
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
                if prior_amount is not None and prior_amount > 0:
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

    def _check_session_budget(self, rule_id: str, transaction: dict, txn_amount: Decimal,
                              prior_transactions: list, params: dict, action: str):
        """
        Session-scoped budget with optional decay tightening.
        Inspired by HeartFlow's session budget pattern (via @yun520-1 on OpenClaw #42475).

        A missing/None `session_id` is treated as a real "default" session: prior
        transactions whose session_id is also None are summed into the same bucket,
        so the budget can never be bypassed by omitting the id (issue #7).

        Params:
          max_session: Maximum cumulative spend per session
          session_id:  Field name in transaction to identify session (default: 'session_id')
          decay_factor: Optional tightening factor (0.0-1.0). Each call's effective
                       threshold shrinks as session spend accumulates.
          require_session_id: Optional bool (default False). When True, a transaction
                       whose session_id is None/missing is blocked (or flagged, per
                       `action`) because callers must always provide a session id for
                       budget tracking, strict guardrail mode.
        """
        max_session = self._to_decimal_safe(params.get('max_session'))
        if max_session is None:
            return None

        session_field = params.get('session_id', 'session_id')
        session_id = transaction.get(session_field)
        agent_id = transaction.get('agent_id')
        decay_factor = params.get('decay_factor')

        # Strict guardrail: session identity is mandatory for budget tracking.
        if params.get('require_session_id') and session_id is None:
            return self._make_result(
                action, rule_id,
                f"session_id is required for session_budget tracking "
                f"(max_session=${self._fmt(max_session)})"
            )

        # Sum prior transactions in the same session. Equality (not truthiness) is
        # used so a None session_id matches prior None-session transactions: they
        # all belong to the same "default/unnamed" session bucket.
        session_total = txn_amount
        for prior in prior_transactions:
            if agent_id and prior.get('agent_id') != agent_id:
                continue
            if prior.get(session_field) == session_id:
                prior_amount = self._to_decimal_safe(prior.get('amount'))
                if prior_amount is not None and prior_amount > 0:
                    session_total += prior_amount

        if session_total > max_session:
            return self._make_result(action, rule_id,
                f"Session spend ${self._fmt(session_total)} exceeds session budget of ${self._fmt(max_session)}")

        # Apply decay tightening if configured
        if decay_factor is not None:
            try:
                decay = float(decay_factor)
                if 0 < decay < 1:
                    remaining = max_session - session_total
                    effective_threshold = txn_amount  # base check
                    # Tighten: if remaining budget is < decay × max_session, per-call threshold shrinks
                    if remaining < max_session * Decimal(str(decay)):
                        # Per-call limit shrinks proportionally to remaining budget
                        per_call_cap = remaining * Decimal(str(decay))
                        if txn_amount > per_call_cap and per_call_cap > Decimal('0'):
                            return self._make_result(action, rule_id,
                                f"Session decay: per-call cap ${self._fmt(per_call_cap)} (remaining "
                                f"${self._fmt(remaining)} < {decay:.0%} of session budget)")
            except (ValueError, TypeError):
                pass

        return None

    def _check_cascade_cost(self, rule_id: str, txn_amount: Decimal, transaction: dict,
                            params: dict, action: str):
        """
        Pre-dispatch cascade cost estimation.
        Inspired by HeartFlow's adaptive controller (via @yun520-1 on OpenClaw #42475).

        Estimates expected value of a call including retry probability × reversal cost,
        and blocks if the cascade-adjusted cost exceeds a threshold.

        Params:
          max_cascade_cost: Threshold for cascade-adjusted cost
          fail_probability: Estimated probability of call failure (0.0-1.0)
          reversal_cost:    Cost of reversing/handling a failed call
          estimated_cascade_cost: Optionally pre-computed by the caller and passed in the transaction

        Transaction fields (optional, override params):
          fail_probability: Per-call failure probability
          reversal_cost:    Per-call reversal cost
          estimated_cascade_cost: Pre-computed cascade cost
        """
        max_cascade = self._to_decimal_safe(params.get('max_cascade_cost'))
        if max_cascade is None:
            return None

        # Check if caller pre-computed cascade cost
        pre_computed = self._to_decimal_safe(transaction.get('estimated_cascade_cost'))
        if pre_computed is not None:
            if pre_computed < 0:
                return self._make_result(action, rule_id,
                    f"Invalid negative cascade cost ${self._fmt(pre_computed)}")
            if pre_computed > max_cascade:
                return self._make_result(action, rule_id,
                    f"Cascade cost ${self._fmt(pre_computed)} exceeds limit of ${self._fmt(max_cascade)}")
            return None

        # Compute cascade cost: call_cost + fail_probability × reversal_cost
        fail_prob = params.get('fail_probability', transaction.get('fail_probability'))
        reversal_cost = self._to_decimal_safe(
            params.get('reversal_cost', transaction.get('reversal_cost'))
        )

        if fail_prob is not None and reversal_cost is not None:
            try:
                fp = Decimal(str(fail_prob))
                if fp < 0 or fp > 1:
                    return self._make_result(action, rule_id,
                        f"Invalid fail_probability {fp} (must be 0-1)")
                if reversal_cost < 0:
                    return self._make_result(action, rule_id,
                        f"Invalid negative reversal cost ${self._fmt(reversal_cost)}")
                cascade_cost = txn_amount + (fp * reversal_cost)
                if cascade_cost > max_cascade:
                    return self._make_result(action, rule_id,
                        f"Cascade cost ${self._fmt(cascade_cost)} (call ${self._fmt(txn_amount)} + "
                        f"{fp:.0%} × ${self._fmt(reversal_cost)}) exceeds limit of ${self._fmt(max_cascade)}")
            except (ValueError, TypeError, InvalidOperation):
                pass

        return None

    def _check_hitl_threshold(self, rule_id: str, transaction: dict, txn_amount: Decimal,
                              prior_transactions: list, params: dict, action: str):
        """Escalate to human review (REVIEW) instead of hard-blocking when a
        spend threshold is crossed. Mirrors SHACKLE SP/1.0 hitl_mode.

        Params:
          max_budget: session budget this threshold is measured against
          mode:       'always' (every call escalates) or 'on_threshold' (default)
          threshold:  fraction of budget (0.0-1.0) below which calls escalate (default 0.15)
          session_id: field name identifying the session (default 'session_id')

        This rule type always escalates to REVIEW; the configured action is
        ignored because the point of the rule is escalation, not hard-block.
        """
        mode = params.get('mode', 'on_threshold')
        if mode == 'always':
            return self._make_result('REVIEW', rule_id,
                "Human review required for every call (hitl mode 'always')")

        max_budget = self._to_decimal_safe(params.get('max_budget'))
        if max_budget is None or max_budget <= 0:
            return None
        threshold = params.get('threshold', 0.15)
        try:
            threshold_f = float(threshold)
        except (TypeError, ValueError):
            threshold_f = 0.15
        if threshold_f < 0 or threshold_f > 1:
            return None

        session_field = params.get('session_id', 'session_id')
        session_id = transaction.get(session_field)
        agent_id = transaction.get('agent_id')

        session_total = txn_amount
        for prior in prior_transactions:
            if prior.get('agent_id') != agent_id:
                continue
            if prior.get(session_field) == session_id:
                prior_amount = self._to_decimal_safe(prior.get('amount'))
                if prior_amount is not None and prior_amount > 0:
                    session_total += prior_amount

        remaining = max_budget - session_total
        if remaining <= 0:
            return self._make_result('REVIEW', rule_id,
                f"Budget exhausted (${self._fmt(session_total)} of ${self._fmt(max_budget)}); human review required")

        fraction = float(remaining) / float(max_budget)
        if fraction <= threshold_f:
            return self._make_result('REVIEW', rule_id,
                f"Remaining budget ${self._fmt(remaining)} is {fraction:.0%} of "
                f"${self._fmt(max_budget)} (threshold {threshold_f:.0%}); human review required")
        return None

    def _check_replay(self, rule_id: str, transaction: dict, prior_transactions: list,
                      params: dict, action: str):
        """Reject a replayed (duplicate) transaction by nonce. Mirrors SHACKLE
        SP/1.0 duplicate_nonce.

        Params:
          field: transaction field holding the single-use nonce (default 'nonce')
        """
        field = params.get('field', 'nonce')
        nonce = transaction.get(field)
        if nonce is None:
            return None
        for prior in prior_transactions:
            if prior.get(field) == nonce:
                return self._make_result(action, rule_id,
                    f"Duplicate nonce '{nonce}': transaction was already seen")
        return None

    def _check_circuit(self, rule_id: str, transaction: dict, params: dict, action: str):
        """Deny all calls while the circuit is tripped. Mirrors SHACKLE SP/1.0
        circuit_open. The runtime latches the trip (e.g. after N consecutive
        denials) and stamps it on the transaction; the engine deterministically
        denies while tripped.

        Params:
          state_field: transaction field carrying the circuit flag
                       (default 'circuit_tripped')
        """
        state_field = params.get('state_field', 'circuit_tripped')
        if transaction.get(state_field) is True:
            return self._make_result(action, rule_id,
                "Circuit open: enforcement paused pending human reset")
        return None

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
        """Format a Decimal for trace/reason output.

        Values that are already exact at 2 decimal places keep the tidy money
        form ("250.00"). Higher-precision values are emitted EXACTLY (never
        quantized), so trace ``detail`` never understates the evaluated amount
        (relevant for sub-cent pricing, token fractions, crypto amounts).
        """
        two_dp = d.quantize(Decimal('0.01'))
        if d == two_dp:
            return f"{two_dp}"
        return f"{d}"

    @staticmethod
    def _make_result(action: str, rule_id: str, reason: str) -> dict:
        """Build the result dict from an action string."""
        severity_map = {
            'BLOCK': 'high',
            'BLOCKED': 'high',
            'FLAG': 'medium',
            'FLAGGED': 'medium',
            'REVIEW': 'high',
            'HITL': 'high',
        }
        decision = action.upper()
        if decision == 'BLOCK':
            decision = 'BLOCKED'
        elif decision == 'FLAG':
            decision = 'FLAGGED'
        elif decision == 'HITL':
            decision = 'REVIEW'
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
