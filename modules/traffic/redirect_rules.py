from __future__ import annotations

from typing import Any

from mitmproxy import http

from modules.gating import rule_enabled

RULE = "redirects"


class RedirectRuleAddon:
    """Simple host-based redirect engine for local-only prank traffic."""

    def __init__(self, redirects: dict[str, str] | None = None, runtime: Any | None = None):
        self.runtime = runtime
        self.redirects = redirects or {
            "google.com": "http://10.67.67.67:8081/",
            "github.com": "http://10.67.67.67:8081/",
            "example.com": "http://10.67.67.67:8081/",
            "adminpanel.com": "http://10.67.67.67:8081/",
            "10.67.67.67": "http://10.67.67.67:8081/",
        }

    def request(self, flow: http.HTTPFlow) -> None:
        if not rule_enabled(self.runtime, flow, RULE):
            return

        host = flow.request.host.lower()
        target = self.redirects.get(host)
        if not target:
            return

        flow.response = http.Response.make(
            302,
            b"",
            {
                "Location": target,
                "Content-Type": "text/plain; charset=utf-8",
                "Cache-Control": "no-store",
            },
        )
