from __future__ import annotations

import json
from typing import Any

from mitmproxy import http

from app.dashboard_view import render_dashboard

DEFAULT_HOSTS = ("admin.com", "adminpanel.com")


class AdminHostAddon:
    """Serves the live dashboard and its API directly on the admin host.

    A plain redirect would bounce clients to the panel's raw IP:port and lose the
    admin.com address bar. Answering in the proxy keeps the dashboard running on
    admin.com itself, sharing the same RuntimeState the panel mutates.
    """

    def __init__(self, runtime: Any, hosts: tuple[str, ...] = DEFAULT_HOSTS):
        self.runtime = runtime
        self.hosts = tuple(h.lower() for h in hosts)

    def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.host.lower() not in self.hosts:
            return

        path = flow.request.path.split("?", 1)[0]

        if flow.request.method == "GET" and path in {"/", "/portal/adminpanel"}:
            flow.response = _html(render_dashboard())
            return

        if flow.request.method == "GET" and path == "/api/state":
            flow.response = _json(self.runtime.as_dict())
            return

        if flow.request.method == "POST" and path in {"/api/rule", "/api/mode", "/"}:
            flow.response = self._handle_post(path, flow.request.content or b"")
            return

        flow.response = http.Response.make(404, b"Not found", {"Content-Type": "text/plain"})

    def _handle_post(self, path: str, body: bytes) -> http.Response:
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json({"error": "invalid JSON"}, status=400)

        if path == "/api/rule":
            rule = data.get("rule")
            if not rule or "enabled" not in data:
                return _json({"error": "rule and enabled are required"}, status=400)
            client_ip = data.get("client_ip") or None
            enabled = bool(data.get("enabled"))
            self.runtime.set_rule(client_ip, rule, enabled)
            return _json({"status": "ok", "client_ip": client_ip or "*", "rule": rule, "enabled": enabled})

        client_ip = data.get("client_ip")
        mode = data.get("mode")
        if not client_ip or not mode:
            return _json({"error": "client_ip and mode are required"}, status=400)
        self.runtime.set_mode(client_ip, mode)
        return _json({"status": "ok", "client_ip": client_ip, "mode": mode})


def _html(markup: str) -> http.Response:
    return http.Response.make(
        200,
        markup.encode("utf-8"),
        {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"},
    )


def _json(payload: dict[str, Any], status: int = 200) -> http.Response:
    return http.Response.make(
        status,
        json.dumps(payload).encode("utf-8"),
        {"Content-Type": "application/json", "Cache-Control": "no-store"},
    )
