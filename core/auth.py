"""
AgentShield Multi-Tenant Auth
==============================
PBKDF2 password hashing and session management.

Uses PBKDF2-HMAC-SHA256 with 200,000 iterations for password hashing.
Sessions are stored in the database with 24-hour expiry.
"""

import hashlib
import base64
import os
import secrets
import hmac as hmac_mod
import re


class AuthManager:
    """Multi-tenant authentication and session management."""

    PBKDF2_ITERATIONS = 200000

    def __init__(self, store):
        self.store = store

    def hash_password(self, password: str) -> str:
        """
        Hash a password using PBKDF2-HMAC-SHA256.

        Returns: base64(salt) + "$" + base64(hash)
        """
        salt = os.urandom(16)
        hash_val = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt, self.PBKDF2_ITERATIONS
        )
        return base64.b64encode(salt).decode() + "$" + base64.b64encode(hash_val).decode()

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against a stored hash. Constant-time comparison."""
        if not stored_hash or '$' not in stored_hash:
            return False
        parts = stored_hash.split('$', 1)
        if len(parts) != 2:
            return False
        try:
            salt = base64.b64decode(parts[0])
            stored = base64.b64decode(parts[1])
        except Exception:
            return False

        computed = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt, self.PBKDF2_ITERATIONS
        )
        return hmac_mod.compare_digest(stored, computed)

    def register(self, email: str, password: str) -> dict | None:
        """
        Register a new account.

        Returns account dict on success, None on failure (duplicate email, invalid input).
        """
        # Validate email format
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return None
        if not password or len(password) < 8:
            return None

        # Check email uniqueness
        existing = self.store.get_account_by_email(email)
        if existing:
            return None

        # Hash and create
        password_hash = self.hash_password(password)
        account_id = self.store.create_account(email, password_hash)
        if not account_id:
            return None

        return self.store.get_account_by_id(account_id)

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate and create a session.

        Returns {"success": True, "token": ..., "account": ...} or
                {"success": False, "reason": "Invalid credentials"}.
        """
        account = self.store.get_account_by_email(email)
        if not account:
            return {"success": False, "reason": "Invalid credentials"}

        if not self.verify_password(password, account['password_hash']):
            return {"success": False, "reason": "Invalid credentials"}

        token = self.store.create_session(account['id'], duration_hours=24)

        return {
            "success": True,
            "token": token,
            "account": {
                "id": account['id'],
                "email": account['email'],
                "tier": account.get('tier', 'free')
            }
        }

    def logout(self, token: str) -> bool:
        """Delete a session, logging the user out."""
        return self.store.delete_session(token)

    def account_from_token(self, token: str) -> dict | None:
        """
        Validate a session token and return the account dict.

        If the session is expired, deletes it and returns None.
        """
        if not token:
            return None
        return self.store.validate_session(token)
