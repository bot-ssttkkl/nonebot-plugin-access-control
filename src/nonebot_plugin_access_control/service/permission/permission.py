from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nonebot_plugin_access_control.models import PermissionOrm
    from nonebot_plugin_access_control.service import Service


class Permission:
    __slots__ = ('service', 'subject', 'allow')

    def __init__(self, orm: "PermissionOrm", service: "Service"):
        self.service = service
        self.subject = orm.subject
        self.allow = orm.allow
