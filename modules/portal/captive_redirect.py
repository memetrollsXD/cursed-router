"""Captive-portal redirect addon for the Cursed Router prank appliance.

Part of a local-only, consensual "useless projects" hackathon build. Answers the
OS connectivity probes with a redirect to a local, obviously-theatrical portal on
a lab network whose users are in on the joke. It captures no credentials and
exfiltrates nothing off the local machine. See README.md "Scope & authorization".
"""
from __future__ import annotations

from typing import Any

from mitmproxy import http

from modules.gating import rule_enabled

RULE = "captive_portal"


class CaptivePortalAddon:
    """Intercepts common captive portal probes and redirects browsers to a local fake portal."""

    def __init__(
        self,
        portal_url: str = "http://10.67.67.67:8081/portal",
        portal_host: str = "10.67.67.67",
        runtime: Any | None = None,
    ):
        self.portal_url = portal_url
        self.portal_host = portal_host
        self.runtime = runtime
        self.portal_hosts = {
            "connectivitycheck.gstatic.com",
            "clients3.google.com",
            "captive.apple.com",
            "msftconnecttest.com",
            "detectportal.firefox.com",
            "nmcheck.gnome.org",
        }

    def request(self, flow: http.HTTPFlow) -> None:
        if not rule_enabled(self.runtime, flow, RULE):
            return

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

        if flow.request.host == self.portal_host and flow.request.path.startswith("/portal"):
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
