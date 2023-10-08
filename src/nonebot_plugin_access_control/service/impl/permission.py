from typing import Optional, TypeVar, Generic
from collections.abc import AsyncGenerator

from nonebot import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..interface.permission import IServicePermission
from ..interface.service import IService
from ..permission import Permission
from ...config import conf
from ...event_bus import T_Listener, on_event, EventType, fire_event
from ...models import PermissionOrm
from ...utils.session import use_ac_session

T_Service = TypeVar("T_Service", bound=IService)


class ServicePermissionImpl(Generic[T_Service], IServicePermission):
    def __init__(self, service: T_Service):
        self.service = service

    def on_set_permission(self, func: Optional[T_Listener] = None):
        return on_event(
            EventType.service_set_permission,
            lambda service: service == self.service,
            func,
        )

    def on_change_permission(self, func: Optional[T_Listener] = None):
        return on_event(
            EventType.service_change_permission,
            lambda service: service == self.service,
            func,
        )

    def on_remove_permission(self, func: Optional[T_Listener] = None):
        return on_event(
            EventType.service_remove_permission,
            lambda service: service == self.service,
            func,
        )

    @staticmethod
    async def _get_permissions(
        service: Optional[T_Service], subject: Optional[str]
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
                    from ..methods import get_service_by_qualified_name

                    s = get_service_by_qualified_name(x.service)
                if s is not None:
                    yield Permission(s, x.subject, x.allow)

    async def get_permission_by_subject(
        self, *subject: str, trace: bool = True
    ) -> Optional[Permission]:
        for sub in subject:
            if trace:
                for node in self.service.trace():
                    async for p in self._get_permissions(node, sub):
                        return p
            else:
                async for p in self._get_permissions(self.service, sub):
                    return p

        return None

    async def get_permissions(
        self, *, trace: bool = True
    ) -> AsyncGenerator[Permission, None]:
        if trace:
            for node in self.service.trace():
                async for p in self._get_permissions(node, None):
                    yield p
        else:
            async for p in self._get_permissions(self.service, None):
                yield p

    @classmethod
    async def get_all_permissions_by_subject(
        cls, *subject: str
    ) -> AsyncGenerator[Permission, None]:
        overridden_services = set()
        for sub in subject:
            async for x in cls._get_permissions(None, sub):
                if x.service not in overridden_services:
                    yield x
                    overridden_services.add(x.service)

    @classmethod
    async def get_all_permissions(cls) -> AsyncGenerator[Permission, None]:
        async for x in cls._get_permissions(None, None):
            yield x

    async def _fire_service_set_permission(self, subject: str, allow: bool):
        await fire_event(
            EventType.service_set_permission,
            {
                "service": self.service,
                "permission": Permission(self.service, subject, allow),
            },
        )

    async def _fire_service_remove_permission(self, subject: str):
        await fire_event(
            EventType.service_remove_permission,
            {"service": self.service, "subject": subject},
        )

    async def _fire_service_change_permission(
        self, subject: str, allow: bool, session: AsyncSession
    ):
        await fire_event(
            EventType.service_change_permission,
            {
                "service": self.service,
                "permission": Permission(self.service, subject, allow),
            },
        )

        for node in self.service.travel():
            if node == self.service:
                continue

            cnt = 0
            async for x in self._get_permissions(node, subject):
                cnt += 1

            if cnt == 0:
                await fire_event(
                    EventType.service_change_permission,
                    {
                        "service": node,
                        "permission": Permission(node, subject, allow),
                    },
                )

    async def set_permission(self, subject: str, allow: bool) -> bool:
        async with use_ac_session() as sess:
            stmt = select(PermissionOrm).where(
                PermissionOrm.service == self.service.qualified_name,
                PermissionOrm.subject == subject,
            )
            p = (await sess.execute(stmt)).scalar_one_or_none()
            if p is None:
                p = PermissionOrm(
                    service=self.service.qualified_name, subject=subject, allow=allow
                )
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

    async def remove_permission(self, subject: str) -> bool:
        async with use_ac_session() as sess:
            stmt = select(PermissionOrm).where(
                PermissionOrm.service == self.service.qualified_name,
                PermissionOrm.subject == subject,
            )
            p = (await sess.execute(stmt)).scalar_one_or_none()
            if p is None:
                return False

            await sess.delete(p)
            await sess.commit()

            await self._fire_service_remove_permission(subject)

            p = await self.get_permission_by_subject(subject)
            if p is not None:
                allow = p.allow
            else:
                allow = conf().access_control_default_permission == "allow"
            await self._fire_service_change_permission(subject, allow, sess)

            return True

    async def check_permission(self, *subject: str) -> bool:
        p = await self.get_permission_by_subject(*subject)
        if p is not None:
            logger.debug(
                f"[permission] {'allowed' if p.allow else 'denied'} "
                f"(service: {p.service}, subject: {p.subject})"
            )
            return p.allow
        else:
            allow = conf().access_control_default_permission == "allow"
            logger.debug(
                f"[permission] {'allowed' if allow else 'denied'} (default) "
                f"(service: {self.service.qualified_name})"
            )
            return allow
