from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from nonebot_plugin_access_control.service import Service


class Permission(NamedTuple):
    service: "Service"
    subject: str
    allow: bool
