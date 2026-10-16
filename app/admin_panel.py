"""Admin panel for the Cursed Router prank appliance.

Part of a local-only, consensual "useless projects" hackathon build. Serves a
dashboard and obviously-theatrical portal pages on the lab network and toggles
prank "modes". It stores no client credentials or browsing contents and sends
nothing off the local machine. See README.md "Scope & authorization".
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from app.dashboard_view import render_dashboard
from app.runtime import RuntimeState


class AdminPanelHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/portal/adminpanel"}:
            self._send_html(self._render_dashboard())
            return

        if self.path in {"/portal/google", "/portal/github", "/portal/youtube"}:
            self._send_html(f"<html><body><h1>Router prank page</h1><p>This page has been cursed by the router.</p></body></html>")
            return

        if self.path == "/api/state":
            payload = json.dumps(self.server.runtime.as_dict()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        if self.path == "/api/rule":
            self._handle_rule(data)
            return

        client_ip = data.get("client_ip")
        mode = data.get("mode")
        if not client_ip or not mode:
            self.send_error(400, "client_ip and mode are required")
            return

        self.server.runtime.set_mode(client_ip, mode)
        self._send_json({"status": "ok", "client_ip": client_ip, "mode": mode})

    def _handle_rule(self, data: dict[str, Any]) -> None:
        rule = data.get("rule")
        if not rule or "enabled" not in data:
            self.send_error(400, "rule and enabled are required")
            return

        client_ip = data.get("client_ip") or None
        enabled = bool(data.get("enabled"))
        self.server.runtime.set_rule(client_ip, rule, enabled)
        self._send_json({"status": "ok", "client_ip": client_ip or "*", "rule": rule, "enabled": enabled})

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _render_dashboard(self) -> str:
        return render_dashboard()


class AdminPanelServer(HTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_class: type[BaseHTTPRequestHandler], runtime: RuntimeState):
        super().__init__(server_address, handler_class)
        self.runtime = runtime


def start_admin_panel(runtime: RuntimeState, host: str = "0.0.0.0", port: int = 8081) -> AdminPanelServer:
    server = AdminPanelServer((host, port), AdminPanelHandler, runtime)
    return server


class AdminPanelAddon:
    """Serves the admin panel from inside the mitmdump process so it shares the proxy's runtime state."""

    def __init__(self, runtime: RuntimeState, host: str = "0.0.0.0", port: int = 8081):
        self.runtime = runtime
        self.host = host
        self.port = port
        self.server: AdminPanelServer | None = None

    def running(self) -> None:
        self.server = start_admin_panel(self.runtime, self.host, self.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        print(f"Admin panel listening on http://{self.host}:{self.port}")

    def done(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
