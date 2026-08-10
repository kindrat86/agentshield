#!/usr/bin/env python3
"""
AgentShield Unified Entrypoint
===============================
Launches the HTTP API server with all components wired up.

Usage:
    python3.11 run_app.py              # Default port 7100
    PORT=8000 python3.11 run_app.py    # Custom port
"""

import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.store import Store
from core.engine import SpendControlEngine
from core.auth import AuthManager
from core.api import ThreadedHTTPServer, APIHandler


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    port = int(os.getenv('PORT', 7100))
    public_dir = os.path.join(project_root, 'public')
    db_path = os.getenv('DB_PATH', os.path.join(project_root, 'agentshield.db'))

    # Initialize components
    store = Store(db_path)
    engine = SpendControlEngine()
    auth = AuthManager(store)

    # Wire up handler class attributes
    APIHandler.store = store
    APIHandler.engine = engine
    APIHandler.auth = auth
    APIHandler.public_dir = public_dir

    server = ThreadedHTTPServer(('0.0.0.0', port), APIHandler)
    print(f"AgentShield API running on port {port}")
    print(f"  Database: {db_path}")
    print(f"  Public dir: {public_dir}")
    print(f"  Health: http://localhost:{port}/health")
    print(f"  Landing: http://localhost:{port}/")
    print(f"  Dashboard: http://localhost:{port}/dashboard")
    print(f"  Risk Calculator: http://localhost:{port}/tools/risk-calculator/")
    print(f"  Eval: http://localhost:{port}/eval")
    server.serve_forever()


if __name__ == '__main__':
    main()
