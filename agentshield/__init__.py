"""
AgentShield — Firewall for AI Agent Spending

Pure Python 3.11 stdlib. Zero dependencies.
9 composable rule types evaluated per-transaction in <1ms.

Quick Start:
    from agentshield import SpendControlEngine

    engine = SpendControlEngine()
    result = engine.evaluate(transaction, rules, prior_transactions)
    # result['decision'] -> 'APPROVED', 'BLOCKED', or 'FLAGGED'

Run the 56-scenario eval gym:
    from agentshield import run_eval
    results = run_eval()
    print(f"{results['passed']}/{results['total']} passed")
"""
from .engine import SpendControlEngine
from .eval_gym import run_eval, SCENARIOS

__version__ = "1.0.0"
__all__ = ["SpendControlEngine", "run_eval", "SCENARIOS"]
