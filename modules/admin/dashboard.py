from __future__ import annotations

from typing import Any


class AdminDashboardAddon:
    """Minimal runtime admin interface to toggle per-client behaviour."""

    def __init__(self, runtime: Any | None = None):
        self.runtime = runtime

    def set_runtime(self, runtime: Any) -> None:
        self.runtime = runtime

    def apply_mode(self, client_ip: str, mode: str) -> str:
        if self.runtime is not None:
            self.runtime.set_mode(client_ip, mode)
        return f"Applied mode '{mode}' to {client_ip}"
