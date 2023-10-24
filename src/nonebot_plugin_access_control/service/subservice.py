from typing import Union

from typing import TYPE_CHECKING

from .subservice_owner import SubServiceOwner

if TYPE_CHECKING:
    from .plugin import PluginService


class SubService(SubServiceOwner[Union["PluginService", "SubService"], "SubService"]):
    def __init__(self, name: str, parent: Union["PluginService", "SubService"]):
        super().__init__()
        self._name = name
        self._parent = parent

    @property
    def name(self) -> str:
        return self._name

    @property
    def qualified_name(self) -> str:
        return self.parent.qualified_name + "." + self.name

    @property
    def parent(self) -> Union["PluginService", "SubService"]:
        return self._parent

    def _make_subservice(self, name: str) -> "SubService":
        return SubService(name, self)
