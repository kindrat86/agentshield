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

    # ─── Badge Handler ────────────────────────────────────────────────────

    def _handle_badge(self, path: str):
        """Serve dynamic SVG badges. /badge/protected → 'Protected by AgentShield' badge.
           /badge/score/<n> → color-coded risk score badge."""
        badge_type = path.split('/badge/', 1)[1] if '/badge/' in path else ''

        if badge_type == 'protected' or badge_type == 'protected/':
            svg = self._badge_protected_svg()
            self._serve_svg(svg, 86400)
        elif badge_type.startswith('score/'):
            try:
                score_str = badge_type.split('score/', 1)[1].rstrip('/')
                score = max(0, min(100, int(score_str)))
                svg = self._badge_score_svg(score)
                self._serve_svg(svg, 3600)
            except (ValueError, IndexError):
                self._send_json({"error": "Invalid score. Use /badge/score/0-100"}, 400)
        else:
            self._send_json({"error": "Badge not found. Try /badge/protected or /badge/score/85"}, 404)

    def _serve_svg(self, svg: str, max_age: int = 86400):
        body = svg.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'image/svg+xml')
        self.send_header('Cache-Control', f'public, max-age={max_age}')
        self._send_cors_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _badge_protected_svg(self) -> str:
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="210" height="28" role="img" aria-label="Protected by AgentShield">
  <title>Protected by AgentShield</title>
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#141414"/><stop offset="100%" stop-color="#1a1a1a"/></linearGradient></defs>
  <rect width="210" height="28" rx="6" fill="url(#g)" stroke="#00d4aa" stroke-width="1"/>
  <text x="10" y="19" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="12" font-weight="700" fill="#00d4aa">🛡 Protected by</text>
  <text x="130" y="19" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="12" font-weight="700" fill="#e8e8e8">AgentShield</text>
