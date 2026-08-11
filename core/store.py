"""
AgentShield Thread-Safe Multi-Tenant Storage
=============================================
SQLite-backed storage with WAL mode and a global write lock.

Multi-tenant isolation is enforced at the query level: every method that reads
or writes tenant data MUST scope by account_id. This is the core security invariant.
"""

import sqlite3
import threading
import uuid
import json
import secrets
from datetime import datetime, timedelta, timezone


# Module-level shared lock. Every method that writes to the DB acquires this.
_DB_LOCK = threading.Lock()


class Store:
    """Thread-safe SQLite multi-tenant storage for AgentShield."""

    def __init__(self, db_path: str = "agentshield.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local connection (each thread gets its own)."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        """Create all tables if they don't exist."""
        conn = self._get_conn()
        with _DB_LOCK:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    tier TEXT DEFAULT 'free',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    api_key TEXT UNIQUE,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    merchant TEXT,
                    category TEXT,
                    decision TEXT,
                    rule_triggered TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                );

                CREATE TABLE IF NOT EXISTS rules (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    params TEXT,
                    action TEXT DEFAULT 'BLOCK',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                );

                CREATE TABLE IF NOT EXISTS licenses (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    license_key TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                );

                CREATE TABLE IF NOT EXISTS email_sequence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    capture_id TEXT,
                    step TEXT,
                    send_at REAL,
                    sent INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS email_captures (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    source TEXT DEFAULT 'landing',
                    created_at TEXT NOT NULL
                );
            """)
            conn.commit()

    # ─── Account Management ───────────────────────────────────────────────

    def create_account(self, email: str, password_hash: str, tier: str = "free") -> str:
        account_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        with _DB_LOCK:
            try:
                conn.execute(
                    "INSERT INTO accounts (id, email, password_hash, tier, created_at) VALUES (?, ?, ?, ?, ?)",
                    (account_id, email, password_hash, tier, now)
                )
                conn.commit()
                return account_id
            except sqlite3.IntegrityError:
                return None

    def get_account_by_email(self, email: str) -> dict | None:
        conn = self._get_conn()
        with _DB_LOCK:
            row = conn.execute(
                "SELECT * FROM accounts WHERE email = ?", (email,)
            ).fetchone()
        return dict(row) if row else None

    def get_account_by_id(self, account_id: str) -> dict | None:
        conn = self._get_conn()
        with _DB_LOCK:
            row = conn.execute(
                "SELECT * FROM accounts WHERE id = ?", (account_id,)
            ).fetchone()
        return dict(row) if row else None

    def update_account_tier(self, account_id: str, tier: str) -> bool:
        conn = self._get_conn()
        with _DB_LOCK:
            cur = conn.execute(
                "UPDATE accounts SET tier = ? WHERE id = ?", (tier, account_id)
            )
            conn.commit()
            return cur.rowcount > 0

    # ─── Agent Management (scoped by account_id) ──────────────────────────

    def create_agent(self, account_id: str, name: str) -> dict:
        agent_id = uuid.uuid4().hex
        api_key = "as_live_" + secrets.token_hex(16)
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        with _DB_LOCK:
            conn.execute(
                "INSERT INTO agents (id, account_id, name, api_key, active, created_at) "
                "VALUES (?, ?, ?, ?, 1, ?)",
                (agent_id, account_id, name, api_key, now)
            )
            conn.commit()
        return {"id": agent_id, "account_id": account_id, "name": name,
                "api_key": api_key, "active": 1, "created_at": now}

    def list_agents(self, account_id: str) -> list[dict]:
        conn = self._get_conn()
        with _DB_LOCK:
            rows = conn.execute(
                "SELECT * FROM agents WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def verify_api_key(self, api_key: str) -> dict | None:
        """Returns agent dict with account_id, or None."""
        conn = self._get_conn()
        with _DB_LOCK:
            row = conn.execute(
                "SELECT * FROM agents WHERE api_key = ? AND active = 1",
                (api_key,)
            ).fetchone()
        return dict(row) if row else None

    def deactivate_agent(self, account_id: str, agent_id: str) -> bool:
        conn = self._get_conn()
        with _DB_LOCK:
            cur = conn.execute(
                "UPDATE agents SET active = 0 WHERE id = ? AND account_id = ?",
                (agent_id, account_id)
            )
            conn.commit()
            return cur.rowcount > 0

    def count_active_agents(self, account_id: str) -> int:
        conn = self._get_conn()
        with _DB_LOCK:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM agents WHERE account_id = ? AND active = 1",
                (account_id,)
            ).fetchone()
        return row['cnt']

    # ─── Transaction Management (scoped by account_id) ────────────────────

    def record_transaction(self, account_id: str, agent_id: str, amount: float,
                           merchant: str, category: str, decision: str,
                           rule_triggered: str | None) -> str:
        txn_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        with _DB_LOCK:
            conn.execute(
                "INSERT INTO transactions (id, account_id, agent_id, amount, merchant, category, "
                "decision, rule_triggered, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (txn_id, account_id, agent_id, float(amount), merchant, category,
                 decision, rule_triggered, now)
            )
            conn.commit()
        return txn_id

    def list_transactions(self, account_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        conn = self._get_conn()
        with _DB_LOCK:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE account_id = ? "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (account_id, limit, offset)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_todays_transactions(self, account_id: str, agent_id: str) -> list[dict]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = self._get_conn()
        with _DB_LOCK:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE account_id = ? AND agent_id = ? "
                "AND created_at LIKE ? ORDER BY created_at DESC",
                (account_id, agent_id, f"{today}%")
            ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_transactions(self, account_id: str, agent_id: str, minutes: int) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        cutoff_str = cutoff.isoformat()
        conn = self._get_conn()
        with _DB_LOCK:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE account_id = ? AND agent_id = ? "
                "AND created_at >= ? ORDER BY created_at DESC",
                (account_id, agent_id, cutoff_str)
            ).fetchall()
        return [dict(r) for r in rows]

    # ─── Rule Management (scoped by account_id) ───────────────────────────

    def create_rule(self, account_id: str, rule_type: str, priority: int,
                    params: dict, action: str) -> str:
        rule_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        with _DB_LOCK:
            conn.execute(
                "INSERT INTO rules (id, account_id, type, priority, params, action, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rule_id, account_id, rule_type, priority, json.dumps(params), action, now)
            )
            conn.commit()
        return rule_id

    def list_rules(self, account_id: str) -> list[dict]:
        conn = self._get_conn()
        with _DB_LOCK:
            rows = conn.execute(
                "SELECT * FROM rules WHERE account_id = ? ORDER BY priority ASC",
                (account_id,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d['params'] = json.loads(d.get('params', '{}'))
            except (json.JSONDecodeError, TypeError):
                d['params'] = {}
            result.append(d)
        return result

    def update_rule(self, account_id: str, rule_id: str, updates: dict) -> bool:
        allowed = ['type', 'priority', 'params', 'action']
        sets = []
        vals = []
        for k in allowed:
            if k in updates:
                sets.append(f"{k} = ?")
                if k == 'params':
                    vals.append(json.dumps(updates[k]))
                else:
                    vals.append(updates[k])
        if not sets:
            return False
        vals.append(rule_id)
        vals.append(account_id)
        conn = self._get_conn()
        with _DB_LOCK:
            cur = conn.execute(
                f"UPDATE rules SET {', '.join(sets)} WHERE id = ? AND account_id = ?",
                vals
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_rule(self, account_id: str, rule_id: str) -> bool:
        conn = self._get_conn()
        with _DB_LOCK:
            cur = conn.execute(
                "DELETE FROM rules WHERE id = ? AND account_id = ?",
                (rule_id, account_id)
            )
            conn.commit()
            return cur.rowcount > 0

    # ─── License Management ───────────────────────────────────────────────

    def store_license(self, account_id: str, license_key: str, tier: str, expires_at: str) -> str:
        license_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        with _DB_LOCK:
            conn.execute(
                "INSERT INTO licenses (id, account_id, license_key, tier, expires_at, active, created_at) "
                "VALUES (?, ?, ?, ?, ?, 1, ?)",
                (license_id, account_id, license_key, tier, expires_at, now)
            )
            conn.commit()
        return license_id

    def get_active_license(self, account_id: str) -> dict | None:
        conn = self._get_conn()
        with _DB_LOCK:
            row = conn.execute(
                "SELECT * FROM licenses WHERE account_id = ? AND active = 1 "
                "ORDER BY created_at DESC LIMIT 1",
                (account_id,)
            ).fetchone()
        return dict(row) if row else None

    def deactivate_license(self, account_id: str, license_id: str) -> bool:
        conn = self._get_conn()
        with _DB_LOCK:
            cur = conn.execute(
                "UPDATE licenses SET active = 0 WHERE id = ? AND account_id = ?",
                (license_id, account_id)
            )
            conn.commit()
            return cur.rowcount > 0

    # ─── Session Management ───────────────────────────────────────────────

    def create_session(self, account_id: str, duration_hours: int = 24) -> str:
        token = secrets.token_hex(32)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=duration_hours)
        conn = self._get_conn()
        with _DB_LOCK:
            conn.execute(
                "INSERT INTO sessions (token, account_id, expires_at, created_at) "
                "VALUES (?, ?, ?, ?)",
                (token, account_id, expires.isoformat(), now.isoformat())
            )
            conn.commit()
        return token

    def validate_session(self, token: str) -> dict | None:
        conn = self._get_conn()
        with _DB_LOCK:
            row = conn.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            if not row:
                return None
            expires_at_str = row['expires_at']
            try:
                expires_dt = datetime.fromisoformat(expires_at_str)
                if datetime.now(timezone.utc) > expires_dt:
                    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                    conn.commit()
                    return None
            except ValueError:
                return None
            account_id = row['account_id']
            acct_row = conn.execute(
                "SELECT * FROM accounts WHERE id = ?", (account_id,)
            ).fetchone()
            return dict(acct_row) if acct_row else None

    def delete_session(self, token: str) -> bool:
        conn = self._get_conn()
        with _DB_LOCK:
            cur = conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return cur.rowcount > 0

    # ─── Email Capture ────────────────────────────────────────────────────

    def capture_email(self, email: str, source: str = "landing") -> str:
        capture_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        with _DB_LOCK:
            conn.execute(
                "INSERT INTO email_captures (id, email, source, created_at) "
                "VALUES (?, ?, ?, ?)",
                (capture_id, email, source, now)
            )
            conn.commit()
        return capture_id

    def list_emails(self, limit: int = 100) -> list[dict]:
        conn = self._get_conn()
        with _DB_LOCK:
            rows = conn.execute(
                "SELECT * FROM email_captures ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
