from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetricsTracker:
    counters: dict[str, int] = field(default_factory=dict)

    def increment(self, key: str, amount: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + amount

    def get(self, key: str) -> int:
        return self.counters.get(key, 0)
