import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.api import APIHandler, ThreadedHTTPServer


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ConsolidationRedirectTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadedHTTPServer(("127.0.0.1", 0), APIHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.opener = urllib.request.build_opener(_NoRedirect)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _response(self, path, method="GET", body=None):
        data = json.dumps(body or {}).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        try:
            return self.opener.open(request, timeout=5)
        except urllib.error.HTTPError as error:
            return error

    def test_legacy_marketing_routes_move_permanently_to_sipibot_pilot(self):
        for path in ("/", "/audit", "/pilot", "/tripwire"):
            with self.subTest(path=path):
                response = self._response(path)
                self.assertEqual(response.code, 301)
                self.assertEqual(
                    response.headers["Location"],
                    "https://sipi.bot/pilot?source=agentshield",
                )
                response.close()

    def test_health_reports_the_canonical_product(self):
        response = self._response("/health")
        self.assertEqual(response.code, 200)
        payload = json.load(response)
        self.assertTrue(payload["migrated"])
        self.assertEqual(payload["canonical"], "https://sipi.bot")
        response.close()

    def test_legacy_evaluate_post_preserves_method_to_canonical_api(self):
        response = self._response(
            "/v1/transactions/evaluate",
            method="POST",
            body={"amount": 10, "merchant": "example.com"},
        )
        self.assertEqual(response.code, 308)
        self.assertEqual(
            response.headers["Location"],
            "https://sipi.bot/v1/transactions/evaluate",
        )
        response.close()


if __name__ == "__main__":
    unittest.main()
