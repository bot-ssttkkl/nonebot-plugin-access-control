from datetime import timedelta, datetime, timezone
from typing import AsyncGenerator, TypeVar, Generic, Optional

from nonebot import logger, require
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..interface import IService
from ..interface.rate_limit import IServiceRateLimit
from ..rate_limit import RateLimitRule
from ...models import RateLimitTokenOrm, RateLimitRuleOrm

T_Service = TypeVar("T_Service", bound=IService)


class ServiceRateLimitImpl(Generic[T_Service], IServiceRateLimit):
    def __init__(self, service: T_Service):
        self.service = service

    @staticmethod
    async def _get_rules_by_subject(service: T_Service,
                                    subject: Optional[str]) -> AsyncGenerator[RateLimitRule, None]:
        async with AsyncSession(get_engine()) as session:
            stmt = select(RateLimitRuleOrm).where(
                RateLimitRuleOrm.service == service.qualified_name
            )
            if subject is not None:
                stmt.append_whereclause(RateLimitRuleOrm.subject == subject)

            async for p in await session.stream_scalars(stmt):
                yield RateLimitRule(p, service)

    async def get_rate_limit_rules(self, *subject: str,
                                   trace: bool = True) -> AsyncGenerator["RateLimitRule", None]:
        for sub in subject:
            if trace:
                for node in self.service.trace():
                    async for p in self._get_rules_by_subject(node, sub):
                        yield p
            else:
                async for p in self._get_rules_by_subject(self.service, sub):
                    yield p

    async def get_all_rate_limit_rules(self, *, trace: bool = True) -> AsyncGenerator["RateLimitRule", None]:
        if trace:
            for node in self.service.trace():
                async for p in self._get_rules_by_subject(node, None):
                    yield p
        else:
            async for p in self._get_rules_by_subject(self.service, None):
                yield p

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int):
        async with AsyncSession(get_engine()) as session:
            orm = RateLimitRuleOrm(subject=subject, service=self.service.qualified_name,
                                   time_span=int(time_span.total_seconds()),
                                   limit=limit)
            session.add(orm)
            await session.commit()

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: int):
        async with AsyncSession(get_engine()) as session:
            stmt = delete(RateLimitTokenOrm).where(
                RateLimitTokenOrm.rule_id == rule_id
            )
            await session.execute(stmt)

            stmt = delete(RateLimitRuleOrm).where(
                RateLimitRuleOrm.id == rule_id
            )
            await session.execute(stmt)

    async def acquire_token_for_rate_limit(self, *subject: str, user: str) -> bool:
        tokens = []

        async for rule in self.get_rate_limit_rules(*subject, user):
            token = await rule.acquire_token(user)
            if token is not None:
                logger.trace(f"[rate limit] token acquired for rule {rule.orm.id} "
                             f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                tokens.append(token)
            else:
                logger.trace(f"[rate limit] limit reached for rule {rule.orm.id} "
                             f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                for t in tokens:
                    await t.retire()
                    logger.trace(f"[rate limit] token retired for rule {rule.orm.id} "
                                 f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                return False

        # 未设置rule
        return True


require('nonebot_plugin_apscheduler')
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", minute="*/10", id="delete_outdated_tokens")
async def _delete_outdated_tokens():
    async with AsyncSession(get_engine()) as session:
        now = datetime.now(timezone.utc)
        rowcount = 0
        async for rule in await session.stream_scalars(select(RateLimitRuleOrm)):
            stmt = (delete(RateLimitTokenOrm)
                    .where(RateLimitTokenOrm.acquire_time < now + timedelta(seconds=rule.time_span))
                    .execution_options(synchronize_session=False))
            result = await session.execute(stmt)
            await session.commit()

            rowcount += result.rowcount

        logger.success(f"deleted {rowcount} outdated rate limit token(s)")
