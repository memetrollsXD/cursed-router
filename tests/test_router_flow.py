from app.main import CursedRouterApp


def test_router_one_shot_run() -> None:
    app = CursedRouterApp()
    status = app.run_once()
    assert status["wifi_running"] is True
    assert status["rules_loaded"] >= 1
