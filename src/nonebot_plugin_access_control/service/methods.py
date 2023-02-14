from typing import Optional

from .base import Service
from .nonebot import NoneBotService
from .plugin import PluginService

_nonebot_service = NoneBotService()


def get_nonebot_service() -> NoneBotService:
    return _nonebot_service


def create_plugin_service(plugin_name: str) -> PluginService:
    return get_nonebot_service().create_plugin_service(plugin_name)


def get_plugin_service(plugin_name: str) -> Optional[PluginService]:
    return get_nonebot_service().get_plugin_service(plugin_name)


def get_service_by_qualified_name(qualified_name: str) -> Optional[Service]:
    return get_nonebot_service().get_service_by_qualified_name(qualified_name)


__all__ = ("get_nonebot_service",
           "create_plugin_service", "get_plugin_service",
           "get_service_by_qualified_name",)
