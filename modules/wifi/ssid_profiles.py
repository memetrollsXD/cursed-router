DEFAULT_SSID_PROFILES = {
    "guest": {"ssid": "CursedRouter-Guest", "channel": 1},
    "cursed": {"ssid": "CursedRouter", "channel": 6},
    "admin": {"ssid": "CursedRouter-Admin", "channel": 11},
}


def get_profile(name: str) -> dict:
    return DEFAULT_SSID_PROFILES.get(name, DEFAULT_SSID_PROFILES["cursed"]).copy()
