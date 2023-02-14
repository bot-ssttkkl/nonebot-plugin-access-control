from datetime import datetime, timezone, timedelta
from typing import Optional

from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from nonebot_plugin_access_control.models import RateLimitRuleOrm, RateLimitTokenOrm
from .token import RateLimitToken


class RateLimitRule:
    def __init__(self, orm: RateLimitRuleOrm):
        self.orm = orm

    async def acquire_token(self, user: str) -> Optional[RateLimitToken]:
        now = datetime.utcnow()

        async with AsyncSession(get_engine()) as session:
            stmt = select(func.count()).where(
                RateLimitTokenOrm.rule_id == self.orm.id,
                RateLimitTokenOrm.user == user,
                RateLimitTokenOrm.acquire_time >= now - timedelta(seconds=self.orm.time_span)
            )
            cnt = (await session.execute(stmt)).scalar_one()

            if cnt >= self.orm.limit:
                return None

            token_orm = RateLimitTokenOrm(rule_id=self.orm.id, user=user)
            session.add(token_orm)
            await session.commit()

            return RateLimitToken(token_orm)
