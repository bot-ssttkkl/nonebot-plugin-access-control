import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, AsyncGenerator, Tuple, overload, Literal, Callable, Awaitable, Type

import nonebot
from nonebot import Bot, logger
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .config import conf
from .errors import RbacError
from .event_bus import on_event, EventType, T_Listener, fire_event
from .models import data_source, PermissionOrm
from .subject import extract_subjects


def _validate_name(name: str) -> bool:
    match_result = re.match(r"[_a-zA-Z]\w*", name)
    return match_result is not None


class Service(ABC):
    def __init__(self):
        self._subservices: Dict[str, Service] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def plugin_service(self) -> "PluginService":
        raise NotImplementedError()

    @property
    @abstractmethod
    def parent(self) -> "Optional[Service]":
        raise NotImplementedError()

    @property
    def qualified_name(self) -> str:
        raise NotImplementedError()

    def patch_matcher(self, matcher: Type[Matcher]) -> Type[Matcher]:
        from .access_control import patch_matcher
        return patch_matcher(matcher, self)

    def create_subservice(self, name: str) -> "Service":
        if name in self.plugin_service._plugin_subservices:
            raise RbacError(f'{name} already exists')

        if not _validate_name(name):
            raise RbacError(f'invalid name: {name}')

        service = SubService(name, self.plugin_service, self)
        self._subservices[name] = service
        self.plugin_service._plugin_subservices[name] = service

        logger.trace(f"created subservice {service.qualified_name}  (parent: {self.qualified_name})")
        return self._subservices[name]

    def get_subservice(self, name: str) -> "Optional[Service]":
        return self._subservices.get(name, None)

    def travel(self):
        sta = [self]
        while len(sta) != 0:
            top, sta = sta[-1], sta[:-1]
            yield top
            sta.extend(top._subservices.values())

    def find(self, name: str) -> "Optional[Service]":
        for s in self.travel():
            if s.name == name:
                return s
        return None

    def on_allow_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_allow_permission,
                        lambda kwargs: kwargs["service"] == self,
                        func)

    def on_deny_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_deny_permission,
                        lambda kwargs: kwargs["service"] == self,
                        func)

    def on_remove_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_remove_permission,
                        lambda kwargs: kwargs["service"] == self,
                        func)

    async def _get_permission(self, node_permission_getter: Callable[["Service", AsyncSession],
                                                                     Awaitable[Optional[bool]]]) -> Optional[bool]:
        async with data_source.start_session() as session:
            v = self
            allow = None

            while v is not None:
                p = await node_permission_getter(v, session)
                if p is not None:
                    allow = p
                    break
                else:
                    v = v.parent

            return allow

    @overload
    async def get_permission(self, subject: str) -> bool:
        ...

    @overload
    async def get_permission(self, subject: str, with_default: Literal[True]) -> bool:
        ...

    @overload
    async def get_permission(self, subject: str, with_default: Literal[False]) -> Optional[bool]:
        ...

    async def get_permission(self, subject: str, with_default: bool = True) -> Optional[bool]:
        async def _get_permission(node: "Service", session: AsyncSession) -> Optional[bool]:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.plugin == node.plugin_service.name,
                           PermissionOrm.service == node.name,
                           PermissionOrm.subject == subject))
            p = (await session.execute(stmt)).scalar_one_or_none()
            if p is not None:
                return p.allow
            else:
                return None

        allow = await self._get_permission(_get_permission)
        if allow is None and with_default:
            allow = conf.access_control_default_permission == 'allow'
        return allow

    async def get_permissions(self) -> AsyncGenerator[Tuple[str, bool], None]:
        async with data_source.start_session() as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.plugin == self.plugin_service.name,
                           PermissionOrm.service == self.name))
            async for p in await session.stream_scalars(stmt):
                yield p.subject, p.allow

    async def _fire_service_set_permission(self, subject: str, allow: bool):
        if allow:
            event_type = EventType.service_allow_permission
        else:
            event_type = EventType.service_deny_permission

        for node in self.travel():
            await fire_event(event_type, {
                "service": node,
                "subject": subject
            })

    async def set_permission(self, subject: str, allow: bool):
        async with data_source.start_session() as session:
            stmt = (insert(PermissionOrm)
                    .values(plugin=self.plugin_service.name,
                            service=self.name,
                            subject=subject,
                            allow=allow)
                    .on_conflict_do_update(set_={PermissionOrm.allow: allow}))
            row_count = (await session.execute(stmt)).rowcount
            ok = row_count == 1

            if ok:
                await session.commit()
                await self._fire_service_set_permission(subject, allow)

            return ok

    async def _fire_service_remove_permission(self, subject: str):
        for node in self.travel():
            await fire_event(EventType.service_remove_permission, {
                "service": node,
                "subject": subject
            })

        await self._fire_service_set_permission(subject, conf.access_control_default_permission == 'allow')

    async def remove_permission(self, subject: str) -> bool:
        async with data_source.start_session() as session:
            stmt = (delete(PermissionOrm)
                    .where(PermissionOrm.plugin == self.plugin_service.name,
                           PermissionOrm.service == self.name,
                           PermissionOrm.subject == subject))
            row_count = (await session.execute(stmt)).rowcount
            ok = row_count == 1

            if ok:
                await session.commit()
                await self._fire_service_remove_permission(subject)

            return ok

    async def __call__(self, bot: Bot, event: Event) -> bool:
        subjects = extract_subjects(bot, event)
        for sub in subjects:
            p = await self.get_permission(sub, False)
            if p is not None:
                return p

        return conf.access_control_default_permission == 'allow'


