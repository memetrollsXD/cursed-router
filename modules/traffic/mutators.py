from __future__ import annotations

from mitmproxy import http


class MutationAddon:
    """Mutates HTML content in a harmless but theatrical way."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def response(self, flow: http.HTTPFlow) -> None:
        if not self.enabled:
            return

        if not flow.response or not flow.response.content:
            return

        content_type = flow.response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return

        try:
            text = flow.response.text
        except Exception:
            return

        if not text:
            return

        text = text.replace("<title>", "<title>Actually this is a toaster - ")
        text = text.replace("</body>", """
            <div style="position:fixed;bottom:16px;right:16px;background:#111;color:#ffd700;padding:12px;border-radius:8px;border:1px solid #ffd700;z-index:99999;font-family:sans-serif;">
                The router is deeply committed to the bit.
            </div>
        </body>
        """)

        flow.response.text = text
