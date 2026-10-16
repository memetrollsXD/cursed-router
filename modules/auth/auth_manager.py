from __future__ import annotations

from dataclasses import dataclass

from modules.auth.magic_passwords import resolve_mood
from modules.auth.ppsk_experiments import validate_psk


@dataclass
class AuthManager:
    mode: str = "magic-passwords"

    def authorize(self, client_id: str, secret: str) -> tuple[bool, str]:
        if self.mode == "everyone-is-allowed":
            return True, "open-lab-mode"

        if self.mode == "magic-passwords":
            mood = resolve_mood(secret)
            return (mood is not None, mood or "invalid-magic")

        if self.mode == "ppsk":
            ok = validate_psk(client_id, secret)
            return ok, "ppsk-accepted" if ok else "ppsk-denied"

        return False, "unsupported-mode"
