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

        client_ip = data.get("client_ip")
        mode = data.get("mode")
        if not client_ip or not mode:
            self.send_error(400, "client_ip and mode are required")
            return

        self.server.runtime.set_mode(client_ip, mode)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "client_ip": client_ip, "mode": mode}).encode("utf-8"))

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
                <h2>Client Mood Control</h2>
                <input id="clientIp" placeholder="192.168.1.12" value="192.168.1.12" />
                <select id="modeSelect">
                    <option value="default">default</option>
                    <option value="banana_mode">banana_mode</option>
                    <option value="echo_mode">echo_mode</option>
                    <option value="penguin_mode">penguin_mode</option>
                    <option value="toaster_mode">toaster_mode</option>
                </select>
                <button onclick="sendMode()">Apply Curse</button>
            </div>
            <div class="card">
                <h2>Connected Clients</h2>
                <table>
                    <thead>
                        <tr><th>Client</th><th>Mode</th><th>Portal</th></tr>
                    </thead>
                    <tbody id="clientTable"></tbody>
                </table>
            </div>
            <div class="card">
                <h2>Event Log</h2>
                <pre id="logBox">Loading...</pre>
            </div>
            <script>
                async function fetchState() {
                    const res = await fetch('/api/state');
                    const data = await res.json();
                    const tbody = document.getElementById('clientTable');
                    tbody.innerHTML = '';
                    const clients = data.clients || {};
                    for (const [ip, info] of Object.entries(clients)) {
                        const tr = document.createElement('tr');
                        tr.innerHTML = '<td>' + ip + '</td><td>' + (info.mode || 'default') + '</td><td>' + (info.portal_seen ? 'yes' : 'no') + '</td>';
                        tbody.appendChild(tr);
                    }
                    document.getElementById('logBox').textContent = (data.logs || []).join('\n') || 'No events yet.';
                }
                async function sendMode() {
                    const payload = { client_ip: document.getElementById('clientIp').value, mode: document.getElementById('modeSelect').value };
                    await fetch('/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
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
