from modules.auth.auth_manager import AuthManager


def test_magic_password_accepts_known_phrase() -> None:
    auth = AuthManager(mode="magic-passwords")
    accepted, mood = auth.authorize("device-1", "banana")
    assert accepted is True
    assert mood == "banana-mode"


def test_ppsk_rejects_unknown_key() -> None:
    auth = AuthManager(mode="ppsk")
    accepted, reason = auth.authorize("device-7", "wrong")
    assert accepted is False
    assert reason == "ppsk-denied"
