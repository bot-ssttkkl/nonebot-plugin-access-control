from datetime import timedelta, datetime, timezone
from typing import Optional, AsyncGenerator

from nonebot import require, logger
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from nonebot_plugin_access_control.models import RateLimitRuleOrm, RateLimitTokenOrm
from nonebot_plugin_access_control.rate_limit.rule import RateLimitRule

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


async def get_rate_limit_rules(service: Optional[str],
                               subject: Optional[str]) -> AsyncGenerator[RateLimitRule, None]:
    async with AsyncSession(get_engine()) as session:
        stmt = select(RateLimitRuleOrm)
        if service is not None:
            stmt.append_whereclause(RateLimitRuleOrm.service == service)
        if subject is not None:
            stmt.append_whereclause(RateLimitRuleOrm.subject == subject)

        async for p in await session.stream_scalars(stmt):
            yield RateLimitRule(p)


async def add_rate_limit_rule(service: str,
                              subject: str,
                              time_span: timedelta,
                              limit: int):
    async with AsyncSession(get_engine()) as session:
        orm = RateLimitRuleOrm(subject=subject, service=service,
                               time_span=int(time_span.total_seconds()),
                               limit=limit)
        session.add(orm)
        await session.commit()


async def remove_rate_limit_rule(rule_id: int):
    async with AsyncSession(get_engine()) as session:
        stmt = delete(RateLimitTokenOrm).where(
            RateLimitTokenOrm.rule_id == rule_id
        )
        await session.execute(stmt)

        stmt = delete(RateLimitRuleOrm).where(
            RateLimitRuleOrm.id == rule_id
        )
        await session.execute(stmt)
