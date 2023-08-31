from datetime import datetime, timedelta
from typing import Optional

from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .interface import TokenStorage
from ....rate_limit import RateLimitRule, RateLimitSingleToken
from .....models import RateLimitTokenOrm, RateLimitRuleOrm
from .....utils.session import use_session_or_create


class DataStoreTokenStorage(TokenStorage):
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    async def acquire_token(self, rule: RateLimitRule, user: str) -> Optional[RateLimitSingleToken]:
        now = datetime.utcnow()

        async with use_session_or_create(self.session) as sess:
            stmt = select(func.count()).where(
                RateLimitTokenOrm.rule_id == rule.id,
                RateLimitTokenOrm.user == user,
                RateLimitTokenOrm.expire_time > now
            )
            cnt = (await sess.execute(stmt)).scalar_one()

            if cnt >= rule.limit:
                return None

            acquire_time = datetime.utcnow()
            expire_time = acquire_time + rule.time_span

            x = RateLimitTokenOrm(rule_id=rule.id, user=user, acquire_time=acquire_time, expire_time=expire_time)
            sess.add(x)
            await sess.commit()

            await sess.refresh(x)

            return RateLimitSingleToken(x.id, x.rule_id, x.user, acquire_time, expire_time)

    async def retire_token(self, token: RateLimitSingleToken):
        async with use_session_or_create(self.session) as sess:
            stmt = delete(RateLimitTokenOrm).where(RateLimitTokenOrm.id == token.id)
            await sess.execute(stmt)
            await sess.commit()


@scheduler.scheduled_job(IntervalTrigger(minutes=10), id="delete_outdated_tokens_datastore")
async def _delete_outdated_tokens():
    async with AsyncSession(get_engine()) as session:
        now = datetime.utcnow()
        stmts = []
        async for rule in await session.stream_scalars(select(RateLimitRuleOrm)):
            stmt = (delete(RateLimitTokenOrm)
                    .where(RateLimitTokenOrm.rule_id == rule.id,
                           RateLimitTokenOrm.expire_time <= now)
                    .execution_options(synchronize_session=False))
            stmts.append(stmt)

        rowcount = 0
        for stmt in stmts:
            result = await session.execute(stmt)
            rowcount += result.rowcount

        await session.commit()

        logger.debug(f"deleted {rowcount} outdated rate limit token(s)")


def get_datastore_token_storage(**kwargs) -> TokenStorage:
    return DataStoreTokenStorage(session=kwargs.get("session"))