class PluginService(Service):
    def __init__(self, name: str, auto_created: bool):
        super().__init__()
        self._name = name
        self._plugin_subservices = {}

        self.auto_created = auto_created

    @property
    def name(self) -> str:
        return self._name

    @property
    def plugin_service(self) -> "PluginService":
        return self

    @property
    def parent(self) -> "Optional[Service]":
        return None

    @property
    def qualified_name(self) -> str:
        return self.name


class SubService(Service):
    def __init__(self, name: str, plugin_service: PluginService, parent: Optional[Service] = None):
        super().__init__()
        self._name = name
        self._plugin_service = plugin_service
        self._parent = parent

    @property
    def name(self) -> str:
        return self._name

    @property
    def plugin_service(self) -> "PluginService":
        return self._plugin_service

    @property
    def parent(self) -> "Optional[Service]":
        return self._parent

    @property
    def qualified_name(self) -> str:
        return f"{self.plugin_service.name}.{self.name}"


_plugin_services: Dict[str, PluginService] = {}


def _create_plugin_service(plugin_name: str, auto_create: bool) -> PluginService:
    if plugin_name in _plugin_services:
        raise ValueError(f"{plugin_name} already created")

    service = PluginService(plugin_name, auto_create)
    _plugin_services[plugin_name] = service
    logger.trace(f"created plugin service {service.qualified_name}")
    return service


def create_plugin_service(plugin_name: str) -> PluginService:
    return _create_plugin_service(plugin_name, False)


def get_plugin_service(plugin_name: str, auto_create: bool = True) -> Optional[PluginService]:
    if plugin_name in _plugin_services:
        return _plugin_services[plugin_name]
    elif auto_create:
        plugin = nonebot.get_plugin(plugin_name)
        if plugin is not None:
            return _create_plugin_service(plugin_name, auto_create)

    return None


async def get_services_by_subject(subject: str) -> AsyncGenerator[Tuple[Service, bool], None]:
    async with data_source.start_session() as session:
        stmt = select(PermissionOrm).where(PermissionOrm.subject == subject)
        async for x in await session.stream_scalars(stmt):
            service = get_plugin_service(x.plugin)
            if service is not None:
                service = service.find(x.service)
                yield service, x.allow


__all__ = ("create_plugin_service", "get_plugin_service", "get_services_by_subject",
           "Service", "PluginService", "SubService")
