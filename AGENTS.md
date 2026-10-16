# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Cursed Router is a local-only, lab-network prank project: a mitmproxy-based traffic layer plus a small admin panel that together turn a hostapd Wi-Fi hotspot into a theatrical captive portal / redirect / HTML-mutation experience. It is explicitly local-only and not for public or unauthorized networks (see `README.md` "Ethical / safety note").

`README.md` is largely an aspirational design doc — it describes many modules, phases, and a `wifi/` layer that do not exist yet. Treat the actual `app/` and `modules/` source as ground truth, not the README's "Suggested project layout".

## Running

```bash
pip install -r requirements.txt    # mitmproxy, PyYAML, Flask
python scripts/start_all.py        # starts the proxy and admin panel
```

`scripts/start_all.py` is the entry point. It runs a single **mitmdump** process on `listen_port=8080` with `app/main.py` as its addon script, passes its output through to the terminal, and exits with mitmdump's exit code. It locates `mitmdump` next to the running interpreter first (uv/venv) before falling back to PATH.

The **admin panel** (`0.0.0.0:8081`) runs inside that same mitmdump process: `AdminPanelAddon` starts it on a background thread in mitmproxy's `running` hook. So `mitmdump -s app/main.py --set listen_port=8080` is equivalent to `start_all.py` (run it from the repo root so `app/main.py`'s `sys.path` insert and the `rules/default.yaml` relative path resolve). There is no way to run the proxy without the panel, and if port 8081 is already taken (e.g. a stale panel, or `mitmweb`'s default UI port) mitmdump aborts at startup with `Address already in use`. `python app/main.py` on its own starts nothing.

There are no tests, linter, or typecheck config in the repo despite README mentions of a `tests/` dir. Shell tooling: use `rg`, `fd`, `eza`.

## Architecture

Everything runs in one mitmdump process:

1. **mitmproxy addon chain** (`app/main.py`). mitmproxy imports this module and reads its module-level `addons` list. `build_addons()` constructs that list from a `RouterConfig` loaded from `rules/default.yaml`. Each addon is a plain class implementing mitmproxy's `request(flow)` / `response(flow)` hooks — they mutate `flow.request` / set `flow.response` to redirect, rewrite, or inject. Order in the list is execution order.

2. **Admin panel** (`app/admin_panel.py`). A stdlib `BaseHTTPRequestHandler` server (no Flask despite the requirement) that renders a dashboard, exposes `GET /api/state` and `POST /` (`{client_ip, mode}` → `runtime.set_mode`), and serves fake prank portal pages. `AdminPanelAddon` (same file) hosts it inside mitmdump.

Key seam: `build_addons()` creates one `RuntimeState` (`app/runtime.py`) and hands it to both the admin panel and the addons, so they share live state (the panel's HTTP thread mutates it while mitmproxy's event loop reads it). However, no traffic addon reads `runtime` yet and nothing registers clients, so admin-panel mode changes don't affect traffic until an addon is wired to consult `runtime.active_modes` / `runtime.get_client()`.

### The addon chain (`modules/`)

Each module is a self-contained mitmproxy addon; add a new behavior by writing a class with `request`/`response` and appending it in `build_addons()`.

- `portal/captive_redirect.py` — intercepts OS captive-portal probe hosts (Apple/Google/Firefox/etc.) and serves a redirect to the local portal.
- `traffic/redirect_rules.py` — host → URL 302 map (config-driven via `redirects`).
- `traffic/google_to_bing.py` — demo addon that rewrites google.com requests to bing.com.
- `traffic/mutators.py` — rewrites `text/html` responses (title prefix + injected banner); gated by `mutators_enabled`.
- `auth/magic_passwords.py` — maps secret phrases (banana/echo/penguin/toaster/…) to "mode" names. Pure helper, not yet hooked into request flow.
- `admin/dashboard.py` — thin wrapper calling `runtime.set_mode`; distinct from the HTTP server in `app/admin_panel.py`.
- `telemetry/logger.py` — file logger to `logs/cursed_router.log`.

### Config

`app/config.py` `RouterConfig.from_file()` reads `rules/default.yaml` (portal host/port, `dns_server`, `mutators_enabled`, `redirects`, `magic_passwords`). YAML is optional at import — if PyYAML or the file is missing it falls back to dataclass defaults. Note the default host is `10.67.67.67` in config/yaml but several modules still carry hardcoded `10.0.0.1` / `127.0.0.1` defaults — keep these in sync when changing addresses.

## Conventions

Addons stay small and single-purpose (one file, one behavior). Behavior should be config/YAML-driven rather than hardcoded where practical. All modules use `from __future__ import annotations` and modern type hints.

## Todos

`todo-rutger.md` is Rutger's task checklist. Each task is a Markdown checkbox; keep the state marker current as work moves:

- `- [ ]` — not started
- `- [~]` — in progress (set this when you pick up a task)
- `- [x]` — complete

When you start working on one of these tasks, flip its box to `~`; when it's done, flip it to `x`. Don't delete completed items or restructure the list.
