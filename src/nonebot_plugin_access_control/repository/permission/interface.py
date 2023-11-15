from typing import Optional, Protocol
from collections.abc import AsyncGenerator

from nonebot_plugin_access_control_api.service.interface import IService
from nonebot_plugin_access_control_api.models.permission import Permission


class IPermissionRepository(Protocol):
    async def get_permissions(
        self, service: Optional[IService], subject: Optional[str]
    ) -> AsyncGenerator[Permission, None]:
        raise NotImplementedError()
        yield Permission()  # noqa

    async def set_permission(
        self, service: Optional[IService], subject: str, allow: bool
    ) -> bool:
        raise NotImplementedError()

    async def remove_permission(
        self, service: Optional[IService], subject: str
    ) -> bool:
        raise NotImplementedError()
