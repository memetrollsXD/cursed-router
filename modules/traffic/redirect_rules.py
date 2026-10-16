from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RedirectRules:
    redirects: dict[str, str] = field(default_factory=dict)

    def add(self, source: str, target: str) -> None:
        self.redirects[source] = target

    def resolve(self, source: str) -> str | None:
        return self.redirects.get(source)
