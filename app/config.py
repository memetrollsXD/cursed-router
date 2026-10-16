from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional dependency for non-venv startup
    yaml = None


@dataclass
class RouterConfig:
    """Runtime configuration for the router's MITM and portal behavior."""

    portal_host: str = "10.67.67.67"
    portal_port: int = 8081
    dns_server: str = "10.67.67.67"
    mutators_enabled: bool = True
    rules_path: str = "rules/default.yaml"
    redirects: dict[str, str] = field(default_factory=dict)
    rules: dict[str, bool] = field(default_factory=dict)
    magic_passwords: list[str] = field(default_factory=lambda: ["banana", "echo", "penguin", "toaster"])

    @classmethod
    def from_file(cls, path: str | Path) -> "RouterConfig":
        config_path = Path(path)
        if not config_path.exists() or yaml is None:
            return cls()

        with config_path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}

        redirects = loaded.get("redirects", {}) or {}
        rules = loaded.get("rules", {}) or {}
        magic_passwords = loaded.get("magic_passwords", []) or []
        mutators_enabled = bool(loaded.get("mutators_enabled", True))

        rules = {str(name): bool(enabled) for name, enabled in rules.items()}
        rules.setdefault("mutators", mutators_enabled)

        return cls(
            portal_host=loaded.get("portal_host", "10.67.67.67"),
            portal_port=int(loaded.get("portal_port", 8081)),
            dns_server=loaded.get("dns_server", "10.67.67.67"),
            mutators_enabled=mutators_enabled,
            rules_path=str(config_path),
            redirects={str(k): str(v) for k, v in redirects.items()},
            rules=rules,
            magic_passwords=[str(item) for item in magic_passwords],
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "portal_host": self.portal_host,
            "portal_port": self.portal_port,
            "dns_server": self.dns_server,
            "mutators_enabled": self.mutators_enabled,
            "redirects": self.redirects,
            "rules": self.rules,
            "magic_passwords": self.magic_passwords,
        }
