from typing import Optional
from collections.abc import AsyncGenerator

from sqlalchemy import select

from ...context import context
from ..utils import use_ac_session
from ...service.interface import IService
from ..orm.permission import PermissionOrm
from ...models.permission import Permission
from .interface import IPermissionRepository
from ...service.interface.nonebot_service import INoneBotService


@context.bind_singleton_to(IPermissionRepository)
class PermissionRepository(IPermissionRepository):
    async def get_permissions(
        self, service: Optional[IService], subject: Optional[str]
    ) -> AsyncGenerator[Permission, None]:
        async with use_ac_session() as session:
            stmt = select(PermissionOrm)
            if service is not None:
                stmt = stmt.where(PermissionOrm.service == service.qualified_name)
            if subject is not None:
                stmt = stmt.where(PermissionOrm.subject == subject)

            async for x in await session.stream_scalars(stmt):
                s = service
                if s is None:
                    s = context.require(INoneBotService).get_service_by_qualified_name(
                        x.service
                    )
                if s is not None:
                    yield Permission(s, x.subject, x.allow)

    async def set_permission(
        self, service: Optional[IService], subject: str, allow: bool
    ) -> bool:
        async with use_ac_session() as sess:
            stmt = select(PermissionOrm).where(
                PermissionOrm.service == service.qualified_name,
                PermissionOrm.subject == subject,
            )
            p = (await sess.execute(stmt)).scalar_one_or_none()
            if p is None:
                p = PermissionOrm(
                    service=service.qualified_name, subject=subject, allow=allow
                )
                sess.add(p)
                old_allow = None
            else:
                old_allow = p.allow
                p.allow = allow

            if old_allow != allow:
                await sess.commit()
                return True
            else:
                return False

    async def remove_permission(
        self, service: Optional[IService], subject: str
    ) -> bool:
        async with use_ac_session() as sess:
            stmt = select(PermissionOrm).where(
                PermissionOrm.service == service.qualified_name,
                PermissionOrm.subject == subject,
            )
            p = (await sess.execute(stmt)).scalar_one_or_none()
            if p is None:
                return False

            await sess.delete(p)
            await sess.commit()
            return True
