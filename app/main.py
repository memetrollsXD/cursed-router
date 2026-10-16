"""Cursed Router — mitmproxy addon entry point.

SCOPE & AUTHORIZATION: local-only, lab-network prank appliance for a "useless projects"
hackathon. Run only on networks and hardware you own or are explicitly permitted to test,
with the knowing participation of connecting clients. This project never captures, stores,
or exfiltrates credentials, form input, or any client secret; telemetry records local prank
events only, not browsing contents. The MITM and captive-portal techniques here are the same
primitives used by real attacks — the boundaries above are what keep this a prank. Do not
deploy on shared, public, or unauthorized Wi-Fi. See README.md "Scope & authorization".
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app.admin_panel import AdminPanelAddon
    from app.config import RouterConfig
    from app.runtime import RuntimeState
    from modules.admin.admin_host import AdminHostAddon
    from modules.admin.dashboard import AdminDashboardAddon
    from modules.auth.magic_passwords import MagicPasswordAddon
    from modules.portal.captive_redirect import CaptivePortalAddon
    from modules.telemetry.logger import TelemetryLogger
    from modules.traffic.client_tracker import ClientTrackerAddon
    from modules.traffic.google_to_bing import GoogleToBingAddon
    from modules.traffic.mutators import MutationAddon
    from modules.traffic.redirect_rules import RedirectRuleAddon
except ModuleNotFoundError as exc:
    if exc.name == "mitmproxy":
        raise SystemExit("Missing dependency: install the project requirements with 'pip install -r requirements.txt'.") from exc
    raise


def build_addons(config: RouterConfig | None = None):
    config = config or RouterConfig.from_file("rules/default.yaml")
    runtime = RuntimeState(rules=dict(config.rules))
    logger = TelemetryLogger()

    addon_list = [
        ClientTrackerAddon(runtime=runtime),
        AdminHostAddon(runtime=runtime, hosts=tuple(config.admin_hosts)),
        CaptivePortalAddon(
            portal_url=f"http://{config.portal_host}:{config.portal_port}/portal",
            portal_host=config.portal_host,
            runtime=runtime,
        ),
        RedirectRuleAddon(config.redirects or {
            "google.com": f"http://{config.portal_host}:{config.portal_port}/portal/google",
            "github.com": f"http://{config.portal_host}:{config.portal_port}/portal/github",
            "adminpanel.com": f"http://{config.portal_host}:{config.portal_port}/",
        }, runtime=runtime),
        GoogleToBingAddon(runtime=runtime),
        MutationAddon(enabled=config.mutators_enabled, runtime=runtime),
        MagicPasswordAddon({
            password: mode for password, mode in {
                "banana": "banana_mode",
                "echo": "echo_mode",
                "penguin": "penguin_mode",
                "toaster": "toaster_mode",
            }.items()
        }),
        AdminDashboardAddon(runtime=runtime),
        AdminPanelAddon(runtime),
    ]
    return addon_list, runtime, logger


addons, runtime, logger = build_addons()

