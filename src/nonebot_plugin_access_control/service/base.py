from abc import ABC
from datetime import timedelta
from typing import Optional, Generic, TypeVar, Type, AsyncGenerator, Tuple

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from typing_extensions import overload, Literal

from .impl.permission import ServicePermissionImpl
from .impl.rate_limit import ServiceRateLimitImpl
from .interface import IService
from ..event_bus import T_Listener
from ..models.rate_limit import LimitFor, RateLimitRuleOrm
from ..subject import extract_subjects

T_ParentService = TypeVar('T_ParentService', bound=Optional["Service"], covariant=True)
T_ChildService = TypeVar('T_ChildService', bound="Service", covariant=True)


class Service(Generic[T_ParentService, T_ChildService],
              IService["Service", T_ParentService, T_ChildService],
              ABC):
    def __init__(self):
        self._permission_impl = ServicePermissionImpl[Service](self)
        self._rate_limit_impl = ServiceRateLimitImpl[Service](self)

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
        return self._permission_impl.on_set_permission(func)

    def on_change_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_change_permission(func)

    def on_remove_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_remove_permission(func)

    @overload
    async def get_permission(self, *subject: str, with_default: Literal[True] = True) -> bool:
        ...

    @overload
    async def get_permission(self, *subject: str, with_default: bool) -> Optional[bool]:
        ...

    async def get_permission(self, *subject: str, with_default: bool = True) -> Optional[bool]:
        return await self._permission_impl.get_permission(*subject, with_default=with_default)

    def get_permissions(self) -> AsyncGenerator[Tuple[str, bool], None]:
        return self._permission_impl.get_permissions()

    async def set_permission(self, subject: str, allow: bool):
        return await self._permission_impl.set_permission(subject, allow)

    async def remove_permission(self, subject: str) -> bool:
        return await self._permission_impl.remove_permission(subject)

    def get_rate_limit_rules(self, subject: Optional[str]) -> AsyncGenerator[RateLimitRuleOrm, None]:
        return self._rate_limit_impl.get_rate_limit_rules(subject)

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int, limit_for: LimitFor):
        return await self._rate_limit_impl.add_rate_limit_rule(subject, time_span, limit, limit_for)

    async def remove_rate_limit_rule(self, rule_id: int):
        return await self._rate_limit_impl.remove_rate_limit_rule(rule_id)

    async def acquire_token_for_rate_limit(self, *subject: str) -> bool:
        return await self._rate_limit_impl.acquire_token_for_rate_limit(*subject)
