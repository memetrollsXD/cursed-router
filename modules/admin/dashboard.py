from __future__ import annotations

from dataclasses import dataclass, field

from modules.admin.client_actions import ClientAction


@dataclass
class AdminDashboard:
    actions: list[ClientAction] = field(default_factory=list)

    def dispatch(self, action: ClientAction) -> None:
        self.actions.append(action)

    def history(self) -> list[ClientAction]:
        return list(self.actions)
