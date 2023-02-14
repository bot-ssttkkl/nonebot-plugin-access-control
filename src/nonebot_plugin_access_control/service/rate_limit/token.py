from datetime import datetime, timezone, timedelta
from typing import Optional

from nonebot import require, logger
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from nonebot_plugin_access_control.models.rate_limit import RateLimitTokenOrm, RateLimitRuleOrm
from nonebot_plugin_access_control.utils.session import use_session_or_create


class RateLimitToken:
    def __init__(self, orm: RateLimitTokenOrm):
        self.orm = orm

    async def retire(self, *, session: Optional[AsyncSession] = None):
        async with use_session_or_create(session) as sess:
            await sess.delete(self.orm)
            await sess.commit()


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

        logger.trace(f"deleted {rowcount} outdated rate limit token(s)")