</svg>'''

    def _badge_score_svg(self, score: int) -> str:
        if score < 33: color, label = '#00d4aa', 'LOW RISK'
        elif score < 66: color, label = '#ffa502', 'MODERATE'
        else: color, label = '#ff4757', 'HIGH RISK'
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="260" height="28" role="img" aria-label="Agent Risk Score: {score}/100, {label}">
  <title>Agent Spend Risk Score: {score}/100 ({label})</title>
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#141414"/><stop offset="100%" stop-color="#1a1a1a"/></linearGradient></defs>
  <rect width="260" height="28" rx="6" fill="url(#g)" stroke="{color}" stroke-width="1"/>
  <text x="10" y="19" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="12" font-weight="600" fill="#888">Agent Risk Score</text>
  <text x="138" y="19" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="13" font-weight="800" fill="{color}">{score}/100</text>
  <text x="193" y="19" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" font-weight="700" fill="{color}">{label}</text>
</svg>'''

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
        return f"session_token={token}; Path=/; SameSite=Lax; Max-Age=86400"

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
            elif path == '/api/auth/google':
                self._handle_google_auth()
            elif path == '/api/auth/google/callback':
                self._handle_google_callback()
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
            elif path == '/comparisons' or path == '/comparisons/':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'index.html'))
            elif path == '/comparisons/helicone':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'helicone.html'))
            elif path == '/comparisons/langsmith':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'langsmith.html'))
            elif path == '/comparisons/portkey':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'portkey.html'))
            elif path == '/comparisons/braintrust':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'braintrust.html'))
            elif path == '/comparisons/agentops':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'agentops.html'))
            elif path == '/comparisons/langfuse':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'langfuse.html'))
            elif path == '/comparisons/wandb':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'wandb.html'))
            elif path == '/comparisons/galileo':
                self._serve_file(os.path.join(self.public_dir, 'comparisons', 'galileo.html'))
            elif path == '/eval-gym-spec':
                self._serve_file(os.path.join(self.public_dir, 'eval-gym-spec.html'))
            elif path == '/blog/zeroclaw-preflight-enforcement' or path == '/blog/how-zeroclaw-implemented-preflight-enforcement':
                self._serve_file(os.path.join(self.public_dir, 'blog', 'how-zeroclaw-implemented-preflight-enforcement.html'))
            elif path == '/audit':
                self._serve_file(os.path.join(self.public_dir, 'audit.html'))
            elif path == '/free-audit':
                self._serve_file(os.path.join(self.public_dir, 'free-audit.html'))
            elif path == '/the-2800-story':
                self._serve_file(os.path.join(self.public_dir, 'the-2800-story.html'))
            elif path == '/challenge':
                self._serve_file(os.path.join(self.public_dir, 'challenge.html'))
            elif path == '/bounty':
                self._serve_file(os.path.join(self.public_dir, 'bounty.html'))
            elif path == '/sitemap.xml':
                self._serve_file(os.path.join(self.public_dir, 'sitemap.xml'))
            elif path == '/embed' or path == '/embed/':
                self._serve_file(os.path.join(self.public_dir, 'embed.html'))
            elif path == '/embed/risk-calculator' or path == '/embed/risk-calculator/':
                self._serve_file(os.path.join(self.public_dir, 'embed', 'risk-calculator', 'index.html'))
            elif path.startswith('/badge/'):
                self._handle_badge(path)
            elif path == '/auth' or path == '/login' or path == '/register':
                self._serve_file(os.path.join(self.public_dir, 'auth.html'))
            elif path == '/tripwire':
                self._serve_file(os.path.join(self.public_dir, 'tripwire.html'))
            elif path == '/checkout':
                self._serve_file(os.path.join(self.public_dir, 'checkout-bump.html'))
            elif path == '/api/stats/prevented':
                if self.store:
                    conn = self.store._get_conn()
                    from core.store import _DB_LOCK
                    with _DB_LOCK:
                        row = conn.execute(
                            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE decision = 'BLOCKED'"
                        ).fetchone()
                    prevented = row['total'] if row else 0
                else:
                    prevented = 2800
                self._send_json({"prevented_total": max(2800, prevented), "currency": "USD"})
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
            elif path == '/api/auth/google':
                self._handle_google_auth()
            elif path == '/api/auth/google/callback':
                self._handle_google_callback()
            elif path == '/api/agents':
                self._handle_create_agent()
            elif path == '/api/rules':
                self._handle_create_rule()
            elif path == '/v1/transactions/evaluate':
                self._handle_evaluate()
            elif path == '/api/email-capture':
                self._handle_email_capture()
            elif path == '/api/email-cron':
                self._handle_email_cron()
            elif path == '/api/track':
                self._handle_track()
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
        # Telegram notification (non-blocking, fail-safe)
        try:
            import subprocess as _sp, urllib.request as _ur, urllib.parse as _up
            bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
            if bot_token:
                _tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                _tg_data = _up.urlencode({
                    "chat_id": "369633431",
                    "text": f"🆕 New AgentShield registration: {email}",
                    "parse_mode": "HTML"
                }).encode()
                _req = _ur.Request(_tg_url, data=_tg_data, method="POST")
                _ur.urlopen(_req, timeout=5)
        except Exception:
            pass  # Registration must succeed even if Telegram is down
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

    def _handle_google_auth(self):
        """Initiate Google OAuth flow or return 501 if not configured."""
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
        if not client_id:
            self._send_json({
                "error": "Google OAuth not configured. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.",
                "fallback": "/auth"
            }, 501)
            return
        redirect_uri = f"https://agentshield.fly.dev/api/auth/google/callback"
        scope = "openid email profile"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&redirect_uri={redirect_uri}"
            f"&response_type=code&scope={scope}&prompt=consent"
        )
        self.send_response(302)
        self._send_cors_headers()
        self.send_header('Location', auth_url)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _handle_google_callback(self):
        """Handle Google OAuth callback, exchange code for user info, create/login user."""
        import urllib.request as _ur, urllib.parse as _up
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        code = params.get('code', [None])[0]
        if not code:
            self._send_json({"error": "No authorization code"}, 400)
            return
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
        if not client_id or not client_secret:
            self._send_json({"error": "Google OAuth not configured"}, 501)
            return
        # Exchange code for tokens
        token_data = _up.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": "https://agentshield.fly.dev/api/auth/google/callback",
            "grant_type": "authorization_code"
        }).encode()
        try:
            req = _ur.Request("https://oauth2.googleapis.com/token", data=token_data, method="POST")
            with _ur.urlopen(req, timeout=10) as resp:
                token_resp = json.loads(resp.read())
            access_token = token_resp.get('access_token', '')
            # Get user info
            req2 = _ur.Request("https://www.googleapis.com/oauth2/v2/userinfo",
                               headers={"Authorization": f"Bearer {access_token}"})
            with _ur.urlopen(req2, timeout=10) as resp2:
                userinfo = json.loads(resp2.read())
            google_email = userinfo.get('email', '')
            if not google_email:
                self._send_json({"error": "No email from Google"}, 400)
                return
            # Try to register, if exists login
            account = self.auth.register(google_email, uuid.uuid4().hex)
            if not account:
                # Account exists, login by creating a session directly
                accounts = self.auth.find_by_email(google_email)
                if accounts:
                    account = accounts
                else:
                    self._send_json({"error": "Account lookup failed"}, 500)
                    return
            token = self.store.create_session(account['id'])
            cookie = self._set_session_cookie(token)
            # Telegram notification for new registrations via Google
            try:
                bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
                if bot_token:
                    _tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    _tg_data = _up.urlencode({
                        "chat_id": "369633431",
                        "text": f"🆕 New AgentShield registration (Google): {google_email}"
                    }).encode()
                    _ur.urlopen(_ur.Request(_tg_url, data=_tg_data, method="POST"), timeout=5)
            except Exception:
                pass
            self.send_response(302)
            self._send_cors_headers()
            self.send_header('Set-Cookie', cookie)
            self.send_header('Location', '/dashboard')
            self.send_header('Content-Length', '0')
            self.end_headers()
        except Exception as e:
            self._send_json({"error": f"Google OAuth failed: {str(e)}"}, 500)

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
        # Sanitize name, strip HTML tags to prevent stored XSS
        import html
        name = html.escape(name, quote=True)[:100]
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
        # Validate required params per rule type (prevent silent no-op rules)
        required_params = {
            'transaction_limit': ['max_amount'],
            'daily_total': ['max_daily'],
            'velocity': ['window_minutes', 'max_count'],
            'merchant_allowlist': ['allowed'],
            'category_block': ['blocked'],
            'session_budget': ['max_session'],
            'cascade_cost': ['max_cascade_cost'],
            'hitl_threshold': ['max_budget'],
        }
        if rule_type in required_params:
            params = body.get('params', {})
            missing = [p for p in required_params[rule_type] if p not in params]
            if missing:
                self._send_json({
                    "error": f"Rule type '{rule_type}' requires params: {missing}",
                    "hint": 'Params must be nested: {"params": {"max_amount": 50}}'
                }, 400)
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
        if result['decision'] in ('BLOCKED', 'FLAGGED', 'REVIEW'):
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

    def _send_resend_email(self, to_email, subject, html_body):
        """Send email via Resend API using stdlib urllib."""
        api_key = os.getenv('RESEND_API_KEY', '')
        if not api_key:
            return False
        import urllib.request as _ur, urllib.error as _ue
        data = json.dumps({
            "from": "AgentShield <noreply@sipiteno.com>",
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }).encode('utf-8')
        req = _ur.Request('https://api.resend.com/emails', data=data,
                         headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json',
                                  'User-Agent': 'AgentShield/1.0'},
                         method='POST')
        try:
            with _ur.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _get_email_bodies(self):
        """Return dict of step -> (subject, html_body) for email sequence."""
        return {
            'soap_day1': ("I lost $2,800 while I was sleeping", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><h1 style="color:#ff4757">I lost $2,800 while I was sleeping</h1><p>At 3:14 AM, my phone buzzed. An email from my API provider.</p><p><strong>$2,793.00. In one hour. While I was asleep.</strong></p><p>An AI agent I deployed had entered a retry loop. Each retry cost $133. It retried 21 times before the budget alert even arrived.</p><p>The alert came at 3:14 AM. I read it at 6:17 AM. Three hours too late.</p><p>Every tool I had was reactive. Rate limits protect the provider. Budget alerts arrive by email. Dashboards show what happened after the money is gone.</p><p>Tomorrow I will show you what I built to stop this from ever happening again.</p><p>, Maryan K.<br>AgentShield<br><a href="https://agentshield.fly.dev">https://agentshield.fly.dev</a></p></body></html>'),
            'soap_day2': ("What if your agent asked permission before spending?", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><h2>Yesterday I told you about losing $2,800 in 60 seconds.</h2><p>Heres what I built: a per-transaction firewall that sits between your agent and the API. Every call is evaluated against rules you set BEFORE it executes.</p><p>Transaction over $500? Blocked. Daily spend over $2,000? Blocked. More than 10 calls in an hour? Flagged.</p><p>The evaluation takes less than 1ms. Pure Python stdlib. Zero dependencies.</p><p>If Id had this running that night, the second call would have been blocked at $266. Not $2,793.</p><p>Tomorrow: the two rules that came from production feedback at HeartFlow.</p><p>, Maryan K.<br>AgentShield</p></body></html>'),
            'soap_day3': ("The rule that catches what daily budgets miss", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><h2>The rule that catches what daily budgets miss</h2><p>session_budget catches the 2 AM cron burst where one session eats the whole day budget. Session-scoped budgets with decay tightening fix this.</p><p>And cascade_cost: a $0.50 call with 30% failure rate and $5 retry = $2 expected cost. Blocks calls that look cheap but compound on failure.</p><p>Tomorrow: the 77-scenario eval gym.</p><p>, Maryan K.<br>AgentShield</p></body></html>'),
            'soap_day4': ("77 test scenarios that prove your spend control works", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><h2>77 test scenarios that prove your spend control works</h2><p>You cant claim spend control without test cases. So I wrote 77 of them.</p><p>The Eval Gym covers clean approvals, transaction limits, daily totals, velocity, allowlists, category blocks, session budgets, cascade costs, and edge cases.</p><p>All MIT licensed: https://agentshield.fly.dev/eval</p><p>Tomorrow: how to get started in 60 seconds.</p><p>, Maryan K.<br>AgentShield</p></body></html>'),
            'soap_day5': ("Your agents are running right now. Do they have a firewall?", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><h2>Your agents are running right now</h2><p>Free options: pip install agentshield, risk calculator, eval gym.</p><p>Paid options: $299 Professional Audit, $19/mo Managed.</p><p>The question isnt whether you need spend control. Its whether you set it up before or after your first incident.</p><p>I wish I had done it before.</p><p>, Maryan K.<br>AgentShield</p></body></html>'),
            'seinfeld_1': ("The cheapest API call that cost $2,800", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><p>Each individual API call was only $133. Thats less than a coffee subscription. But 21 of them in 60 seconds? Thats $2,793.</p><p>The lesson: its not the individual call cost that kills you. Its the loop. The retry. The accumulation.</p><p>AgentShield blocks the second call. Not the 21st.</p><p>, Maryan K.</p></body></html>'),
            'seinfeld_2': ("Why your rate limit is a speed bump, not a firewall", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><p>Rate limits cap requests per second. They dont cap dollars.</p><p>Your provider is happy to let you make 100 calls at $133 each. They get paid either way.</p><p>AgentShield caps dollars. Thats the difference.</p><p>, Maryan K.</p></body></html>'),
            'seinfeld_3': ("The 3 AM test: would your agent survive it?", '<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a"><p>If your agent ran unattended from midnight to 6 AM, what would your bill look like?</p><p>Thats the 3 AM test. If you dont know the answer, you need AgentShield.</p><p>Risk calculator: https://agentshield.fly.dev/tools/risk-calculator/</p><p>, Maryan K.</p></body></html>'),
        }

    def _handle_email_capture(self):
        body = self._read_body()
        email = body.get('email', '').strip()
        source = body.get('source', 'landing')
        if not email or '@' not in email:
            self._send_json({"error": "Valid email required"}, 400)
            return
        capture_id = self.store.capture_email(email, source)
        # Send Soap Opera Day 1 immediately
        bodies = self._get_email_bodies()
        day1 = bodies.get('soap_day1', ('', ''))
        sent = self._send_resend_email(email, day1[0], day1[1])
        # Schedule remaining emails
        try:
            import time as _time
            now = _time.time()
            day = 86400
            steps = [
                ('soap_day2', now + day),
                ('soap_day3', now + day*2),
                ('soap_day4', now + day*3),
                ('soap_day5', now + day*4),
                ('seinfeld_1', now + day*7),
                ('seinfeld_2', now + day*10),
                ('seinfeld_3', now + day*14),
            ]
            conn = self.store._get_conn()
            for step, send_at in steps:
                conn.execute(
                    "INSERT OR IGNORE INTO email_sequence (email, capture_id, step, send_at, sent) VALUES (?,?,?,?,0)",
                    (email, capture_id, step, send_at)
                )
            conn.commit()
        except Exception:
            pass  # Email capture must succeed even if scheduling fails
        self._send_json({"success": True, "id": capture_id, "email_sent": sent}, 201)

    def _handle_email_cron(self):
        """Daily email sequence sender. Protected by CRON_SECRET."""
        cron_secret = os.getenv('CRON_SECRET', 'changeme')
        auth = self.headers.get('X-Cron-Secret', '')
        if auth != cron_secret:
            self._send_json({"error": "Unauthorized"}, 403)
            return
        import time as _time
        now = _time.time()
        conn = self.store._get_conn()
        rows = conn.execute(
            "SELECT id, email, step FROM email_sequence WHERE sent = 0 AND send_at <= ? ORDER BY send_at LIMIT 50",
            (now,)
        ).fetchall()
        bodies = self._get_email_bodies()
        sent_count = 0
        for row in rows:
            eid, email, step = row
            entry = bodies.get(step, None)
            if entry:
                ok = self._send_resend_email(email, entry[0], entry[1])
                if ok:
                    conn.execute("UPDATE email_sequence SET sent = 1 WHERE id = ?", (eid,))
                    sent_count += 1
        conn.commit()
        self._send_json({"sent": sent_count, "checked": len(rows)}, 200)

    # ─── Analytics Tracking ───────────────────────────────────────────────

    def _handle_track(self):
        """Lightweight event tracking, appends to a JSONL file. No PII."""
        import json as _json
        import time as _time
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length).decode('utf-8', errors='replace') if length else '{}'
            event = _json.loads(raw) if raw.strip() else {}
        except Exception:
            event = {}
        record = {
            'e': str(event.get('e', 'unknown'))[:50],
            'p': str(event.get('p', ''))[:100],
            'r': str(event.get('r', ''))[:100],
            'ts': _time.time()
        }
        try:
            with open('/data/analytics.jsonl', 'a') as f:
                f.write(_json.dumps(record) + '\n')
        except OSError:
            # Fallback for local dev without /data volume
            try:
                with open('analytics.jsonl', 'a') as f:
                    f.write(_json.dumps(record) + '\n')
            except OSError:
                pass
        self._send_json({"ok": True}, 200)

    # ─── Billing (Stripe) ─────────────────────────────────────────────────

    def _handle_billing_checkout(self):
        """Create a Stripe Checkout Session and redirect the user."""
        # Read session cookie inline (not via _get_session_account) so we
        # can send a friendly redirect hint instead of bare "Unauthorized"
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
        if not token:
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        if not token:
            self._send_json({"error": "Please log in to continue", "redirect": "/auth?next=checkout"}, 401)
            return
        account = self.auth.account_from_token(token)
        if not account:
            self._send_json({"error": "Please log in to continue", "redirect": "/auth?next=checkout"}, 401)
            return
        body = self._read_body()
        tier = body.get('tier')
        price_map = {
            'dev': os.getenv('STRIPE_PRICE_DEV'),
            'team': os.getenv('STRIPE_PRICE_TEAM'),
            'managed': os.getenv('STRIPE_PRICE_MANAGED'),
            'tripwire': os.getenv('STRIPE_PRICE_TRIPWIRE'),
            'bump': os.getenv('STRIPE_PRICE_BUMP'),
            'audit': os.getenv('STRIPE_PRICE_AUDIT', os.getenv('STRIPE_PRICE_DEV')),
        }
        price_id = price_map.get(tier)
        if not price_id:
            self._send_json({"error": "Invalid tier or Stripe not configured"}, 400)
            return

        stripe_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe_key:
            self._send_json({"error": "Stripe not configured"}, 500)
            return

        # Create a Stripe Checkout Session using urllib (stdlib)
        import urllib.request
        import urllib.error
        import urllib.parse
        import base64

        is_one_time = tier in ('tripwire', 'bump')
        checkout_mode = 'payment' if is_one_time else 'subscription'
        checkout_data = urllib.parse.urlencode({
            'mode': checkout_mode,
            'line_items[0][price]': price_id,
            'line_items[0][quantity]': '1',
            'success_url': f"https://agentshield.fly.dev/dashboard?upgrade=success&tier={tier}",
            'cancel_url': 'https://agentshield.fly.dev/dashboard?upgrade=cancelled',
            'client_reference_id': account['id'],
            'metadata[tier]': tier,
            'metadata[account_id]': account['id'],
        }).encode()

        req = urllib.request.Request(
            'https://api.stripe.com/v1/checkout/sessions',
            data=checkout_data,
            headers={
                'Authorization': 'Basic ' + base64.b64encode(f'{stripe_key}:'.encode()).decode(),
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                session_data = json.loads(resp.read().decode())
            checkout_url = session_data.get('url')
            if checkout_url:
                self._send_json({"url": checkout_url, "session_id": session_data.get('id', '')}, 200)
            else:
                self._send_json({"error": "Failed to create checkout session"}, 500)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                error_data = json.loads(error_body)
                self._send_json({"error": error_data.get('error', {}).get('message', 'Stripe error')}, e.code)
            except json.JSONDecodeError:
                self._send_json({"error": f"Stripe API error: {e.code}"}, e.code)
        except Exception as e:
            self._send_json({"error": f"Checkout failed: {str(e)}"}, 500)

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
                md_content = f.read()
            # Wrap in SEO-optimized HTML with Open Graph tags and JSON-LD schema
            import html as html_module
            title = "At 3 AM, My AI Agent Spent $2,800 in 60 Seconds, Here's What I Built"
            description = "How I built AgentShield: a Python stdlib-only firewall for AI agent spending. Composable spend rules evaluated per-transaction in under 1ms. 77/77 eval gym."
            url = "https://agentshield.fly.dev/blog"
            
            # Simple markdown to HTML conversion for body
            body_html = html_module.escape(md_content)
            body_html = body_html.replace('**', '<strong>', 1)  # Fallback if markdown
            
            # Build full SEO HTML
            seo_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<!-- Open Graph -->
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="AgentShield">
<meta property="article:published_time" content="2026-08-11T00:00:00Z">
<meta property="article:author" content="Sipiteno">
<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<!-- Article JSON-LD -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{description}",
  "author": {{
    "@type": "Organization",
    "name": "AgentShield"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "AgentShield",
    "url": "https://agentshield.fly.dev"
  }},
  "datePublished": "2026-08-11",
  "mainEntityOfPage": "{url}"
}}
</script>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif; background: #0a0a0a; color: #e8e8e8; max-width: 800px; margin: 0 auto; padding: 40px 24px; line-height: 1.7; }}
h1, h2, h3 {{ color: #00d4aa; margin-top: 1.5em; }}
h1 {{ font-size: 1.8em; }}
code {{ background: #1a1a1a; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
pre {{ background: #141414; padding: 16px; border-radius: 8px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
a {{ color: #00d4aa; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #2a2a2a; padding: 8px; text-align: left; }}
th {{ background: #141414; }}
blockquote {{ border-left: 3px solid #00d4aa; padding-left: 16px; color: #888; }}
</style>
</head>
<body>
<pre style="background:none;padding:0;white-space:pre-wrap;font-family:inherit;font-size:inherit;overflow-wrap:break-word">{html_module.escape(md_content)}</pre>
<p style="margin-top:40px;border-top:1px solid #2a2a2a;padding-top:20px">
<a href="/">← Back to AgentShield</a> · 
<a href="/tools/risk-calculator/">Try the Risk Calculator</a> · 
<a href="/dashboard">Dashboard</a>
</p>
</body>
</html>"""
            self._send_html(seo_html)
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
            # Try package import first, then tests fallback
            try:
                from agentshield import run_eval
            except ImportError:
                from tests.eval_gym import run_eval
            results = run_eval()
            self._send_json(results)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
