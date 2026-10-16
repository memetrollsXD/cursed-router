import unittest

from modules.auth.auth_manager import AuthManager


class TestAuthManager(unittest.TestCase):
    def test_magic_password_accepts_known_phrase(self) -> None:
        auth = AuthManager(mode="magic-passwords")
        accepted, mood = auth.authorize("device-1", "banana")
        self.assertTrue(accepted)
        self.assertEqual(mood, "banana-mode")

    def test_ppsk_rejects_unknown_key(self) -> None:
        auth = AuthManager(mode="ppsk")
        accepted, reason = auth.authorize("device-7", "wrong")
        self.assertFalse(accepted)
        self.assertEqual(reason, "ppsk-denied")


if __name__ == "__main__":
    unittest.main()
