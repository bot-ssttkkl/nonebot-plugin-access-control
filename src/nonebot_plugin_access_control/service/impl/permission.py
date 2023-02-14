from typing import Optional, AsyncGenerator, TypeVar, Generic

from nonebot import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from ..interface.permission import IServicePermission
from ..interface.service import IService
from ..permission import Permission
from ...config import conf
from ...event_bus import T_Listener, on_event, EventType, fire_event
from ...models import PermissionOrm
from ...utils.session import use_session_or_create

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
                                          subject: Optional[str],
                                          session: AsyncSession) -> AsyncGenerator[Permission, None]:
        stmt = select(PermissionOrm).where(
            PermissionOrm.service == service.qualified_name
        )
        if subject is not None:
            stmt.append_whereclause(PermissionOrm.subject == subject)

        async for x in await session.stream_scalars(stmt):
            yield Permission(x, service)

    async def get_permission(self, *subject: str, trace: bool = True,
                             session: Optional[AsyncSession] = None) -> Optional[Permission]:
        async with use_session_or_create(session) as sess:
            for sub in subject:
                if trace:
                    for node in self.service.trace():
                        async for p in self._get_permissions_by_subject(node, sub, sess):
                            return p
                else:
                    async for p in self._get_permissions_by_subject(self.service, sub, sess):
                        return p

            return None

    async def get_all_permissions(self, *, trace: bool = True,
                                  session: Optional[AsyncSession] = None) -> AsyncGenerator[Permission, None]:
        async with use_session_or_create(session) as sess:
            if trace:
                for node in self.service.trace():
                    async for p in self._get_permissions_by_subject(node, None, sess):
                        yield p
            else:
                async for p in self._get_permissions_by_subject(self.service, None, sess):
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

    async def set_permission(self, subject: str, allow: bool, session: Optional[AsyncSession] = None) -> bool:
        async with use_session_or_create(session) as sess:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.service.qualified_name,
                           PermissionOrm.subject == subject))
            p = (await sess.execute(stmt)).scalar_one_or_none()
            if p is None:
                p = PermissionOrm(service=self.service.qualified_name,
                                  subject=subject,
                                  allow=allow)
                sess.add(p)
                old_allow = None
            else:
                old_allow = p.allow
                p.allow = allow

            if old_allow != allow:
                await sess.commit()
                await self._fire_service_set_permission(subject, allow)
                await self._fire_service_change_permission(subject, allow, sess)
                return True
            else:
                return False

    async def remove_permission(self, subject: str, session: Optional[AsyncSession] = None) -> bool:
        async with use_session_or_create(session) as sess:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.service.qualified_name,
                           PermissionOrm.subject == subject))
            p = (await sess.execute(stmt)).scalar_one_or_none()
            if p is None:
                return False

            await sess.delete(p)
            await sess.commit()

            await self._fire_service_remove_permission(subject)

            p = await self.get_permission(subject)
            if p is not None:
                allow = p.allow
            else:
                allow = conf.access_control_default_permission == 'allow'
            await self._fire_service_change_permission(subject, allow, sess)

            return True

    async def check_permission(self, *subject: str, session: Optional[AsyncSession] = None) -> bool:
        async with use_session_or_create(session) as sess:
            p = await self.get_permission(*subject, session=sess)
            if p is not None:
                logger.trace(f"[permission] {'allowed' if p.allow else 'denied'} "
                             f"(service: {p.service}, subject: {p.subject})")
                return p.allow
            else:
                allow = conf.access_control_default_permission == 'allow'
                logger.trace(f"[permission] {'allowed' if allow else 'denied'} (default) "
                             f"(service: {self.service.qualified_name})")
                return allow
