from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DNSOverrides:
    default_target: str
    map: dict[str, str] = field(default_factory=lambda: {
        "google.com": "very-legal-search.example",
        "github.com": "the-future-of-coding.example",
        "youtube.com": "this-is-not-a-video.example",
    })

    def resolve(self, domain: str) -> str:
        return self.map.get(domain, self.default_target)
