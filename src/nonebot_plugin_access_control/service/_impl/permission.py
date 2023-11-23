from typing import Optional
from collections.abc import AsyncGenerator

from nonebot import logger
from nonebot_plugin_access_control_api.context import context
from nonebot_plugin_access_control_api.models.permission import Permission
from nonebot_plugin_access_control_api.service.interface.service import IService
from nonebot_plugin_access_control_api.service.interface.permission import (
    IServicePermission,
)
from nonebot_plugin_access_control_api.event_bus import (
    EventType,
    T_Listener,
    on_event,
    fire_event,
)

from ...config import conf
from ...repository.utils import use_ac_session
from ...repository.permission import IPermissionRepository


class ServicePermissionImpl(IServicePermission):
    repo = context.require(IPermissionRepository)

    def __init__(self, service: IService):
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

    async def get_permission_by_subject(
        self, *subject: str, trace: bool = True
    ) -> Optional[Permission]:
        async with use_ac_session():
            for sub in subject:
                if trace:
                    for node in self.service.trace():
                        async for p in self.repo.get_permissions(node, sub):
                            return p
                else:
                    async for p in self.repo.get_permissions(self.service, sub):
                        return p

            return None

    async def get_permissions(
        self, *, trace: bool = True
    ) -> AsyncGenerator[Permission, None]:
        async with use_ac_session():
            if trace:
                for node in self.service.trace():
                    async for p in self.repo.get_permissions(node, None):
                        yield p
            else:
                async for p in self.repo.get_permissions(self.service, None):
                    yield p

    @classmethod
    async def get_all_permissions_by_subject(
        cls, *subject: str
    ) -> AsyncGenerator[Permission, None]:
        async with use_ac_session():
            overridden_services = set()
            for sub in subject:
                async for x in cls.repo.get_permissions(None, sub):
                    if x.service not in overridden_services:
                        yield x
                        overridden_services.add(x.service)

    @classmethod
    async def get_all_permissions(cls) -> AsyncGenerator[Permission, None]:
        async with use_ac_session():
            async for x in cls.repo.get_permissions(None, None):
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

    async def _fire_service_change_permission(self, subject: str, allow: bool):
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
            async for x in self.repo.get_permissions(node, subject):
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
        async with use_ac_session():
            ok = await self.repo.set_permission(self.service, subject, allow)

            if ok:
                await self._fire_service_set_permission(subject, allow)
                await self._fire_service_change_permission(subject, allow)

            return ok

    async def remove_permission(self, subject: str) -> bool:
        async with use_ac_session():
            ok = await self.repo.remove_permission(self.service, subject)
            if ok:
                await self._fire_service_remove_permission(subject)

                p = await self.get_permission_by_subject(subject)
                if p is not None:
                    allow = p.allow
                else:
                    allow = conf().access_control_default_permission == "allow"
                await self._fire_service_change_permission(subject, allow)

            return ok

    async def check_permission(self, *subject: str) -> bool:
        async with use_ac_session():
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
