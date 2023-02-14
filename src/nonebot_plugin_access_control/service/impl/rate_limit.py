from datetime import timedelta, datetime
from typing import AsyncGenerator, TypeVar, Generic, Optional

from nonebot import logger
from sqlalchemy import delete, func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..interface import IService
from ..interface.rate_limit import IServiceRateLimit
from ..rate_limit import RateLimitRule, RateLimitToken
from ...models import RateLimitTokenOrm, RateLimitRuleOrm
from ...utils.session import use_session_or_create

T_Service = TypeVar("T_Service", bound=IService)


class ServiceRateLimitImpl(Generic[T_Service], IServiceRateLimit):
    def __init__(self, service: T_Service):
        self.service = service

    @staticmethod
    async def _get_rules_by_subject(service: T_Service,
                                    subject: Optional[str],
                                    session: AsyncSession) -> AsyncGenerator[RateLimitRule, None]:
        stmt = select(RateLimitRuleOrm).where(
            RateLimitRuleOrm.service == service.qualified_name
        )
        if subject is not None:
            stmt.append_whereclause(RateLimitRuleOrm.subject == subject)

        async for p in await session.stream_scalars(stmt):
            yield RateLimitRule(p, service)

    async def get_rate_limit_rules(self, *subject: str,
                                   trace: bool = True,
                                   session: Optional[AsyncSession] = None) -> AsyncGenerator[RateLimitRule, None]:
        async with use_session_or_create(session) as sess:
            for sub in subject:
                if trace:
                    for node in self.service.trace():
                        async for p in self._get_rules_by_subject(node, sub, sess):
                            yield p
                else:
                    async for p in self._get_rules_by_subject(self.service, sub, sess):
                        yield p

    async def get_all_rate_limit_rules(self, *, trace: bool = True,
                                       session: Optional[AsyncSession] = None) -> AsyncGenerator[RateLimitRule, None]:
        async with use_session_or_create(session) as sess:
            if trace:
                for node in self.service.trace():
                    async for p in self._get_rules_by_subject(node, None, sess):
                        yield p
            else:
                async for p in self._get_rules_by_subject(self.service, None, sess):
                    yield p

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int,
                                  *, session: Optional[AsyncSession] = None):
        async with use_session_or_create(session) as sess:
            orm = RateLimitRuleOrm(subject=subject, service=self.service.qualified_name,
                                   time_span=int(time_span.total_seconds()),
                                   limit=limit)
            sess.add(orm)
            await sess.commit()

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: int,
                                     *, session: Optional[AsyncSession] = None):
        async with use_session_or_create(session) as sess:
            stmt = delete(RateLimitTokenOrm).where(
                RateLimitTokenOrm.rule_id == rule_id
            )
            await sess.execute(stmt)

            stmt = delete(RateLimitRuleOrm).where(
                RateLimitRuleOrm.id == rule_id
            )
            await sess.execute(stmt)

    @staticmethod
    async def _acquire_token(rule: RateLimitRule, user: str,
                            *, session: Optional[AsyncSession] = None) -> Optional[RateLimitToken]:
        now = datetime.utcnow()

        async with use_session_or_create(session) as sess:
            stmt = select(func.count()).where(
                RateLimitTokenOrm.rule_id == rule.orm.id,
                RateLimitTokenOrm.user == user,
                RateLimitTokenOrm.acquire_time >= now - timedelta(seconds=rule.orm.time_span)
            )
            cnt = (await sess.execute(stmt)).scalar_one()

            if cnt >= rule.orm.limit:
                return None

            token_orm = RateLimitTokenOrm(rule_id=rule.orm.id, user=user)
            sess.add(token_orm)
            await sess.commit()

            return RateLimitToken(token_orm)

    async def acquire_token_for_rate_limit(self, *subject: str, user: str,
                                           session: Optional[AsyncSession] = None) -> bool:
        async with use_session_or_create(session) as sess:
            tokens = []

            async for rule in self.get_rate_limit_rules(*subject, session=sess):
                token = await self._acquire_token(rule, user, session=sess)
                if token is not None:
                    logger.trace(f"[rate limit] token acquired for rule {rule.orm.id} "
                                 f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                    tokens.append(token)
                else:
                    logger.trace(f"[rate limit] limit reached for rule {rule.orm.id} "
                                 f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                    for t in tokens:
                        await t.retire(session=sess)
                        logger.trace(f"[rate limit] token retired for rule {rule.orm.id} "
                                     f"(service: {rule.orm.service}, subject: {rule.orm.subject})")
                    return False

            # 未设置rule
            return True
