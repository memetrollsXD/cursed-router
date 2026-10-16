from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EventBus:
    events: list[str] = field(default_factory=list)

    def publish(self, event_name: str) -> None:
        self.events.append(event_name)
