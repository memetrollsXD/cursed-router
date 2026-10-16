from __future__ import annotations


class PageMutator:
    def mutate(self, html: str, mode: str = "default") -> str:
        if mode == "banana-mode":
            return html.replace("<title>", "<title>🍌 ")
        if mode == "penguin-mode":
            return html.replace("<title>", "<title>🐧 ")
        return html
