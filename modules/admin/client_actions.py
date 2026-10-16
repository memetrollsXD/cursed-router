from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClientAction:
    client_id: str
    action: str
    payload: dict | None = None
