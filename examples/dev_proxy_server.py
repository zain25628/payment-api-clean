#!/usr/bin/env python3
"""
Dev proxy for provider-buttons-example.html

This simple proxy server forwards requests from the HTML example to the backend API,
adding CORS headers to bypass browser security restrictions during local development.

Usage:
  1) python dev_proxy_server.py
  2) In provider-buttons-example.html set Base URL to: http://localhost:5050
  3) Buttons will call /wallets/request/... through this proxy, bypassing CORS.

Note: This is for development only. In production, configure proper CORS on the backend
      or serve the HTML from the same origin as the API.
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.error

TARGET_BASE = "http://127.0.0.1:8000"
PORT = 5051


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def _set_cors(self):
        """Add CORS headers (development only)."""
        self.send_header("Access-Control-Allow-Origin", "*")  # dev only
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        """Forward POST requests to the backend API."""
        # Only forward requests starting with /wallets/
        if not self.path.startswith("/wallets/"):
            self.send_response(404)
            self._set_cors()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not found - this proxy only handles /wallets/* endpoints")
            return

        # Read request body
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else b"{}"
        api_key = self.headers.get("X-API-Key", "")

        # Forward to backend
        upstream_url = f"{TARGET_BASE}{self.path}"
        req = urllib.request.Request(
            upstream_url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
        )

        try:
            with urllib.request.urlopen(req) as resp:
                upstream_body = resp.read()
                status = resp.getcode()
                content_type = resp.headers.get(
                    "Content-Type", "application/json"
                )
        except urllib.error.HTTPError as e:
            upstream_body = e.read()
            status = e.code
            content_type = e.headers.get("Content-Type", "application/json")
        except Exception as e:
            self.send_response(500)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": "proxy_failed", "detail": str(e)}).encode("utf-8")
            )
            return

        # Send response back to browser
        self.send_response(status)
        self._set_cors()
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(upstream_body)

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[PROXY] {args[0]} - {args[1]}")


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print("=" * 60)
        print(f"Dev Proxy Server Started")
        print(f"Listening on: http://localhost:{PORT}")
        print(f"Forwarding to: {TARGET_BASE}")
        print("=" * 60)
        print(f"\nTo use with provider-buttons-example.html:")
        print(f"  1. Set Base URL to: http://localhost:{PORT}")
        print(f"  2. Click any payment button")
        print(f"  3. Requests will be proxied to the backend API\n")
        print("Press Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nProxy server stopped.")
