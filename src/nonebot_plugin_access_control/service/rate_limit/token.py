from datetime import datetime
from typing import NamedTuple


class RateLimitSingleToken(NamedTuple):
    id: int
    rule_id: str
    user: str
    acquire_time: datetime
    expire_time: datetime
