from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN_HOST = "0.0.0.0"
ADMIN_PORT = 8081
PROXY_PORT = 8080


def ensure_root() -> None:
    os.chdir(ROOT)


def start_admin_panel() -> subprocess.Popen[str]:
    cmd = [
        sys.executable,
        "-c",
        (
            "from app.admin_panel import start_admin_panel; "
            "from app.runtime import RuntimeState; "
            "server = start_admin_panel(RuntimeState(), '0.0.0.0', 8081); "
            "print('Admin panel listening on http://127.0.0.1:8081'); "
            "server.serve_forever()"
        ),
    ]
    return subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def start_proxy() -> subprocess.Popen[str]:
    mitmdump = shutil.which("mitmdump")
    if not mitmdump:
        raise RuntimeError("mitmdump is not installed or not on PATH. Install mitmproxy first.")

    cmd = [mitmdump, "-q", "-s", "app/main.py", "--set", f"listen_port={PROXY_PORT}"]
    return subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def main() -> int:
    ensure_root()
    print(f"Starting cursed-router services from {ROOT}")

    admin = start_admin_panel()
    proxy = start_proxy()

    def shutdown(_signum, _frame) -> None:
        print("\nStopping services...")
        for child in (admin, proxy):
            if child.poll() is None:
                child.terminate()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            admin_status = admin.poll()
            proxy_status = proxy.poll()
            if admin_status is not None:
                print(f"Admin panel exited unexpectedly with code {admin_status}")
                break
            if proxy_status is not None:
                print(f"Mitmproxy exited unexpectedly with code {proxy_status}")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping all services.")
    finally:
        for child in (admin, proxy):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
