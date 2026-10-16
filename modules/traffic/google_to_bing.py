from __future__ import annotations

from mitmproxy import http


class GoogleToBingAddon:
    """Test addon: redirect Google traffic to Bing for a quick local demo."""

    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.host.lower()
        if host not in {"google.com", "www.google.com"}:
            return

        flow.request.scheme = "https"
        flow.request.host = "www.bing.com"
        flow.request.port = 443
        flow.request.path = "/"
        flow.request.headers["Host"] = "www.bing.com"
