from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROXY_PORT = 8080


def find_mitmdump() -> str:
    # The venv isn't necessarily activated, so look next to the running interpreter first.
    venv_bin = str(Path(sys.executable).parent)
    mitmdump = shutil.which("mitmdump", path=venv_bin) or shutil.which("mitmdump")
    if not mitmdump:
        raise SystemExit("mitmdump is not installed or not on PATH. Install mitmproxy first.")
    return mitmdump


def main() -> int:
    print(f"Starting cursed-router from {ROOT}", flush=True)
    cmd = [find_mitmdump(), "-q", "-s", "app/main.py", "--set", f"listen_port={PROXY_PORT}"]
    try:
        return subprocess.run(cmd, cwd=ROOT).returncode
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
