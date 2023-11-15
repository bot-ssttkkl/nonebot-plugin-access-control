from datetime import datetime, timedelta
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from ..service import Service


class RateLimitRule(NamedTuple):
    id: str
    service: "Service"
    subject: str
    time_span: timedelta
    limit: int
    overwrite: bool


class RateLimitSingleToken(NamedTuple):
    id: int
    rule_id: str
    user: str
    acquire_time: datetime
    expire_time: datetime
