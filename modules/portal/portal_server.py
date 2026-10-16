from __future__ import annotations

from dataclasses import dataclass

from modules.portal.rules import RuleEngine


@dataclass
class PortalServer:
    rules: RuleEngine

    def splash(self, client_id: str) -> str:
        matched = self.rules.match(client_id=client_id, domain="portal")
        if matched and matched.get("action") == "cat-portal":
            return "Welcome to Cat Portal"
        return "Welcome to Cursed Router"
