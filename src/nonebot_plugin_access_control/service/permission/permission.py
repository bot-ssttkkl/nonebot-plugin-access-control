from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nonebot_plugin_access_control.models import PermissionOrm
    from nonebot_plugin_access_control.service import Service


class Permission:
    def __init__(self, orm: "PermissionOrm", service: "Service"):
        self.orm = orm
        self._service = service

    @property
    def service(self) -> "Service":
        return self._service

    @property
    def subject(self) -> str:
        return self.orm.subject

    @property
    def allow(self) -> bool:
        return self.orm.allow
