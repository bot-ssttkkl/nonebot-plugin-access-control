from datetime import timedelta
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from nonebot_plugin_access_control.service import Service


class RateLimitRule(NamedTuple):
    id: str
    service: "Service"
    subject: str
    time_span: timedelta
    limit: int
    overwrite: bool
