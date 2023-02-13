from abc import ABC, abstractmethod
from datetime import timedelta
from typing import AsyncGenerator, Optional

from nonebot_plugin_access_control.models import RateLimitRuleOrm
from nonebot_plugin_access_control.models.rate_limit import LimitFor


class IServiceRateLimit(ABC):
    @abstractmethod
    def get_rate_limit_rules(self, subject: Optional[str]) -> AsyncGenerator[RateLimitRuleOrm, None]:
        ...

    @abstractmethod
    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int, limit_for: LimitFor):
        ...

    @abstractmethod
    async def remove_rate_limit_rule(self, rule_id: int):
        ...
