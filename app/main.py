from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app.config import RouterConfig
    from app.runtime import RuntimeState
    from modules.admin.dashboard import AdminDashboardAddon
    from modules.auth.magic_passwords import MagicPasswordAddon
    from modules.portal.captive_redirect import CaptivePortalAddon
    from modules.telemetry.logger import TelemetryLogger
    from modules.traffic.google_to_bing import GoogleToBingAddon
    from modules.traffic.mutators import MutationAddon
    from modules.traffic.redirect_rules import RedirectRuleAddon
except ModuleNotFoundError as exc:
    if exc.name == "mitmproxy":
        raise SystemExit("Missing dependency: install the project requirements with 'pip install -r requirements.txt'.") from exc
    raise


def build_addons(config: RouterConfig | None = None):
    config = config or RouterConfig()
    runtime = RuntimeState()
    logger = TelemetryLogger()

    addon_list = [
        CaptivePortalAddon(portal_url=f"http://{config.portal_host}:{config.portal_port}/portal"),
        RedirectRuleAddon(config.redirects or {
            "google.com": f"http://{config.portal_host}:{config.portal_port}/portal/google",
            "github.com": f"http://{config.portal_host}:{config.portal_port}/portal/github",
        }),
        GoogleToBingAddon(),
        MutationAddon(enabled=config.mutators_enabled),
        MagicPasswordAddon({
            password: mode for password, mode in {
                "banana": "banana_mode",
                "echo": "echo_mode",
                "penguin": "penguin_mode",
                "toaster": "toaster_mode",
            }.items()
        }),
        AdminDashboardAddon(runtime=runtime),
    ]
    return addon_list, runtime, logger


addons, runtime, logger = build_addons()


if __name__ == "__main__":
    logger.info("Cursed Router startup complete")
    print("Cursed router ready.")
    print("Installed addons:", len(addons))
    print("Runtime state:", runtime.as_dict())
