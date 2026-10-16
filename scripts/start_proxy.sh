#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

mitmproxy --mode regular --listen-port 8080 --set confdir=./config