"""
AgentShield → Agent-Devtools event emitter
===========================================
Emits one JSON object per spend evaluation in the schema defined by
``docs/integrations/agent-devtools.md``, so Agent-Devtools can render AgentShield
decisions as a first-class trace source alongside the agent's own execution trace.

Delivery modes (all zero-dependency):
  - ndjson to stdout
  - ndjson appended to a file (for file tailing)
  - in-process callback (for embedding in an agent runtime)

Money stays Decimal-safe strings across the wire (the engine never uses float).
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Optional

from agentshield.engine import SpendControlEngine

SCHEMA_VERSION = "1.0"
EVENT_TYPE = "agentshield.spend.evaluation"


class SpendEvaluationEmitter:
    """Wraps a :class:`SpendControlEngine` and emits spend-evaluation events."""

    def __init__(self, engine: Optional[SpendControlEngine] = None):
        self.engine = engine if engine is not None else SpendControlEngine()

    def build_event(
        self,
        transaction: dict,
        rules: list,
        prior_transactions: Optional[list] = None,
        *,
        trace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> dict:
        """Build a full SpendEvaluationEvent dict (schema v1)."""
        prior = prior_transactions or []
        traced = self.engine.evaluate_with_trace(transaction, rules, prior)

        txn = transaction if isinstance(transaction, dict) else {}
        return {
            "schema_version": SCHEMA_VERSION,
            "event_type": EVENT_TYPE,
            "event_id": event_id or uuid.uuid4().hex,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "agent_id": agent_id if agent_id is not None else txn.get("agent_id"),
            "session_id": session_id if session_id is not None else txn.get("session_id"),
            "transaction": self._serialize_transaction(txn),
            "decision": traced["decision"],
            "evaluation": traced["evaluation"],
        }

    @staticmethod
    def _serialize_transaction(transaction: dict) -> dict:
        """Echo the transaction, converting Decimal values to Decimal-safe strings."""
        out = {}
        for key, value in transaction.items():
            if isinstance(value, Decimal):
                out[key] = str(value)
            else:
                out[key] = value
        return out

    def emit(
        self,
        transaction: dict,
        rules: list,
        prior_transactions: Optional[list] = None,
        *,
        on_event: Optional[Callable[[dict], None]] = None,
        **kwargs,
    ) -> dict:
        """Build the event and route it to the configured sinks.

        If ``on_event`` is given it is invoked with the event dict (in-process hook).
        Always returns the event dict so callers can handle it directly too.
        """
        event = self.build_event(transaction, rules, prior_transactions, **kwargs)
        if on_event is not None:
            on_event(event)
        return event

    @staticmethod
    def to_ndjson(event: dict) -> str:
        """Serialize a single event to one NDJSON line."""
        return json.dumps(event, default=str, ensure_ascii=False)

    def write_ndjson(self, event: dict, file=None) -> str:
        """Write one NDJSON line to ``file`` (default stdout) and return the line."""
        line = self.to_ndjson(event)
        target = sys.stdout if file is None else file
        target.write(line + "\n")
        if file is not None:
            target.flush()
        return line
