"""
AgentShield HTTP API Gateway
=============================
Stdlib-only HTTP server with ThreadingMixIn, CORS, and SSE.

Routes: 18 endpoints covering health, static serving, auth, agents,
rules, transactions, events (SSE), dashboard stats, email capture,
billing, blog, and eval.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import json
import threading
import queue
import os
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie
import mimetypes

# These will be set by run_app.py before the server starts
store = None
engine = None
auth = None


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


# ─── SSE Event Broadcasting ────────────────────────────────────────────────

_EVENT_SUBSCRIBERS = []
_EVENT_LOCK = threading.Lock()


def broadcast_event(event: dict):
    """Broadcast an event to all SSE subscribers."""
    with _EVENT_LOCK:
        dead = []
        for i, q in enumerate(_EVENT_SUBSCRIBERS):
            try:
                q.put_nowait(event)
            except queue.Full:
                dead.append(i)
        for i in reversed(dead):
            _EVENT_SUBSCRIBERS.pop(i)


class APIHandler(BaseHTTPRequestHandler):
    # Class-level attributes set by run_app.py
    store = None
    engine = None
    auth = None
    public_dir = None

    def log_message(self, format, *args):
        # Suppress default logging to keep output clean
        pass

    # ─── CORS ─────────────────────────────────────────────────────────────

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _handle_options(self):
        self.send_response(204)
        self._send_cors_headers()
        self.send_header('Content-Length', '0')
        self.end_headers()

    # ─── Response Helpers ─────────────────────────────────────────────────

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200):
        body = html.encode('utf-8') if isinstance(html, str) else html
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self._send_cors_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, status: int = 200, content_type: str = 'text/plain'):
        body = text.encode('utf-8') if isinstance(text, str) else text
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self._send_cors_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_redirect(self, location: str):
        self.send_response(302)
        self._send_cors_headers()
        self.send_header('Location', location)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _read_body(self) -> dict:
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")

    def _serve_file(self, filepath: str):
        """Serve a static file from public_dir."""
        if not os.path.exists(filepath):
            self._send_json({"error": "Not found"}, 404)
            return
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        with open(filepath, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self._send_cors_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ─── Auth Helpers ─────────────────────────────────────────────────────

    def _get_session_account(self) -> dict | None:
        """Extract session from cookie, return account dict or send 401."""
        cookie_header = self.headers.get('Cookie', '')
        token = None
        if cookie_header:
            cookie = SimpleCookie()
            try:
                cookie.load(cookie_header)
            except Exception:
                pass
            if 'session_token' in cookie:
                token = cookie['session_token'].value
        if not token:
            # Also check Authorization: Bearer for API-style session
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        if not token:
            self._send_json({"error": "Unauthorized"}, 401)
            return None
        account = self.auth.account_from_token(token)
        if not account:
            self._send_json({"error": "Unauthorized"}, 401)
            return None
        return account

    def _get_agent_account(self) -> dict | None:
        """Extract agent API key from Authorization header."""
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            self._send_json({"error": "Missing or invalid Authorization header"}, 401)
            return None
        api_key = auth_header[7:]
        agent = self.store.verify_api_key(api_key)
        if not agent:
            self._send_json({"error": "Invalid API key"}, 401)
            return None
        return agent

    def _set_session_cookie(self, token: str) -> str:
        return f"session_token={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400"

    # ─── Main Router ──────────────────────────────────────────────────────

    def do_GET(self):
        if self._handle_options_if_needed():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == '/health':
                self._send_json({"status": "ok", "version": "1.0.0"})
            elif path == '/':
                self._serve_file(os.path.join(self.public_dir, 'index.html'))
            elif path == '/dashboard':
                self._serve_file(os.path.join(self.public_dir, 'dashboard.html'))
            elif path == '/api/auth/me':
                self._handle_auth_me()
            elif path == '/api/agents':
                self._handle_list_agents()
            elif path == '/api/rules':
                self._handle_list_rules()
            elif path == '/api/dashboard/stats':
                self._handle_dashboard_stats()
            elif path == '/api/transactions':
                self._handle_list_transactions(parsed.query)
            elif path == '/v1/events':
                self._handle_sse()
            elif path == '/eval':
                self._handle_eval_results()
            elif path == '/blog' or path == '/blog/':
                self._serve_blog()
            elif path == '/pilot' or path == '/pilot/':
                self._serve_pilot()
            elif path.startswith('/tools/risk-calculator'):
                fpath = os.path.join(self.public_dir, 'tools', 'risk-calculator', 'index.html')
                self._serve_file(fpath)
            else:
                # Try to serve static assets from public/
                safe_path = os.path.normpath(path).lstrip('/')
                static_file = os.path.join(self.public_dir, safe_path)
                if os.path.isfile(static_file):
                    self._serve_file(static_file)
                else:
                    self._send_json({"error": "Not found"}, 404)
        except Exception as e:
            self._send_json({"error": f"Internal error: {str(e)}"}, 500)

    def do_POST(self):
        if self._handle_options_if_needed():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == '/api/auth/register':
                self._handle_register()
            elif path == '/api/auth/login':
                self._handle_login()
            elif path == '/api/auth/logout':
                self._handle_logout()
            elif path == '/api/agents':
                self._handle_create_agent()
            elif path == '/api/rules':
                self._handle_create_rule()
            elif path == '/v1/transactions/evaluate':
                self._handle_evaluate()
            elif path == '/api/email-capture':
                self._handle_email_capture()
            elif path == '/api/billing/checkout':
                self._handle_billing_checkout()
            elif path == '/api/billing/webhook':
                self._handle_billing_webhook()
            else:
                self._send_json({"error": "Not found"}, 404)
        except ValueError:
            self._send_json({"error": "Invalid JSON body"}, 400)
        except Exception as e:
            self._send_json({"error": f"Internal error: {str(e)}"}, 500)

    def do_PUT(self):
        if self._handle_options_if_needed():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            # /api/rules/<id>
            match = re.match(r'^/api/rules/(.+)$', path)
            if match:
                self._handle_update_rule(match.group(1))
            else:
                self._send_json({"error": "Not found"}, 404)
        except ValueError:
            self._send_json({"error": "Invalid JSON body"}, 400)
        except Exception as e:
            self._send_json({"error": f"Internal error: {str(e)}"}, 500)

    def do_DELETE(self):
        if self._handle_options_if_needed():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            match = re.match(r'^/api/rules/(.+)$', path)
            if match:
                self._handle_delete_rule(match.group(1))
            match_agent = re.match(r'^/api/agents/(.+)$', path)
            if match_agent:
                self._handle_deactivate_agent(match_agent.group(1))
            else:
                self._send_json({"error": "Not found"}, 404)
        except Exception as e:
            self._send_json({"error": f"Internal error: {str(e)}"}, 500)

    def do_OPTIONS(self):
        self._handle_options()

    def _handle_options_if_needed(self) -> bool:
        return False  # do_OPTIONS handles OPTIONS method

    # ─── Auth Handlers ────────────────────────────────────────────────────

    def _handle_register(self):
        body = self._read_body()
        email = body.get('email', '').strip()
        password = body.get('password', '')
        if not email or not password:
            self._send_json({"error": "Email and password required"}, 400)
            return
        if len(password) < 8:
            self._send_json({"error": "Password must be at least 8 characters"}, 400)
            return
        account = self.auth.register(email, password)
        if not account:
            self._send_json({"error": "Email already registered or invalid"}, 409)
            return
        # Auto-login: create session
        token = self.store.create_session(account['id'])
        cookie = self._set_session_cookie(token)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.send_header('Set-Cookie', cookie)
        response = {
            "id": account['id'],
            "email": account['email'],
            "tier": account.get('tier', 'free')
        }
        body_bytes = json.dumps(response, default=str).encode('utf-8')
        self.send_header('Content-Length', str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def _handle_login(self):
        body = self._read_body()
        email = body.get('email', '').strip()
        password = body.get('password', '')
        if not email or not password:
            self._send_json({"error": "Email and password required"}, 400)
            return
        result = self.auth.login(email, password)
        if not result['success']:
            self._send_json({"error": result['reason']}, 401)
            return
        cookie = self._set_session_cookie(result['token'])
        account = result['account']
        response = {
            "id": account['id'],
            "email": account['email'],
            "tier": account.get('tier', 'free')
        }
        body_bytes = json.dumps(response, default=str).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.send_header('Set-Cookie', cookie)
        self.send_header('Content-Length', str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def _handle_logout(self):
        cookie_header = self.headers.get('Cookie', '')
        token = None
        if cookie_header:
            cookie = SimpleCookie()
            try:
                cookie.load(cookie_header)
                if 'session_token' in cookie:
                    token = cookie['session_token'].value
            except Exception:
                pass
        if token:
            self.auth.logout(token)
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Set-Cookie', 'session_token=; Path=/; Max-Age=0')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _handle_auth_me(self):
        account = self._get_session_account()
        if not account:
            return
        self._send_json({
            "id": account['id'],
            "email": account['email'],
            "tier": account.get('tier', 'free')
        })

    # ─── Agent Handlers ───────────────────────────────────────────────────

    def _handle_list_agents(self):
        account = self._get_session_account()
        if not account:
            return
        agents = self.store.list_agents(account['id'])
        self._send_json({"agents": agents})

    def _handle_create_agent(self):
        account = self._get_session_account()
        if not account:
            return
        body = self._read_body()
        name = body.get('name', f'Agent-{datetime.now().strftime("%H%M%S")}')
        agent = self.store.create_agent(account['id'], name)
        self._send_json(agent, 201)

    def _handle_deactivate_agent(self, agent_id: str):
        account = self._get_session_account()
        if not account:
            return
        ok = self.store.deactivate_agent(account['id'], agent_id)
        self._send_json({"success": ok})

    # ─── Rule Handlers ────────────────────────────────────────────────────

    def _handle_list_rules(self):
        account = self._get_session_account()
        if not account:
            return
        rules = self.store.list_rules(account['id'])
        self._send_json({"rules": rules})

    def _handle_create_rule(self):
        account = self._get_session_account()
        if not account:
            return
        body = self._read_body()
        rule_type = body.get('type')
        priority = body.get('priority', 10)
        params = body.get('params', {})
        action = body.get('action', 'BLOCK')
        if not rule_type:
            self._send_json({"error": "Rule type required"}, 400)
            return
        rule_id = self.store.create_rule(
            account['id'], rule_type, priority, params, action
        )
        self._send_json({"id": rule_id, "message": "Rule created"}, 201)

    def _handle_update_rule(self, rule_id: str):
        account = self._get_session_account()
        if not account:
            return
        body = self._read_body()
        ok = self.store.update_rule(account['id'], rule_id, body)
        self._send_json({"success": ok})

    def _handle_delete_rule(self, rule_id: str):
        account = self._get_session_account()
        if not account:
            return
        ok = self.store.delete_rule(account['id'], rule_id)
        self._send_json({"success": ok})

    # ─── Transaction Handlers ─────────────────────────────────────────────

    def _handle_evaluate(self):
        """Core product endpoint: evaluate a transaction against rules."""
        agent = self._get_agent_account()
        if not agent:
            return

        body = self._read_body()
        transaction = body.get('transaction', body)

        # Validate transaction shape
        required = ['amount', 'merchant', 'category']
        if not all(k in transaction for k in required):
            self._send_json({'error': 'Missing required fields', 'required': required}, 400)
            return

        # Inject agent_id and timestamp if not provided
        transaction['agent_id'] = transaction.get('agent_id', agent['id'])
        transaction['id'] = transaction.get('id', f"txn_{uuid.uuid4().hex[:12]}")
        if 'timestamp' not in transaction:
            transaction['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Get rules and prior transactions
        rules = self.store.list_rules(agent['account_id'])
        prior = self.store.get_recent_transactions(agent['account_id'], agent['id'], 1440)

        # Evaluate
        result = self.engine.evaluate(transaction, rules, prior)

        # Record the transaction
        self.store.record_transaction(
            agent['account_id'], agent['id'],
            transaction['amount'], transaction['merchant'], transaction['category'],
            result['decision'], result.get('rule_triggered')
        )

        # Broadcast if blocked/flagged
        if result['decision'] in ('BLOCKED', 'FLAGGED'):
            broadcast_event({
                'type': result['decision'].lower(),
                'transaction': transaction,
                'reason': result['reason'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

        self._send_json(result)

    def _handle_list_transactions(self, query: str):
        account = self._get_session_account()
        if not account:
            return
        params = parse_qs(query)
        limit = int(params.get('limit', ['100'])[0])
        offset = int(params.get('offset', ['0'])[0])
        txns = self.store.list_transactions(account['id'], limit, offset)
        self._send_json({"transactions": txns})

    # ─── SSE Events ───────────────────────────────────────────────────────

    def _handle_sse(self):
        """Server-Sent Events stream for real-time blocked transaction alerts."""
        # Verify agent API key
        agent = self._get_agent_account()
        if not agent:
            return

        q = queue.Queue(maxsize=100)
        with _EVENT_LOCK:
            _EVENT_SUBSCRIBERS.append(q)

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self._send_cors_headers()
        self.end_headers()

        # Send initial keepalive
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
        except Exception:
            pass

        try:
            while True:
                try:
                    event = q.get(timeout=15)
                    data = json.dumps(event, default=str)
                    self.wfile.write(f"data: {data}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Keepalive ping
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _EVENT_LOCK:
                if q in _EVENT_SUBSCRIBERS:
                    _EVENT_SUBSCRIBERS.remove(q)

    # ─── Dashboard Stats ──────────────────────────────────────────────────

    def _handle_dashboard_stats(self):
        account = self._get_session_account()
        if not account:
            return
        agents = self.store.list_agents(account['id'])
        active_agents = [a for a in agents if a.get('active')]
        txns = self.store.list_transactions(account['id'], limit=500)
        today_txns = [t for t in txns if t.get('created_at', '').startswith(
            datetime.now(timezone.utc).strftime('%Y-%m-%d')
        )]
        blocked = [t for t in txns if t.get('decision') == 'BLOCKED']
        rules_list = self.store.list_rules(account['id'])
        self._send_json({
            "total_transactions": len(txns),
            "today_transactions": len(today_txns),
            "blocked_count": len(blocked),
            "active_agents": len(active_agents),
            "total_agents": len(agents),
            "rules_count": len(rules_list),
            "tier": account.get('tier', 'free'),
            "account_id": account['id']
        })

    # ─── Email Capture ────────────────────────────────────────────────────

    def _handle_email_capture(self):
        body = self._read_body()
        email = body.get('email', '').strip()
        source = body.get('source', 'landing')
        if not email or '@' not in email:
            self._send_json({"error": "Valid email required"}, 400)
            return
        capture_id = self.store.capture_email(email, source)
        self._send_json({"success": True, "id": capture_id}, 201)

    # ─── Billing (Stripe) ─────────────────────────────────────────────────

    def _handle_billing_checkout(self):
        account = self._get_session_account()
        if not account:
            return
        body = self._read_body()
        tier = body.get('tier')
        price_map = {
            'dev': os.getenv('STRIPE_PRICE_DEV'),
            'team': os.getenv('STRIPE_PRICE_TEAM'),
            'managed': os.getenv('STRIPE_PRICE_MANAGED')
        }
        price_id = price_map.get(tier)
        if not price_id:
            self._send_json({"error": "Invalid tier or Stripe not configured"}, 400)
            return
        # In production, create a Stripe Checkout Session here
        self._send_json({
            "message": "Stripe checkout requires server-side stripe library",
            "tier": tier,
            "price_id": price_id,
            "account_id": account['id']
        })

    def _handle_billing_webhook(self):
        body = self._read_body()
        event_type = body.get('type', '')
        if event_type == 'checkout.session.completed':
            # Activate license
            data = body.get('data', {}).get('object', {})
            account_id = data.get('client_reference_id')
            tier = data.get('metadata', {}).get('tier', 'dev')
            if account_id:
                from core.licensing import generate_license_key
                expires = '2027-12-31T23:59:59Z'
                key = generate_license_key(account_id, tier, expires)
                self.store.store_license(account_id, key, tier, expires)
                self.store.update_account_tier(account_id, tier)
                self._send_json({"success": True, "message": "License activated"})
                return
        elif event_type == 'customer.subscription.deleted':
            self._send_json({"success": True, "message": "Subscription deleted"})
            return
        self._send_json({"success": True, "message": "Webhook received"})

    # ─── Blog / Pilot / Eval ──────────────────────────────────────────────

    def _serve_blog(self):
        blog_path = os.path.join(
            os.path.dirname(self.public_dir), 'content', 'agent-kill-switch.md'
        )
        if os.path.exists(blog_path):
            with open(blog_path, 'r') as f:
                content = f.read()
            self._send_text(content, 200, 'text/markdown')
        else:
            self._send_json({"error": "Blog article not found"}, 404)

    def _serve_pilot(self):
        pilot_html = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentShield Pilot Program</title><style>
body{font-family:system-ui;background:#0a0a0a;color:#e8e8e8;max-width:800px;margin:0 auto;padding:40px;line-height:1.6}
h1{color:#00d4aa}.price{font-size:3em;color:#00d4aa;font-weight:700}
.btn{display:inline-block;padding:16px 32px;background:#00d4aa;color:#000;text-decoration:none;border-radius:8px;font-weight:700;margin-top:20px}
</style></head><body>
<h1>AgentShield Pilot Program</h1>
<p>We're onboarding 5 teams for a free 30-day pilot. You get:</p>
<ul><li>Up to 20 AI agents monitored</li><li>Custom spend-control rules</li><li>Real-time SSE alerts</li><li>Direct engineering support</li></ul>
<p class="price">Free for 30 days</p>
<a class="btn" href="/api/auth/register">Apply for Pilot →</a>
</body></html>"""
        self._send_html(pilot_html)

    def _handle_eval_results(self):
        try:
            from tests.eval_gym import run_eval, generate_report
            results = run_eval()
            self._send_json(results)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
