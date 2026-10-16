from __future__ import annotations

from dataclasses import dataclass

from modules.traffic.page_mutator import PageMutator


@dataclass
class MITMProxy:
    mutator: PageMutator

    def transform_html(self, html: str, mode: str = "default") -> str:
        return self.mutator.mutate(html, mode)
