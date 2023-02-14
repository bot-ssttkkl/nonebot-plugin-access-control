from typing import Optional, AsyncGenerator, TypeVar, Generic

from nonebot import logger
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from ..interface.permission import IServicePermission
from ..interface.service import IService
from ..permission import Permission
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
    async def _get_permissions_by_subject(service: T_Service,
                                          subject: Optional[str]) -> AsyncGenerator[Permission, None]:
        async with AsyncSession(get_engine()) as session:
            stmt = select(PermissionOrm).where(
                PermissionOrm.service == service.qualified_name
            )
            if subject is not None:
                stmt.append_whereclause(PermissionOrm.subject == subject)

            async for x in await session.stream_scalars(stmt):
                yield Permission(x, service)

    async def get_permission(self, *subject: str, trace: bool = True) -> Optional[Permission]:
        for sub in subject:
            if trace:
                for node in self.service.trace():
                    async for p in self._get_permissions_by_subject(node, sub):
                        return p
            else:
                async for p in self._get_permissions_by_subject(self.service, sub):
                    return p

        return None

    async def get_all_permissions(self, *, trace: bool = True) -> AsyncGenerator[Permission, None]:
        if trace:
            for node in self.service.trace():
                async for p in self._get_permissions_by_subject(node, None):
                    yield p
        else:
            async for p in self._get_permissions_by_subject(self.service, None):
                yield p

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

            p = await self.get_permission(subject)
            await self._fire_service_change_permission(subject, p.allow, session)

            return True

    async def check_permission(self, *subject: str) -> bool:
        p = await self.get_permission(*subject)
        if p is not None:
            logger.trace(f"[permission] {'allowed' if p.allow else 'denied'} "
                         f"(service: {p.service}, subject: {p.subject})")
            return p.allow
        else:
            allow = conf.access_control_default_permission == 'allow'
            logger.trace(f"[permission] {'allowed' if allow else 'denied'} (default) "
                         f"(service: {self.service.qualified_name}, subject: {p.subject})")
            return allow
