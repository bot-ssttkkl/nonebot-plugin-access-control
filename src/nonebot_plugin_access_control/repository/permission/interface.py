from typing import Optional, Protocol
from collections.abc import AsyncGenerator

from ...service.interface import IService
from ...models.permission import Permission


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
