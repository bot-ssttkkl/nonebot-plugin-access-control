from datetime import timedelta
from typing import AsyncGenerator, TypeVar, Generic, Optional

from ..interface import IService
from ..interface.rate_limit import IServiceRateLimit
from ...models import RateLimitRuleOrm
from ...models.rate_limit import LimitFor

T_Service = TypeVar("T_Service", bound=IService)


class ServiceRateLimitImpl(Generic[T_Service], IServiceRateLimit):
    def __init__(self, service: T_Service):
        self.service = service

    def get_rate_limit_rules(self, subject: Optional[str]) -> AsyncGenerator[RateLimitRuleOrm, None]:
        pass

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int, limit_for: LimitFor):
        pass

    async def remove_rate_limit_rule(self, rule_id: int):
        pass

    async def acquire_token_for_rate_limit(self, *subject: str) -> bool:
        pass
