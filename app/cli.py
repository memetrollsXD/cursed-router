from __future__ import annotations

import argparse

from app.main import CursedRouterApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cursed Router control CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("start", help="Start the cursed router")
    sub.add_parser("status", help="Show one-shot status")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    app = CursedRouterApp()

    if args.command == "start":
        app.run_once()
        print("Cursed router started")
        return 0

    status = app.run_once()
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
