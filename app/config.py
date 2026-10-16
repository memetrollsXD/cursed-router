from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RouterConfig:
    ssid: str = "CursedRouter"
    interface: str = "wlan0"
    channel: int = 6
    rules_file: Path = Path("rules/default.yaml")
    theme_file: Path = Path("rules/themes.yaml")
    telemetry_enabled: bool = True
    magic_mode: str = "magic-passwords"
    admin_bind: str = "127.0.0.1:8080"
    metadata: dict[str, str] = field(default_factory=dict)
