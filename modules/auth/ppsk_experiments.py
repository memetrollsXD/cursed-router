PPSK_KEYS = {
    "device-1": "quasar-biscuit",
    "device-7": "magic-toast",
}


def validate_psk(client_id: str, key: str) -> bool:
    return PPSK_KEYS.get(client_id) == key
