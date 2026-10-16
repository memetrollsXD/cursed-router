from __future__ import annotations

from typing import Any

from mitmproxy import http

from modules.gating import client_ip


class ClientTrackerAddon:
    """Registers every client seen in traffic so the dashboard can list and target them."""

    def __init__(self, runtime: Any | None = None):
        self.runtime = runtime

    def request(self, flow: http.HTTPFlow) -> None:
        if self.runtime is None:
            return
        ip = client_ip(flow)
        if ip is None:
            return
        self.runtime.register_client(ip, flow.request.headers.get("User-Agent"))
