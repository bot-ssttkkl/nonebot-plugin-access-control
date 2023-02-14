from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator

from nonebot_plugin_access_control.event_bus import T_Listener
from nonebot_plugin_access_control.service.permission import Permission


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

    @abstractmethod
    async def get_permission(self, *subject: str, trace: bool = True) -> Optional[Permission]:
        ...

    @abstractmethod
    def get_all_permissions(self, *, trace: bool = True) -> AsyncGenerator[Permission, None]:
        raise NotImplementedError()

    @abstractmethod
    async def set_permission(self, subject: str, allow: bool) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def remove_permission(self, subject: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def check_permission(self, *subject: str) -> bool:
        raise NotImplementedError()
