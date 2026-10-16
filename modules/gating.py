from __future__ import annotations

from typing import Any

from mitmproxy import http


def client_ip(flow: http.HTTPFlow) -> str | None:
    peer = getattr(flow.client_conn, "peername", None)
    if peer:
        return peer[0]
    return None


def rule_enabled(runtime: Any | None, flow: http.HTTPFlow, rule: str) -> bool:
    """A missing runtime or unknown client leaves the addon fully enabled."""
    if runtime is None:
        return True
    ip = client_ip(flow)
    if ip is None:
        return True
    return runtime.is_rule_enabled(ip, rule)
