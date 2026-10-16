from __future__ import annotations

from mitmproxy import http


class RedirectRuleAddon:
    """Simple host-based redirect engine for local-only prank traffic."""

    def __init__(self, redirects: dict[str, str] | None = None):
        self.redirects = redirects or {
            "google.com": "http://10.0.0.1:8081/portal/google",
            "github.com": "http://10.0.0.1:8081/portal/github",
            "example.com": "http://10.0.0.1:8081/portal/example",
        }

    def request(self, flow: http.HTTPFlow) -> None:
        target = self.redirects.get(flow.request.host.lower())
        if not target:
            return

        flow.response = http.Response.make(
            302,
            b"",
            {
                "Location": target,
                "Content-Type": "text/plain; charset=utf-8",
            },
        )
