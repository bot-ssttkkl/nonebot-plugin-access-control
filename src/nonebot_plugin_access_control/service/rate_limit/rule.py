from datetime import timedelta
from typing import TYPE_CHECKING

from nonebot_plugin_access_control.models import RateLimitRuleOrm

if TYPE_CHECKING:
    from nonebot_plugin_access_control.service import Service


class RateLimitRule:
    __slots__ = ('id', 'service', 'subject', 'time_span', 'limit')

    def __init__(self, orm: RateLimitRuleOrm, service: "Service"):
        self.id = orm.id
        self.service = service
        self.subject = orm.subject
        self.time_span = timedelta(seconds=orm.time_span)
        self.limit = orm.limit
