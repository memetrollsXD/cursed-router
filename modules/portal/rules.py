from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class RuleEngine:
    rules: list[dict]

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RuleEngine":
        loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        rules = loaded.get("rules", [])
        return cls(rules=rules)

    def match(self, client_id: str, domain: str) -> dict | None:
        for rule in self.rules:
            if rule.get("client") in (None, client_id) and rule.get("domain") in (None, domain):
                return rule
        return None
