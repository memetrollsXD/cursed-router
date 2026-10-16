"""Shared HTML for the Cursed Router admin dashboard.

Rendered both by the standalone admin-panel HTTP server (app/admin_panel.py) and
by the proxy addon that serves the dashboard directly on the admin host so the
admin.com URL stays intact instead of bouncing to a raw IP.
"""
from __future__ import annotations


def render_dashboard() -> str:
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

                    document.getElementById('logBox').textContent = (data.logs || []).join('\\n') || 'No events yet.';
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
