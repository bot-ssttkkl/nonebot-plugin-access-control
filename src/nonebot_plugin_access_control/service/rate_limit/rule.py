from datetime import timedelta
from typing import TYPE_CHECKING

from nonebot_plugin_access_control.models import RateLimitRuleOrm

if TYPE_CHECKING:
    from nonebot_plugin_access_control.service import Service


class RateLimitRule:
    def __init__(self, orm: RateLimitRuleOrm, service: "Service"):
        self.orm = orm
        self._service = service

    @property
    def id(self) -> int:
        return self.orm.id

    @property
    def service(self) -> "Service":
        return self._service

    @property
    def subject(self) -> str:
        return self.orm.subject

    @property
    def time_span(self) -> timedelta:
        return timedelta(seconds=self.orm.time_span)

    @property
    def limit(self) -> int:
        return self.orm.limit
