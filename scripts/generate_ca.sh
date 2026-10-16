#!/usr/bin/env bash
set -euo pipefail

mitmproxy --version >/dev/null 2>&1 || {
  echo "mitmproxy is not installed. Install it from requirements.txt first."
  exit 1
}

mkdir -p ./config
mitmdump --set confdir=./config --scripts ./app/main.py
# The CA is generated when mitmproxy runs for the first time; this script is intentionally lightweight.
