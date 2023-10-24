from typing import Optional, TYPE_CHECKING

from .nonebot import NoneBotService

if TYPE_CHECKING:
    from .base import Service
    from .plugin import PluginService

_nonebot_service = NoneBotService()


def get_nonebot_service() -> "NoneBotService":
    return _nonebot_service


def create_plugin_service(plugin_name: str) -> "PluginService":
    return get_nonebot_service().create_plugin_service(plugin_name)


def get_plugin_service(
    plugin_name: str, *, raise_on_not_exists: bool = False
) -> Optional["PluginService"]:
    return get_nonebot_service().get_plugin_service(
        plugin_name, raise_on_not_exists=raise_on_not_exists
    )


def get_service_by_qualified_name(
    qualified_name: str, *, raise_on_not_exists: bool = False
) -> Optional["Service"]:
    return get_nonebot_service().get_service_by_qualified_name(
        qualified_name, raise_on_not_exists=raise_on_not_exists
    )


__all__ = (
    "get_nonebot_service",
    "create_plugin_service",
    "get_plugin_service",
    "get_service_by_qualified_name",
)
