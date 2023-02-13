from typing import Optional, AsyncGenerator, Tuple, TypeVar, Generic

from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from typing_extensions import overload, Literal

from ..interface.permission import IServicePermission
from ..interface.service import IService
from ...config import conf
from ...event_bus import T_Listener, on_event, EventType, fire_event
from ...models import PermissionOrm

T_Service = TypeVar("T_Service", bound=IService)


class ServicePermissionImpl(Generic[T_Service], IServicePermission):
    def __init__(self, service: T_Service):
        self.service = service

    def on_set_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_set_permission,
                        lambda service: service == self.service,
                        func)

    def on_change_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_change_permission,
                        lambda service: service == self.service,
                        func)

    def on_remove_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_remove_permission,
                        lambda service: service == self.service,
                        func)

    @staticmethod
    async def _node_permission_getter(node: T_Service, subject: str, session: AsyncSession) -> Optional[bool]:
        stmt = (select(PermissionOrm)
                .where(PermissionOrm.service == node.qualified_name,
                       PermissionOrm.subject == subject))
        p = (await session.execute(stmt)).scalar_one_or_none()
        if p is not None:
            return p.allow
        else:
            return None

    async def _get_permission(self, subject: str, session: AsyncSession) -> Optional[bool]:
        node: Optional[T_Service] = self.service
        allow = None

        while node is not None:
            p = await self._node_permission_getter(node, subject, session)
            if p is not None:
                allow = p
                break
            else:
                node = node.parent

        return allow

    @overload
    async def get_permission(self, *subject: str, with_default: Literal[True] = True) -> bool:
        ...

    @overload
    async def get_permission(self, *subject: str, with_default: bool) -> Optional[bool]:
        ...

    async def get_permission(self, *subject: str, with_default: bool = True) -> Optional[bool]:

        async with AsyncSession(get_engine()) as session:
            for sub in subject:
                allow = await self._get_permission(sub, session)
                if allow is not None:
                    return allow

            if with_default:
                return conf.access_control_default_permission == 'allow'
            else:
                return None

    async def get_permissions(self) -> AsyncGenerator[Tuple[str, bool], None]:
        async with AsyncSession(get_engine()) as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.service.qualified_name))
            async for p in await session.stream_scalars(stmt):
                yield p.subject, p.allow

    async def _fire_service_set_permission(self, subject: str, allow: bool):
        await fire_event(EventType.service_set_permission, {
            "service": self.service,
            "subject": subject,
            "allow": allow,
        })

    async def _fire_service_remove_permission(self, subject: str):
        await fire_event(EventType.service_remove_permission, {
            "service": self.service,
            "subject": subject
        })

    async def _fire_service_change_permission(self, subject: str, allow: bool, session: AsyncSession):
        await fire_event(EventType.service_change_permission, {
            "service": self.service,
            "subject": subject,
            "allow": allow,
        })

        async def dfs(node: T_Service):
            stmt = (select(count(PermissionOrm.subject))
                    .where(PermissionOrm.service == node.qualified_name,
                           PermissionOrm.subject == subject))
            cnt = (await session.execute(stmt)).scalar_one()

            if cnt == 0:
                await fire_event(EventType.service_change_permission, {
                    "service": node,
                    "subject": subject,
                    "allow": allow,
                })

        for c in self.service.children:
            await dfs(c)

    async def set_permission(self, subject: str, allow: bool):
        async with AsyncSession(get_engine()) as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.service.qualified_name,
                           PermissionOrm.subject == subject))
            p = (await session.execute(stmt)).scalar_one_or_none()
            if p is None:
                p = PermissionOrm(service=self.service.qualified_name,
                                  subject=subject,
                                  allow=allow)
                session.add(p)
                old_allow = None
            else:
                old_allow = p.allow
                p.allow = allow

            if old_allow != allow:
                await session.commit()
                await self._fire_service_set_permission(subject, allow)
                await self._fire_service_change_permission(subject, allow, session)
                return True
            else:
                return False

    async def remove_permission(self, subject: str) -> bool:
        async with AsyncSession(get_engine()) as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.service.qualified_name,
                           PermissionOrm.subject == subject))
            p = (await session.execute(stmt)).scalar_one_or_none()
            if p is None:
                return False

            await session.delete(p)
            await session.commit()

            await self._fire_service_remove_permission(subject)

            allow = await self.get_permission(subject)
            await self._fire_service_change_permission(subject, allow, session)

            return True
