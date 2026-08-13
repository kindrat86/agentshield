"""
AgentShield, The Safety Layer for Autonomous AI

A per-transaction enforcement engine for AI agents.
Evaluates every API call against your rules in <1ms before it executes.
Pure Python 3.11 stdlib. Zero dependencies. MIT licensed.

Quick Start:
    from agentshield import SpendControlEngine, run_eval

    engine = SpendControlEngine()
    result = engine.evaluate(transaction, rules, prior_transactions)
    print(result["decision"])  # APPROVED, BLOCKED, or FLAGGED

    # Run the 56-scenario eval gym:
    results = run_eval()
    print(f"{results['passed']}/{results['total']} passed")

    # Emergency scan:
    # python -m agentshield.emergency

    # Kill switch:
    # python -m agentshield.kill
"""

from agentshield.engine import SpendControlEngine
from agentshield.emitter import SpendEvaluationEmitter
from agentshield.eval_gym import run_eval, SCENARIOS

__version__ = "1.2.0"
__author__ = "Maryan K."
__license__ = "MIT"

__all__ = ["SpendControlEngine", "SpendEvaluationEmitter", "run_eval", "SCENARIOS"]
