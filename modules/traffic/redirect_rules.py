from __future__ import annotations

from mitmproxy import http


class RedirectRuleAddon:
    """Simple host-based redirect engine for local-only prank traffic."""

    def __init__(self, redirects: dict[str, str] | None = None):
        self.redirects = redirects or {
            "google.com": "http://127.0.0.1:8081/",
            "github.com": "http://127.0.0.1:8081/",
            "example.com": "http://127.0.0.1:8081/",
            "adminpanel.com": "http://127.0.0.1:8081/",
            "10.67.67.67": "http://127.0.0.1:8081/",
        }

    def request(self, flow: http.HTTPFlow) -> None:
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
