from datetime import timedelta
from typing import Optional, Protocol
from collections.abc import AsyncGenerator

from nonebot_plugin_access_control_api.service.interface import IService
from nonebot_plugin_access_control_api.models.rate_limit import RateLimitRule

from ..orm.rate_limit import RateLimitRuleOrm


class IRateLimitRepository(Protocol):
    async def get_rules_by_subject(
        self, service: Optional[IService], subject: Optional[str]
    ) -> AsyncGenerator[RateLimitRuleOrm, None]:
        raise NotImplementedError()
        yield RateLimitRuleOrm()  # noqa

    async def add_rate_limit_rule(
        self,
        service: IService,
        subject: str,
        time_span: timedelta,
        limit: int,
        overwrite: bool = False,
    ) -> RateLimitRule:
        raise NotImplementedError()

    async def remove_rate_limit_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        raise NotImplementedError()
