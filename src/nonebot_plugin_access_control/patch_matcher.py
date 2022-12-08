from typing import Type

import nonebot
from nonebot import get_driver, logger
from nonebot.internal.matcher import Matcher

from .config import conf
from .service import Service, get_plugin_service


def _contain_rbac_service(matcher: Type[Matcher]):
    for checker in matcher.rule.checkers:
        if isinstance(checker.call, Service):
            return True
    for checker in matcher.permission.checkers:
        if isinstance(checker.call, Service):
            return True
    return False


if conf.access_control_enable_patch:
    @get_driver().on_startup
    def _do_patch():
        for plugin in nonebot.get_loaded_plugins():
            if plugin.name == 'nonebot_plugin_rbac':
                continue

            service = get_plugin_service(plugin.name)
            for matcher in plugin.matcher:
                if not _contain_rbac_service(matcher):
                    matcher.rule &= service
                    logger.debug(f"patched matcher {matcher}")
