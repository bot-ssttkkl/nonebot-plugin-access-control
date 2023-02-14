from typing import Type, Dict

import nonebot
from nonebot import get_driver, logger, Bot
from nonebot.exception import IgnoredException
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.message import run_preprocessor

from .config import conf
from .errors import AccessControlError
from .service import Service, get_nonebot_service

_matcher_service_mapping: Dict[Type[Matcher], Service] = {}


def patch_matcher(matcher: Type[Matcher], service: Service) -> Type[Matcher]:
    _matcher_service_mapping[matcher] = service
    logger.debug(f"patched {matcher}  (with service {service.qualified_name})")
    return matcher


@run_preprocessor
async def check(matcher: Matcher, bot: Bot, event: Event):
    service = _matcher_service_mapping.get(type(matcher), None)
    if service is None:
        return

    try:
        await service.check_or_throw(bot, event)
    except AccessControlError as e:
        raise IgnoredException("permission denied by nonebot_plugin_access_control")


if conf.access_control_auto_patch_enabled:
    @get_driver().on_startup
    def _():
        nonebot_service = get_nonebot_service()

        for plugin in nonebot.get_loaded_plugins():
            if plugin.name == 'nonebot_plugin_access_control' or plugin.name in conf.access_control_auto_patch_ignore:
                continue

            service = nonebot_service.get_or_create_plugin_service(plugin.name)
            if service.auto_created:
                for matcher in plugin.matcher:
                    patch_matcher(matcher, service)
