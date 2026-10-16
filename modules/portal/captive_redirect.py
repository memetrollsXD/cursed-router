from __future__ import annotations

from mitmproxy import http


class CaptivePortalAddon:
    """Intercepts common captive portal probes and redirects browsers to a local fake portal."""

    def __init__(self, portal_url: str = "http://10.0.0.1:8081/portal"):
        self.portal_url = portal_url
        self.portal_hosts = {
            "connectivitycheck.gstatic.com",
            "clients3.google.com",
            "captive.apple.com",
            "msftconnecttest.com",
            "detectportal.firefox.com",
            "nmcheck.gnome.org",
        }

    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.pretty_host.lower()
        if host in self.portal_hosts:
            flow.response = http.Response.make(
                200,
                (
                    "<html><head><title>Router Access Check</title></head>"
                    "<body><meta http-equiv='refresh' content='0;url="
                    + self.portal_url
                    + "' /></body></html>"
                ).encode("utf-8"),
                {"Content-Type": "text/html; charset=utf-8"},
            )
            return

        if flow.request.host == "10.0.0.1" and flow.request.path.startswith("/portal"):
            flow.response = http.Response.make(
                200,
                b"""
                <html>
                  <head><title>Cursed Router Portal</title></head>
                  <body style="font-family:sans-serif;background:#111;color:#eee;padding:2rem;">
                    <h1>Welcome to the Internet, Possibly</h1>
                    <p>The access point is performing an interpretive review of your browsing experience.</p>
                    <form>
                      <label>Password:</label><br>
                      <input type="password" name="password" /><br><br>
                      <button type="submit">Accept the absurdity</button>
                    </form>
                  </body>
                </html>
                """,
                {"Content-Type": "text/html; charset=utf-8"},
            )
