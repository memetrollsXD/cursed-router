import unittest

from app.main import CursedRouterApp


class TestRouterFlow(unittest.TestCase):
    def test_router_one_shot_run(self) -> None:
        app = CursedRouterApp()
        status = app.run_once()
        self.assertTrue(status["wifi_running"])
        self.assertGreaterEqual(status["rules_loaded"], 1)


if __name__ == "__main__":
    unittest.main()
