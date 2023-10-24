from abc import ABC
from datetime import timedelta, datetime
from functools import wraps
from typing import Optional, Generic, TypeVar
from collections.abc import AsyncGenerator

from nonebot import Bot, logger
from nonebot.exception import IgnoredException
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import (
    Matcher,
    current_bot,
    current_event,
    current_matcher,
)
from nonebot.message import run_preprocessor

from .impl.permission import ServicePermissionImpl
from .impl.rate_limit import ServiceRateLimitImpl
from .interface import IService
from .interface.rate_limit import AcquireTokenResult, IRateLimitToken
from .permission import Permission
from .rate_limit import RateLimitRule
from ..config import conf
from ..errors import AccessControlError, PermissionDeniedError, RateLimitedError
from ..event_bus import T_Listener
from ..subject import extract_subjects

T_ParentService = TypeVar("T_ParentService", bound=Optional["Service"], covariant=True)
T_ChildService = TypeVar("T_ChildService", bound="Service", covariant=True)


class Service(
    Generic[T_ParentService, T_ChildService],
    IService["Service", T_ParentService, T_ChildService],
    ABC,
):
    _matcher_service_mapping: dict[type[Matcher], "Service"] = {}

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

    def patch_matcher(self, matcher: type[Matcher]) -> type[Matcher]:
        self._matcher_service_mapping[matcher] = self
        logger.debug(f"patched {matcher}  (with service {self.qualified_name})")
        return matcher

    def patch_handler(self, retire_on_throw: bool = False):
        def decorator(func):
            @wraps(func)
            async def wrapped_func(*args, **kwargs):
                bot = current_bot.get()
                event = current_event.get()

                if not await self.check(bot, event, acquire_rate_limit_token=False):
                    raise PermissionDeniedError()

                result = await self.acquire_token_for_rate_limit_receiving_result(
                    bot, event
                )
                if not result.success:
                    raise RateLimitedError(result)

                matcher = current_matcher.get()
                matcher.state["ac_token"] = result.token

                try:
                    return await func(*args, **kwargs)
                except BaseException as e:
                    if retire_on_throw:
                        await result.token.retire()
                    raise e

            return wrapped_func

        return decorator

    async def check(
        self,
        bot: Bot,
        event: Event,
        *,
        acquire_rate_limit_token: bool = True,
        throw_on_fail: bool = False,
    ) -> bool:
        subjects = extract_subjects(bot, event)
        return await self.check_by_subject(
            *subjects,
            acquire_rate_limit_token=acquire_rate_limit_token,
            throw_on_fail=throw_on_fail,
        )

    async def check_by_subject(
        self,
        *subjects: str,
        acquire_rate_limit_token: bool = True,
        throw_on_fail: bool = False,
    ) -> bool:
        if not throw_on_fail:
            try:
                await self.check_by_subject(
                    *subjects,
                    acquire_rate_limit_token=acquire_rate_limit_token,
                    throw_on_fail=True,
                )
                return True
            except AccessControlError:
                return False

        allow = await self.check_permission(*subjects)
        if not allow:
            raise PermissionDeniedError()

        if acquire_rate_limit_token:
            result = (
                await self.acquire_token_for_rate_limit_by_subjects_receiving_result(
                    *subjects
                )
            )
            if not result.success:
                raise RateLimitedError(result)

    def on_set_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_set_permission(func)

    def on_change_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_change_permission(func)

    def on_remove_permission(self, func: Optional[T_Listener] = None):
        return self._permission_impl.on_remove_permission(func)

    async def get_permission_by_subject(
        self, *subject: str, trace: bool = True
    ) -> Optional[Permission]:
        return await self._permission_impl.get_permission_by_subject(
            *subject, trace=trace
        )

    def get_permissions(
        self, *, trace: bool = True
    ) -> AsyncGenerator[Permission, None]:
        return self._permission_impl.get_permissions(trace=trace)

    @classmethod
    def get_all_permissions_by_subject(
        cls, *subject: str
    ) -> AsyncGenerator[Permission, None]:
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

    def get_rate_limit_rules_by_subject(
        self, *subject: str, trace: bool = True
    ) -> AsyncGenerator[RateLimitRule, None]:
        return self._rate_limit_impl.get_rate_limit_rules_by_subject(
            *subject, trace=trace
        )

    def get_rate_limit_rules(
        self, *, trace: bool = True
    ) -> AsyncGenerator[RateLimitRule, None]:
        return self._rate_limit_impl.get_rate_limit_rules(trace=trace)

    @classmethod
    def get_all_rate_limit_rules_by_subject(
        cls, *subject: str
    ) -> AsyncGenerator[RateLimitRule, None]:
        return ServiceRateLimitImpl.get_all_rate_limit_rules_by_subject(*subject)

    @classmethod
    def get_all_rate_limit_rules(cls) -> AsyncGenerator[RateLimitRule, None]:
        return ServiceRateLimitImpl.get_all_rate_limit_rules()

    async def add_rate_limit_rule(
        self, subject: str, time_span: timedelta, limit: int, overwrite: bool = False
    ) -> RateLimitRule:
        return await self._rate_limit_impl.add_rate_limit_rule(
            subject, time_span, limit, overwrite
        )

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: str) -> bool:
        return await ServiceRateLimitImpl.remove_rate_limit_rule(rule_id)

    async def acquire_token_for_rate_limit(
        self, bot: Bot, event: Event
    ) -> Optional[IRateLimitToken]:
        return await self._rate_limit_impl.acquire_token_for_rate_limit(bot, event)

    async def acquire_token_for_rate_limit_receiving_result(
        self, bot: Bot, event: Event
    ) -> AcquireTokenResult:
        return (
            await self._rate_limit_impl.acquire_token_for_rate_limit_receiving_result(
                bot, event
            )
        )

    async def acquire_token_for_rate_limit_by_subjects(
        self, *subject: str
    ) -> Optional[IRateLimitToken]:
        return await self._rate_limit_impl.acquire_token_for_rate_limit_by_subjects(
            *subject
        )

    async def acquire_token_for_rate_limit_by_subjects_receiving_result(
        self, *subject: str
    ) -> AcquireTokenResult:
        return await self._rate_limit_impl.acquire_token_for_rate_limit_by_subjects_receiving_result(
            *subject
        )

    @classmethod
    async def clear_rate_limit_tokens(cls):
        return await ServiceRateLimitImpl.clear_rate_limit_tokens()


@run_preprocessor
async def check(matcher: Matcher, bot: Bot, event: Event):
    service = Service._matcher_service_mapping.get(type(matcher), None)
    if service is None:
        return

    try:
        await service.check(bot, event, throw_on_fail=True)
    except PermissionDeniedError:
        if conf().access_control_reply_on_permission_denied_enabled:
            await matcher.send(conf().access_control_reply_on_permission_denied)
        raise IgnoredException("permission denied (by nonebot_plugin_access_control)")
    except RateLimitedError as e:
        if conf().access_control_reply_on_rate_limited_enabled:
            msg = conf().access_control_reply_on_rate_limited
            if msg is None:
                now = datetime.utcnow()
                available_time = e.result.available_time
                msg = "使用太频繁了，请稍后再试。" "下次可用时间：{:.0f}秒后".format(
                    available_time.timestamp() - now.timestamp()
                )
            await matcher.send(msg)
        raise IgnoredException("rate limited (by nonebot_plugin_access_control)")
