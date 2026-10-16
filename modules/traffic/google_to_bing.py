"""Demo redirect addon for the Cursed Router prank appliance.

Part of a local-only, consensual "useless projects" hackathon build: a gag that
bounces google.com to bing.com on a lab network whose users are in on the joke.
It captures no credentials and exfiltrates nothing. See README.md "Scope & authorization".
"""
from __future__ import annotations

from typing import Any

from mitmproxy import http

from modules.gating import rule_enabled

RULE = "google_to_bing"


class GoogleToBingAddon:
    """Test addon: redirect Google traffic to Bing for a quick local demo."""

    def __init__(self, runtime: Any | None = None):
        self.runtime = runtime

    def request(self, flow: http.HTTPFlow) -> None:
        if not rule_enabled(self.runtime, flow, RULE):
            return

        host = flow.request.host.lower()
        if host not in {"google.com", "www.google.com"}:
            return

        flow.request.scheme = "https"
        flow.request.host = "www.bing.com"
        flow.request.port = 443
        flow.request.path = "/"
        flow.request.headers["Host"] = "www.bing.com"
