from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from nonebot_plugin_access_control.models import RateLimitRuleOrm, RateLimitTokenOrm
from .token import RateLimitToken

if TYPE_CHECKING:
    from nonebot_plugin_access_control.service import Service


class RateLimitRule:
    def __init__(self, orm: RateLimitRuleOrm, service: "Service"):
        self.orm = orm
        self._service = service

    @property
    def id(self) -> int:
        return self.orm.id

    @property
    def service(self) -> "Service":
        return self._service

    @property
    def subject(self) -> str:
        return self.orm.subject

    @property
    def time_span(self) -> timedelta:
        return timedelta(seconds=self.orm.time_span)

    @property
    def limit(self) -> int:
        return self.orm.limit

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
