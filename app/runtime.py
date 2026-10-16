from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

GLOBAL_SCOPE = "*"


@dataclass
class ClientSession:
    ip: str
    mode: str = "default"
    portal_seen: bool = False
    user_agent: str | None = None
    rules: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class RuntimeState:
    clients: dict[str, ClientSession] = field(default_factory=dict)
    active_modes: dict[str, str] = field(default_factory=dict)
    rules: dict[str, bool] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

    def get_client(self, ip: str) -> ClientSession:
        if ip not in self.clients:
            self.clients[ip] = ClientSession(ip=ip)
        return self.clients[ip]

    def register_client(self, ip: str, user_agent: str | None = None) -> ClientSession:
        client = self.get_client(ip)
        if user_agent:
            client.user_agent = user_agent
        return client

    def log(self, message: str) -> None:
        self.logs.append(message)

    def set_mode(self, ip: str, mode: str) -> None:
        self.active_modes[ip] = mode
        client = self.get_client(ip)
        client.mode = mode
        client.notes.append(f"mode={mode}")
        self.log(f"Client {ip} switched to mode '{mode}'")

    def is_rule_enabled(self, ip: str, rule: str) -> bool:
        client = self.clients.get(ip)
        if client is not None and rule in client.rules:
            return client.rules[rule]
        return self.rules.get(rule, True)

    def set_rule(self, ip: str | None, rule: str, enabled: bool) -> None:
        if ip in (None, GLOBAL_SCOPE):
            self.rules[rule] = enabled
            self.log(f"Rule '{rule}' default set to {'on' if enabled else 'off'}")
            return
        client = self.get_client(ip)
        client.rules[rule] = enabled
        self.log(f"Client {ip} rule '{rule}' set to {'on' if enabled else 'off'}")

    def effective_rules(self, ip: str) -> dict[str, bool]:
        return {rule: self.is_rule_enabled(ip, rule) for rule in self.rules}

    def as_dict(self) -> dict[str, Any]:
        return {
            "clients": {
                ip: {
                    "mode": client.mode,
                    "portal_seen": client.portal_seen,
                    "user_agent": client.user_agent,
                    "rules": self.effective_rules(ip),
                }
                for ip, client in self.clients.items()
            },
            "active_modes": self.active_modes,
            "rules": self.rules,
            "logs": self.logs,
        }
