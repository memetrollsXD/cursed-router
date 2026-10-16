from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROXY_HOST = "10.67.67.67"
PROXY_PORT = 8090
WATCH_DIRS = ("app", "modules", "rules")
WATCH_SUFFIXES = {".py", ".yaml", ".yml"}
POLL_SECONDS = 1.0


def find_mitmdump() -> str:
    # The venv isn't necessarily activated, so look next to the running interpreter first.
    venv_bin = str(Path(sys.executable).parent)
    mitmdump = shutil.which("mitmdump", path=venv_bin) or shutil.which("mitmdump")
    if not mitmdump:
        raise SystemExit("mitmdump is not installed or not on PATH. Install mitmproxy first.")
    return mitmdump


def snapshot_sources() -> dict[Path, float]:
    return {
        path: path.stat().st_mtime
        for directory in WATCH_DIRS
        for path in (ROOT / directory).rglob("*")
        if path.suffix in WATCH_SUFFIXES and path.is_file()
    }


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def main() -> int:
    print(f"Starting cursed-router from {ROOT}", flush=True)
    cmd = [
        find_mitmdump(), "-q", "-s", "app/main.py",
        "--set", f"listen_host={PROXY_HOST}",
        "--set", f"listen_port={PROXY_PORT}",
    ]
    proc = subprocess.Popen(cmd, cwd=ROOT)
    sources = snapshot_sources()
    try:
        while True:
            time.sleep(POLL_SECONDS)
            current = snapshot_sources()
            if current == sources:
                continue
            sources = current
            print("Source change detected, restarting mitmdump", flush=True)
            stop(proc)
            proc = subprocess.Popen(cmd, cwd=ROOT)
    except KeyboardInterrupt:
        stop(proc)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
