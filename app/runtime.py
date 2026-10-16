from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClientSession:
    ip: str
    mode: str = "default"
    portal_seen: bool = False
    user_agent: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class RuntimeState:
    clients: dict[str, ClientSession] = field(default_factory=dict)
    active_modes: dict[str, str] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

    def get_client(self, ip: str) -> ClientSession:
        if ip not in self.clients:
            self.clients[ip] = ClientSession(ip=ip)
        return self.clients[ip]

    def log(self, message: str) -> None:
        self.logs.append(message)

    def set_mode(self, ip: str, mode: str) -> None:
        self.active_modes[ip] = mode
        client = self.get_client(ip)
        client.mode = mode
        client.notes.append(f"mode={mode}")
        self.log(f"Client {ip} switched to mode '{mode}'")

    def as_dict(self) -> dict[str, Any]:
        return {
            "clients": {ip: {"mode": client.mode, "portal_seen": client.portal_seen} for ip, client in self.clients.items()},
            "active_modes": self.active_modes,
            "logs": self.logs,
        }
