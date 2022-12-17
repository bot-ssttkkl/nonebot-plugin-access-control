import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, AsyncGenerator, Tuple, overload, Literal, Callable, Awaitable, Type, Collection

import nonebot
from nonebot import Bot, logger
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

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

    def __repr__(self):
        return self.qualified_name

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def qualified_name(self) -> str:
        if self.parent is None:
            return self.name
        else:
            return self.parent.qualified_name + "." + self.name

    @property
    @abstractmethod
    def plugin_service(self) -> "PluginService":
        raise NotImplementedError()

    @property
    @abstractmethod
    def parent(self) -> "Optional[Service]":
        raise NotImplementedError()

    @property
    def children(self) -> "Collection[Service]":
        return self._subservices.values()

    def create_subservice(self, name: str) -> "Service":
        if not _validate_name(name):
            raise RbacError(f'invalid name: {name}')

        if name in self._subservices:
            raise RbacError(f'subservice already exists: {self.qualified_name}.{name}')

        service = SubService(name, self.plugin_service, self)
        self._subservices[name] = service

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

    def patch_matcher(self, matcher: Type[Matcher]) -> Type[Matcher]:
        from .access_control import patch_matcher
        return patch_matcher(matcher, self)

    def on_set_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_set_permission,
                        lambda service: service == self,
                        func)

    def on_change_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_change_permission,
                        lambda service: service == self,
                        func)

    def on_remove_permission(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_remove_permission,
                        lambda service: service == self,
                        func)

    async def _get_permission(self, node_permission_getter: Callable[["Service", AsyncSession],
                                                                     Awaitable[Optional[bool]]],
                              session: AsyncSession) -> Optional[bool]:
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
    async def get_permission(self, *subject: str, with_default: Literal[True] = True) -> bool:
        ...

    @overload
    async def get_permission(self, *subject: str, with_default: Literal[False]) -> Optional[bool]:
        ...

    async def get_permission(self, *subject: str, with_default: bool = True) -> Optional[bool]:
        async def _get_permission(node: "Service", sub: str, session: AsyncSession) -> Optional[bool]:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == node.qualified_name,
                           PermissionOrm.subject == sub))
            p = (await session.execute(stmt)).scalar_one_or_none()
            if p is not None:
                return p.allow
            else:
                return None

        async with data_source.start_session() as session:
            for sub in subject:
                allow = await self._get_permission(lambda node, session: _get_permission(node, sub, session), session)
                if allow is not None:
                    return allow

            if with_default:
                return conf.access_control_default_permission == 'allow'
            else:
                return None

    async def get_permissions(self) -> AsyncGenerator[Tuple[str, bool], None]:
        async with data_source.start_session() as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.qualified_name))
            async for p in await session.stream_scalars(stmt):
                yield p.subject, p.allow

    @overload
    async def check(self, bot: Bot, event: Event, with_default: Literal[True] = True) -> bool:
        ...

    @overload
    async def check(self, bot: Bot, event: Event, with_default: Literal[False]) -> Optional[bool]:
        ...

    async def check(self, bot: Bot, event: Event, with_default: bool = True) -> Optional[bool]:
        subjects = extract_subjects(bot, event)
        return await self.get_permission(*subjects, with_default=with_default)

    async def _fire_service_set_permission(self, subject: str, allow: bool):
        await fire_event(EventType.service_set_permission, {
            "service": self,
            "subject": subject,
            "allow": allow,
        })

    async def _fire_service_remove_permission(self, subject: str):
        await fire_event(EventType.service_remove_permission, {
            "service": self,
            "subject": subject
        })

    async def _fire_service_change_permission(self, subject: str, allow: bool, session: AsyncSession):
        await fire_event(EventType.service_change_permission, {
            "service": self,
            "subject": subject,
            "allow": allow,
        })

        async def dfs(node: Service):
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

        for c in self.children:
            await dfs(c)

    async def set_permission(self, subject: str, allow: bool):
        async with data_source.start_session() as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.qualified_name,
                           PermissionOrm.subject == subject))
            p = (await session.execute(stmt)).scalar_one_or_none()
            if p is None:
                p = PermissionOrm(service=self.qualified_name,
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
        async with data_source.start_session() as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.qualified_name,
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


class PluginService(Service):
    def __init__(self, name: str, auto_created: bool):
        super().__init__()
        self._name = name
        self._auto_created = auto_created

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
    def auto_created(self) -> bool:
        return self._auto_created


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


def get_service_by_qualified_name(qualified_name: str, auto_create_plugin_service: bool = True) -> Optional[Service]:
    seg = qualified_name.split('.')
    service = get_plugin_service(seg[0], auto_create_plugin_service)
    for i in range(1, len(seg)):
        if service is None:
            return None
        service = service.get_subservice(seg[i])
    return service


async def get_services_by_subject(subject: str) -> AsyncGenerator[Tuple[Service, bool], None]:
    async with data_source.start_session() as session:
        stmt = select(PermissionOrm).where(PermissionOrm.subject == subject)
        async for x in await session.stream_scalars(stmt):
            service = get_service_by_qualified_name(x.service)
            yield service, x.allow


__all__ = ("create_plugin_service", "get_plugin_service", "get_services_by_subject",
           "Service", "PluginService", "SubService")
