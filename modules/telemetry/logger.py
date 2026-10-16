from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TelemetryLogger:
    enabled: bool = True
    logs: list[dict] = field(default_factory=list)

    def log(self, event: str, payload: dict) -> None:
        if self.enabled:
            self.logs.append({"event": event, "payload": payload})
