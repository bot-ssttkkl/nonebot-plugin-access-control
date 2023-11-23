from datetime import datetime
from functools import wraps

from nonebot import logger, Bot
from nonebot.exception import IgnoredException
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import (
    Matcher,
    current_bot,
    current_event,
    current_matcher,
)
from nonebot.message import run_preprocessor
from nonebot_plugin_access_control_api.errors import (
    PermissionDeniedError,
    RateLimitedError,
)
from nonebot_plugin_access_control_api.models.rate_limit import AcquireTokenResult
from nonebot_plugin_access_control_api.service.interface import IService
from nonebot_plugin_access_control_api.service.interface.patcher import IServicePatcher

from ...config import conf


class ServicePatcherImpl(IServicePatcher):
    _matcher_service_mapping: dict[type[Matcher], IService] = {}

    def __init__(self, service: IService):
        self.service = service

    @classmethod
    async def handle_permission_denied(cls, matcher: Matcher):
        if conf().access_control_reply_on_permission_denied_enabled:
            await matcher.send(conf().access_control_reply_on_permission_denied)

    @classmethod
    async def handle_rate_limited(cls, matcher: Matcher, result: AcquireTokenResult):
        if conf().access_control_reply_on_rate_limited_enabled:
            msg = conf().access_control_reply_on_rate_limited
            if msg is None:
                now = datetime.utcnow()
                available_time = result.available_time
                msg = (
                    "使用太频繁了，请稍后再试。"
                    f"下次可用时间：{available_time.timestamp() - now.timestamp():.0f}秒后"
                )
            await matcher.send(msg)

    def patch_matcher(self, matcher: type[Matcher]) -> type[Matcher]:
        self._matcher_service_mapping[matcher] = self.service
        logger.debug(f"patched {matcher}  (with service {self.service.qualified_name})")
        return matcher

    def patch_handler(self, retire_on_throw: bool = False):
        def decorator(func):
            @wraps(func)
            async def wrapped_func(*args, **kwargs):
                bot = current_bot.get()
                event = current_event.get()
                matcher = current_matcher.get()

                if not await self.service.check(
                        bot, event, acquire_rate_limit_token=False
                ):
                    await self.handle_permission_denied(matcher)
                    return

                result = (
                    await self.service.acquire_token_for_rate_limit_receiving_result(
                        bot, event
                    )
                )
                if not result.success:
                    await self.handle_rate_limited(matcher, result)
                    return

                matcher.state["ac_token"] = result.token

                try:
                    return await func(*args, **kwargs)
                except BaseException as e:
                    if retire_on_throw:
                        await result.token.retire()
                    raise e

            return wrapped_func

        return decorator


@run_preprocessor
async def check(matcher: Matcher, bot: Bot, event: Event):
    service = ServicePatcherImpl._matcher_service_mapping.get(type(matcher), None)
    if service is None:
        return

    try:
        await service.check(bot, event, throw_on_fail=True)
    except PermissionDeniedError:
        await ServicePatcherImpl.handle_permission_denied(matcher)
        raise IgnoredException("permission denied (by nonebot_plugin_access_control)")
    except RateLimitedError as e:
        await ServicePatcherImpl.handle_rate_limited(matcher, e.result)
        raise IgnoredException("rate limited (by nonebot_plugin_access_control)")
