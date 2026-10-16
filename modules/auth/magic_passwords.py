from __future__ import annotations


class MagicPasswordAddon:
    """Small helper layer that maps magic passwords to hilarious modes."""

    def __init__(self, password_modes: dict[str, str] | None = None):
        self.password_modes = password_modes or {
            "banana": "banana_mode",
            "echo": "echo_mode",
            "penguin": "penguin_mode",
            "toaster": "toaster_mode",
            "quasar": "quasar_mode",
        }

    def resolve_password(self, password: str) -> str | None:
        return self.password_modes.get(password.strip().lower())

    def handle_password(self, client_ip: str, password: str) -> dict[str, str] | None:
        mode = self.resolve_password(password)
        if mode is None:
            return None

        return {
            "client_ip": client_ip,
            "mode": mode,
            "message": f"Magic password accepted for {client_ip}. The router is now in {mode}.",
        }
