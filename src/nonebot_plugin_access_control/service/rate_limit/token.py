from datetime import datetime
from typing import NamedTuple


class RateLimitToken(NamedTuple):
    id: int
    rule_id: int
    user: str
    acquire_time: datetime
