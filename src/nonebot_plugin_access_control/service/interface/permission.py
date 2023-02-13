from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator, Tuple

from typing_extensions import overload, Literal

from nonebot_plugin_access_control.event_bus import T_Listener


class IServicePermission(ABC):
    @abstractmethod
    def on_set_permission(self, func: Optional[T_Listener] = None):
        raise NotImplementedError()

    @abstractmethod
    def on_change_permission(self, func: Optional[T_Listener] = None):
        raise NotImplementedError()

    @abstractmethod
    def on_remove_permission(self, func: Optional[T_Listener] = None):
        raise NotImplementedError()

    @overload
    async def get_permission(self, *subject: str, with_default: Literal[True] = True) -> bool:
        ...

    @overload
    async def get_permission(self, *subject: str, with_default: bool) -> Optional[bool]:
        ...

    @abstractmethod
    async def get_permission(self, *subject: str, with_default: bool = True) -> Optional[bool]:
        raise NotImplementedError()

    @abstractmethod
    def get_permissions(self) -> AsyncGenerator[Tuple[str, bool], None]:
        raise NotImplementedError()

    @abstractmethod
    async def set_permission(self, subject: str, allow: bool):
        raise NotImplementedError()

    @abstractmethod
    async def remove_permission(self, subject: str) -> bool:
        raise NotImplementedError()
