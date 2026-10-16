from __future__ import annotations

from app.config import RouterConfig
from modules.admin.dashboard import AdminDashboard
from modules.auth.auth_manager import AuthManager
from modules.portal.portal_server import PortalServer
from modules.portal.rules import RuleEngine
from modules.telemetry.events import EventBus
from modules.telemetry.logger import TelemetryLogger
from modules.telemetry.metrics import MetricsTracker
from modules.traffic.dns_overrides import DNSOverrides
from modules.wifi.hostapd_manager import HostapdManager


class CursedRouterApp:
    def __init__(self, config: RouterConfig | None = None) -> None:
        self.config = config or RouterConfig()
        self.event_bus = EventBus()
        self.logger = TelemetryLogger(enabled=self.config.telemetry_enabled)
        self.metrics = MetricsTracker()
        self.wifi = HostapdManager(self.config)
        self.auth = AuthManager(mode=self.config.magic_mode)
        self.rules = RuleEngine.from_yaml(self.config.rules_file)
        self.portal = PortalServer(self.rules)
        self.dns = DNSOverrides(default_target="internet-is-fine.local")
        self.dashboard = AdminDashboard()

    def run_once(self) -> dict[str, str | bool | int]:
        self.wifi.start()
        self.event_bus.publish("router.started")
        self.logger.log("router.started", {"ssid": self.config.ssid})
        self.metrics.increment("runs")
        return {
            "ssid": self.config.ssid,
            "wifi_running": self.wifi.running,
            "rules_loaded": self.rules.rule_count,
            "telemetry_enabled": self.config.telemetry_enabled,
        }


def main() -> int:
    app = CursedRouterApp()
    app.run_once()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
