"""Admin panel for the Cursed Router prank appliance.

Part of a local-only, consensual "useless projects" hackathon build. Serves a
dashboard and obviously-theatrical portal pages on the lab network and toggles
prank "modes". It stores no client credentials or browsing contents and sends
nothing off the local machine. See README.md "Scope & authorization".
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from app.runtime import RuntimeState


class AdminPanelHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/portal/adminpanel"}:
            self._send_html(self._render_dashboard())
            return

        if self.path in {"/portal/google", "/portal/github", "/portal/youtube"}:
            self._send_html(f"<html><body><h1>Router prank page</h1><p>This page has been cursed by the router.</p></body></html>")
            return

        if self.path == "/api/state":
            payload = json.dumps(self.server.runtime.as_dict()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        if self.path == "/api/rule":
            self._handle_rule(data)
            return

        client_ip = data.get("client_ip")
        mode = data.get("mode")
        if not client_ip or not mode:
            self.send_error(400, "client_ip and mode are required")
            return

        self.server.runtime.set_mode(client_ip, mode)
        self._send_json({"status": "ok", "client_ip": client_ip, "mode": mode})

    def _handle_rule(self, data: dict[str, Any]) -> None:
        rule = data.get("rule")
        if not rule or "enabled" not in data:
            self.send_error(400, "rule and enabled are required")
            return

        client_ip = data.get("client_ip") or None
        enabled = bool(data.get("enabled"))
        self.server.runtime.set_rule(client_ip, rule, enabled)
        self._send_json({"status": "ok", "client_ip": client_ip or "*", "rule": rule, "enabled": enabled})

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _render_dashboard(self) -> str:
        return """
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Cursed Router Admin</title>
            <style>
                body { font-family: sans-serif; background: #111; color: #eee; margin: 2rem; }
                .card { background: #1c1c1c; border: 1px solid #444; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }
                button { background: #ffb703; color: #111; border: none; border-radius: 8px; padding: 0.6rem 1rem; font-weight: bold; cursor: pointer; }
                input, select { padding: 0.5rem; border-radius: 8px; border: 1px solid #555; background: #222; color: #fff; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 0.75rem; border-bottom: 1px solid #333; text-align: left; }
            </style>
        </head>
        <body>
            <h1>🛠️ Cursed Router Admin</h1>
            <div class="card">
                <h2>Rule Defaults</h2>
                <p>Applied to any client without its own override.</p>
                <table>
                    <thead><tr><th>Rule</th><th>Default</th></tr></thead>
                    <tbody id="defaultsTable"></tbody>
                </table>
            </div>
            <div class="card">
                <h2>Per-Client Rules</h2>
                <p>Tick a box to enable a rule for that client; untick to disable it.</p>
                <table>
                    <thead><tr id="clientHead"><th>Client</th></tr></thead>
                    <tbody id="clientTable"></tbody>
                </table>
            </div>
            <div class="card">
                <h2>Event Log</h2>
                <pre id="logBox">Loading...</pre>
            </div>
            <script>
                function checkbox(ip, rule, enabled) {
                    const box = document.createElement('input');
                    box.type = 'checkbox';
                    box.checked = enabled;
                    box.onchange = () => setRule(ip, rule, box.checked);
                    return box;
                }
                async function fetchState() {
                    const res = await fetch('/api/state');
                    const data = await res.json();
                    const rules = Object.keys(data.rules || {}).sort();

                    const defaults = document.getElementById('defaultsTable');
                    defaults.innerHTML = '';
                    for (const rule of rules) {
                        const tr = document.createElement('tr');
                        const name = document.createElement('td');
                        name.textContent = rule;
                        const toggle = document.createElement('td');
                        toggle.appendChild(checkbox('*', rule, data.rules[rule]));
                        tr.appendChild(name);
                        tr.appendChild(toggle);
                        defaults.appendChild(tr);
                    }

                    const head = document.getElementById('clientHead');
                    head.innerHTML = '<th>Client</th><th>Portal</th>';
                    for (const rule of rules) {
                        const th = document.createElement('th');
                        th.textContent = rule;
                        head.appendChild(th);
                    }

                    const tbody = document.getElementById('clientTable');
                    tbody.innerHTML = '';
                    const clients = data.clients || {};
                    for (const [ip, info] of Object.entries(clients)) {
                        const tr = document.createElement('tr');
                        const ipCell = document.createElement('td');
                        ipCell.textContent = ip;
                        tr.appendChild(ipCell);
                        const portalCell = document.createElement('td');
                        portalCell.textContent = info.portal_seen ? 'yes' : 'no';
                        tr.appendChild(portalCell);
                        const clientRules = info.rules || {};
                        for (const rule of rules) {
                            const cell = document.createElement('td');
                            cell.appendChild(checkbox(ip, rule, clientRules[rule]));
                            tr.appendChild(cell);
                        }
                        tbody.appendChild(tr);
                    }
                    if (!Object.keys(clients).length) {
                        tbody.innerHTML = '<tr><td colspan="' + (rules.length + 2) + '">No clients seen yet.</td></tr>';
                    }

                    document.getElementById('logBox').textContent = (data.logs || []).join('\n') || 'No events yet.';
                }
                async function setRule(clientIp, rule, enabled) {
                    await fetch('/api/rule', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ client_ip: clientIp, rule, enabled }) });
                    await fetchState();
                }
                setInterval(fetchState, 2000);
                fetchState();
            </script>
        </body>
        </html>
        """


class AdminPanelServer(HTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_class: type[BaseHTTPRequestHandler], runtime: RuntimeState):
        super().__init__(server_address, handler_class)
        self.runtime = runtime


def start_admin_panel(runtime: RuntimeState, host: str = "0.0.0.0", port: int = 8081) -> AdminPanelServer:
    server = AdminPanelServer((host, port), AdminPanelHandler, runtime)
    return server


class AdminPanelAddon:
    """Serves the admin panel from inside the mitmdump process so it shares the proxy's runtime state."""

    def __init__(self, runtime: RuntimeState, host: str = "0.0.0.0", port: int = 8081):
        self.runtime = runtime
        self.host = host
        self.port = port
        self.server: AdminPanelServer | None = None

    def running(self) -> None:
        self.server = start_admin_panel(self.runtime, self.host, self.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        print(f"Admin panel listening on http://{self.host}:{self.port}")

    def done(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
