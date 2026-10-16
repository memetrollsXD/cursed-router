from __future__ import annotations

from dataclasses import dataclass

from app.config import RouterConfig


@dataclass
class HostapdManager:
    config: RouterConfig
    running: bool = False

    def render_config(self) -> str:
        return "\n".join(
            [
                f"interface={self.config.interface}",
                f"ssid={self.config.ssid}",
                f"channel={self.config.channel}",
            ]
        )

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False
