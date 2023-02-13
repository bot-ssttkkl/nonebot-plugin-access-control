from abc import ABC
from typing import Optional, AsyncGenerator, Tuple, Generic, TypeVar, Type, Callable, Awaitable

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from typing_extensions import overload, Literal

from .interface import IService
from ..config import conf
from ..event_bus import T_Listener, on_event, EventType, fire_event
from ..models import PermissionOrm
from ..subject import extract_subjects

T_ParentService = TypeVar('T_ParentService', bound=Optional["Service"], covariant=True)
T_ChildService = TypeVar('T_ChildService', bound="Service", covariant=True)


class Service(Generic[T_ParentService, T_ChildService],
              IService["Service", T_ParentService, T_ChildService],
              ABC):
    def __repr__(self):
        return self.qualified_name

    def travel(self):
        sta = [self]
        while len(sta) != 0:
            top, sta = sta[-1], sta[:-1]
            yield top
            sta.extend(top.children)

    def find(self, name: str) -> Optional["Service"]:
        for s in self.travel():
            if s.name == name:
                return s
        return None

    def patch_matcher(self, matcher: Type[Matcher]) -> Type[Matcher]:
        from ..access_control import patch_matcher
        return patch_matcher(matcher, self)

    @overload
    async def check(self, bot: Bot, event: Event, with_default: Literal[True] = True) -> bool:
        ...

    @overload
    async def check(self, bot: Bot, event: Event, with_default: bool) -> Optional[bool]:
        ...

    async def check(self, bot: Bot, event: Event, with_default: bool = True) -> Optional[bool]:
        subjects = extract_subjects(bot, event)
        return await self.get_permission(*subjects, with_default=with_default)

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
        v: Optional[Service] = self
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
    async def get_permission(self, *subject: str, with_default: bool) -> Optional[bool]:
        ...

    async def get_permission(self, *subject: str, with_default: bool = True) -> Optional[bool]:
        async def node_permission_getter(node: Service, sub: str, session: AsyncSession) -> Optional[bool]:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == node.qualified_name,
                           PermissionOrm.subject == sub))
            p = (await session.execute(stmt)).scalar_one_or_none()
            if p is not None:
                return p.allow
            else:
                return None

        async with AsyncSession(get_engine()) as session:
            for sub in subject:
                allow = await self._get_permission(lambda node, session: node_permission_getter(node, sub, session),
                                                   session)
                if allow is not None:
                    return allow

            if with_default:
                return conf.access_control_default_permission == 'allow'
            else:
                return None

    async def get_permissions(self) -> AsyncGenerator[Tuple[str, bool], None]:
        async with AsyncSession(get_engine()) as session:
            stmt = (select(PermissionOrm)
                    .where(PermissionOrm.service == self.qualified_name))
            async for p in await session.stream_scalars(stmt):
                yield p.subject, p.allow

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
        async with AsyncSession(get_engine()) as session:
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
        async with AsyncSession(get_engine()) as session:
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
