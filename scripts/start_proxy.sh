#!/usr/bin/env bash
set -euo pipefail

mitmdump -q -s app/main.py --set listen_port=8080