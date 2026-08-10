"""
AgentShield Cryptographic Licensing
====================================
Offline-verifiable license keys using HMAC-SHA256.

Architecture:
  - Server generates license keys signed with a master secret.
  - Client validates keys locally without network calls.
  - Daily phone-home is a soft check, not a hard gate.

License Key Format:
  Base64( payload + "|" + signature_hex )
  payload = LICENSE_VERSION|account_id|tier|expires_at
  signature_hex = HMAC-SHA256(payload, MASTER_SECRET).hex()
"""

import hmac
import hashlib
import base64
import os
from datetime import datetime, timezone


# Master secret: 64 hex chars (32 bytes). Load from env or generate on first run.
# In production, ALWAYS set LICENSING_MASTER_SECRET in the environment.
MASTER_SECRET = os.environ.get(
    'LICENSING_MASTER_SECRET',
    hashlib.sha256(b'agentshield-default-dev-secret-do-not-use-in-prod').hexdigest()
)
LICENSE_VERSION = 1


def generate_license_key(account_id: str, tier: str, expires_at: str) -> str:
    """
    Generate a signed, base64-encoded license key.

    Args:
        account_id: The account identifier.
        tier: One of 'free', 'dev', 'team', 'managed'.
        expires_at: ISO format datetime string (e.g., '2027-01-01T00:00:00Z').

    Returns:
        Base64-encoded license key string.
    """
    payload = f"{LICENSE_VERSION}|{account_id}|{tier}|{expires_at}"
    signature = hmac.new(
        MASTER_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()
    combined = payload + "|" + signature.hex()
    return base64.b64encode(combined.encode()).decode()


def validate_license_key(license_key_b64: str) -> dict:
    """
    Validate a base64-encoded license key offline.

    Args:
        license_key_b64: The base64-encoded license key.

    Returns:
        On success: {"valid": True, "account_id": ..., "tier": ..., "expires_at": ...}
        On failure: {"valid": False, "reason": ...}
    """
    if not license_key_b64:
        return {"valid": False, "reason": "Empty license key"}

    try:
        decoded = base64.b64decode(license_key_b64).decode()
    except Exception:
        return {"valid": False, "reason": "Invalid base64 encoding"}

    # Split on last '|' to separate payload from signature
    parts = decoded.rsplit('|', 1)
    if len(parts) != 2:
        return {"valid": False, "reason": "Malformed license key structure"}

    payload, signature_hex = parts

    # Recompute HMAC and compare in constant time
    expected_sig = hmac.new(
        MASTER_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    try:
        provided_sig = bytes.fromhex(signature_hex)
    except ValueError:
        return {"valid": False, "reason": "Invalid signature format"}

    if not hmac.compare_digest(expected_sig, provided_sig):
        return {"valid": False, "reason": "Invalid signature"}

    # Parse payload: version|account_id|tier|expires_at
    fields = payload.split('|')
    if len(fields) != 4:
        return {"valid": False, "reason": "Malformed payload"}

    version_str, account_id, tier, expires_at = fields

    try:
        version = int(version_str)
    except ValueError:
        return {"valid": False, "reason": "Invalid version"}

    if version != LICENSE_VERSION:
        return {"valid": False, "reason": f"Unsupported license version: {version}"}

    # Check expiration
    exp_ts = _parse_ts(expires_at)
    if exp_ts is None:
        return {"valid": False, "reason": "Invalid expiration format"}

    if datetime.now(timezone.utc) > exp_ts:
        return {"valid": False, "reason": "License expired"}

    return {
        "valid": True,
        "account_id": account_id,
        "tier": tier,
        "expires_at": expires_at
    }


def get_tier_limits(tier: str) -> dict:
    """Return the limits for a given tier."""
    limits = {
        "free":    {"max_agents": 1, "max_rules": 0, "max_daily_txns": 100,   "can_approve": False},
        "dev":     {"max_agents": 5, "max_rules": 10, "max_daily_txns": 1000,  "can_approve": False},
        "team":    {"max_agents": 20, "max_rules": 50, "max_daily_txns": 5000,  "can_approve": True},
        "managed": {"max_agents": 100, "max_rules": 200, "max_daily_txns": 50000, "can_approve": True},
    }
    return limits.get(tier, limits["free"])


def check_tier_compliance(store, account_id: str) -> dict:
    """
    Check whether an account is compliant with its tier limits.

    Args:
        store: A Store instance.
        account_id: The account to check.

    Returns:
        {"compliant": bool, "violations": [list of violation strings]}
    """
    violations = []

    account = store.get_account_by_id(account_id)
    if not account:
        return {"compliant": False, "violations": ["Account not found"]}

    tier = account.get('tier', 'free')
    limits = get_tier_limits(tier)

    active_agents = store.count_active_agents(account_id)
    if active_agents > limits['max_agents']:
        violations.append(
            f"Active agents ({active_agents}) exceeds tier limit ({limits['max_agents']})"
        )

    active_license = store.get_active_license(account_id)
    if active_license:
        validation = validate_license_key(active_license['license_key'])
        if not validation['valid']:
            violations.append(f"License invalid: {validation['reason']}")

    return {
        "compliant": len(violations) == 0,
        "violations": violations
    }


def _parse_ts(ts_str: str) -> datetime | None:
    """Parse an ISO timestamp string into an aware datetime."""
    if not ts_str:
        return None
    try:
        ts = ts_str
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None
