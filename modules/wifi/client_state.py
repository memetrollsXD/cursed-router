from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClientState:
    connected_clients: set[str] = field(default_factory=set)

    def connect(self, client_id: str) -> None:
        self.connected_clients.add(client_id)

    def disconnect(self, client_id: str) -> None:
        self.connected_clients.discard(client_id)

    def is_connected(self, client_id: str) -> bool:
        return client_id in self.connected_clients
