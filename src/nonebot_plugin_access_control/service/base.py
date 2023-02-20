from abc import ABC
from datetime import timedelta
from typing import Optional, Generic, TypeVar, Type, AsyncGenerator

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher

from .impl.permission import ServicePermissionImpl
from .impl.rate_limit import ServiceRateLimitImpl
from .interface import IService
from .permission import Permission
from .rate_limit import RateLimitRule
from ..errors import AccessControlError, PermissionDeniedError, RateLimitedError
from ..event_bus import T_Listener
from ..subject import union_subject_extractor

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

    def trace(self):
        node = self
        while node is not None:
            yield node
            node = node.parent

    def get_child(self, name: str) -> Optional["Service"]:
        for s in self.children:
            if s.name == name:
                return s
        return None

    def patch_matcher(self, matcher: Type[Matcher]) -> Type[Matcher]:
        from ..access_control import patch_matcher
        return patch_matcher(matcher, self)

    async def check(self, bot: Bot, event: Event,
                    *, acquire_rate_limit_token: bool = True,
                    throw_on_fail: bool = False) -> bool:
        subjects = union_subject_extractor.extract(bot, event)
        return await self.check_by_subject(*subjects,
                                           acquire_rate_limit_token=acquire_rate_limit_token,
                                           throw_on_fail=throw_on_fail)

    async def check_by_subject(self, *subjects: str,
                               acquire_rate_limit_token: bool = True,
                               throw_on_fail: bool = False) -> bool:
        if not throw_on_fail:
            try:
                await self.check_by_subject(*subjects,
                                            acquire_rate_limit_token=acquire_rate_limit_token,
                                            throw_on_fail=True)
                return True
            except AccessControlError:
                return False

        allow = await self.check_permission(*subjects)
        if not allow:
            raise PermissionDeniedError()

        if acquire_rate_limit_token:
            user_id = subjects[0]
            allow = await self.acquire_token_for_rate_limit(*subjects, user=user_id)

            if not allow:
                raise RateLimitedError()

    def on_set_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_set_permission(func)

    def on_change_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_change_permission(func)

    def on_remove_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_remove_permission(func)

    async def get_permission_by_subject(self, *subject: str, trace: bool = True) -> Optional[Permission]:
        return await self._permission_impl.get_permission_by_subject(*subject, trace=trace)

    def get_permissions(self, *, trace: bool = True) -> AsyncGenerator[Permission, None]:
        return self._permission_impl.get_permissions(trace=trace)

    @classmethod
    def get_all_permissions_by_subject(cls, *subject: str) -> AsyncGenerator[Permission, None]:
        return ServicePermissionImpl.get_all_permissions_by_subject(*subject)

    @classmethod
    def get_all_permissions(cls) -> AsyncGenerator[Permission, None]:
        return ServicePermissionImpl.get_all_permissions()

    async def set_permission(self, subject: str, allow: bool) -> bool:
        return await self._permission_impl.set_permission(subject, allow)

    async def remove_permission(self, subject: str) -> bool:
        return await self._permission_impl.remove_permission(subject)

    async def check_permission(self, *subject: str) -> bool:
        return await self._permission_impl.check_permission(*subject)

    def on_add_rate_limit_rule(self, func: Optional[T_Listener] = None):
        return self._rate_limit_impl.on_add_rate_limit_rule(func)

    def on_remove_rate_limit_rule(self, func: Optional[T_Listener] = None):
        return self._rate_limit_impl.on_remove_rate_limit_rule(func)

    def get_rate_limit_rules_by_subject(self, *subject: str,
                                        trace: bool = True) -> AsyncGenerator[RateLimitRule, None]:
        return self._rate_limit_impl.get_rate_limit_rules_by_subject(*subject, trace=trace)

    def get_rate_limit_rules(self, *, trace: bool = True) -> AsyncGenerator[RateLimitRule, None]:
        return self._rate_limit_impl.get_rate_limit_rules(trace=trace)

    @classmethod
    def get_all_rate_limit_rules_by_subject(cls, *subject: str) -> AsyncGenerator[RateLimitRule, None]:
        return ServiceRateLimitImpl.get_all_rate_limit_rules_by_subject(*subject)

    @classmethod
    def get_all_rate_limit_rules(cls) -> AsyncGenerator[RateLimitRule, None]:
        return ServiceRateLimitImpl.get_all_rate_limit_rules()

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta,
                                  limit: int, overwrite: bool = False) -> RateLimitRule:
        return await self._rate_limit_impl.add_rate_limit_rule(subject, time_span, limit, overwrite)

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: str) -> bool:
        return await ServiceRateLimitImpl.remove_rate_limit_rule(rule_id)

    async def acquire_token_for_rate_limit(self, *subject: str, user: str) -> bool:
        return await self._rate_limit_impl.acquire_token_for_rate_limit(*subject, user=user)

    @classmethod
    async def clear_rate_limit_tokens(cls):
        return await ServiceRateLimitImpl.clear_rate_limit_tokens()
