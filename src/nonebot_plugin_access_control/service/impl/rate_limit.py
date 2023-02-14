from datetime import timedelta
from typing import AsyncGenerator, TypeVar, Generic, Optional

from nonebot import logger

from ..interface import IService
from ..interface.rate_limit import IServiceRateLimit
from ...rate_limit import get_rate_limit_rules, RateLimitRule
from ...rate_limit.repo import add_rate_limit_rule, remove_rate_limit_rule

T_Service = TypeVar("T_Service", bound=IService)


class ServiceRateLimitImpl(Generic[T_Service], IServiceRateLimit):
    def __init__(self, service: T_Service):
        self.service = service

    async def get_rate_limit_rules(self, subject: Optional[str]) -> AsyncGenerator[RateLimitRule, None]:
        async for rule in get_rate_limit_rules(self.service.qualified_name, subject):
            yield rule

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int):
        await add_rate_limit_rule(self.service.qualified_name, subject, time_span, limit)

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: int):
        await remove_rate_limit_rule(rule_id)

    async def acquire_token_for_rate_limit(self, *subject: str, user: str) -> bool:
        tokens = []

        for sub in subject:
            acquired = False

            for node in self.service.trace():
                async for rule in get_rate_limit_rules(node.qualified_name, sub):
                    token = await rule.acquire_token(user)
                    if token is not None:
                        logger.trace(f"[rate limit] token acquired for rule {rule.orm.id} "
                                     f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                        tokens.append(token)
                        acquired = True
                    else:
                        logger.trace(f"[rate limit] limit reached for rule {rule.orm.id} "
                                     f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                        for t in tokens:
                            await t.retire()
                            logger.trace(f"[rate limit] token retired for rule {rule.orm.id} "
                                         f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                        return False

            # 优先级高的subject若设置了rule，则不再检查优先级低的subject
            if acquired:
                return True

        # 未设置rule
        return True
