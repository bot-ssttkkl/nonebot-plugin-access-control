from typing import TYPE_CHECKING

from .subservice import SubService
from .subservice_owner import SubServiceOwner

if TYPE_CHECKING:
    from .nonebot import NoneBotService


class PluginService(SubServiceOwner["NoneBotService", SubService]):
    def __init__(self, name: str, auto_created: bool, parent: "NoneBotService"):
        super().__init__()
        self._name = name
        self._auto_created = auto_created
        self._parent = parent

    @property
    def name(self) -> str:
        return self._name

    @property
    def qualified_name(self) -> str:
        return self._name

    @property
    def parent(self) -> "NoneBotService":
        return self._parent

    @property
    def auto_created(self) -> bool:
        return self._auto_created

    def _make_subservice(self, name: str) -> SubService:
        return SubService(name, self)
