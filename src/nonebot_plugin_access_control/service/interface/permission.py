from abc import ABC, abstractmethod
from typing import Optional
from collections.abc import AsyncGenerator

from nonebot_plugin_access_control.event_bus import T_Listener
from ..permission import Permission


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
    async def get_permission_by_subject(
        self, *subject: str, trace: bool = True
    ) -> Optional[Permission]:
        raise NotImplementedError()

    @abstractmethod
    def get_permissions(
        self, *, trace: bool = True
    ) -> AsyncGenerator[Permission, None]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_all_permissions_by_subject(
        cls, *subject: str
    ) -> AsyncGenerator[Permission, None]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_all_permissions(cls) -> AsyncGenerator[Permission, None]:
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
