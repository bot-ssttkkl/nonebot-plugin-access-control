from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional, Protocol, NamedTuple

if TYPE_CHECKING:
    from ..service.interface.service import IService


class RateLimitRule(NamedTuple):
    id: str
    service: "IService"
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


class IRateLimitToken(Protocol):
    async def retire(self):
        ...


class AcquireTokenResult(NamedTuple):
    success: bool
    token: Optional[IRateLimitToken] = None
    violating: Optional[Sequence[RateLimitRule]] = None
    available_time: Optional[datetime] = None
