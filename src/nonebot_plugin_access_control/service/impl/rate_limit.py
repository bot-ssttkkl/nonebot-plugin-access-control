from datetime import datetime, timedelta
from typing import AsyncGenerator, TypeVar, Generic
from typing import Optional

from nonebot import require, logger
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import delete
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..interface import IService
from ..interface.rate_limit import IServiceRateLimit
from ..rate_limit import RateLimitRule, RateLimitToken
from ...event_bus import T_Listener, EventType, on_event, fire_event
from ...models import RateLimitTokenOrm, RateLimitRuleOrm
from ...utils.session import use_session_or_create

T_Service = TypeVar("T_Service", bound=IService)


class ServiceRateLimitImpl(Generic[T_Service], IServiceRateLimit):
    def __init__(self, service: T_Service):
        self.service = service

    def on_add_rate_limit_rule(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_add_rate_limit_rule,
                        lambda service: service == self.service,
                        func)

    def on_remove_rate_limit_rule(self, func: Optional[T_Listener] = None):
        return on_event(EventType.service_remove_rate_limit_rule,
                        lambda service: service == self.service,
                        func)

    @staticmethod
    async def _get_rules_by_subject(service: Optional[T_Service],
                                    subject: Optional[str],
                                    session: AsyncSession) -> AsyncGenerator[RateLimitRule, None]:
        stmt = select(RateLimitRuleOrm)
        if service is not None:
            stmt.append_whereclause(RateLimitRuleOrm.service == service.qualified_name)
        if subject is not None:
            stmt.append_whereclause(RateLimitRuleOrm.subject == subject)

        async for x in await session.stream_scalars(stmt):
            s = service
            if s is None:
                from ..methods import get_service_by_qualified_name
                s = get_service_by_qualified_name(x.service)
            if s is not None:
                yield RateLimitRule(x.id, s, x.subject, timedelta(seconds=x.time_span), x.limit)

    async def get_rate_limit_rules_by_subject(
            self, *subject: str,
            trace: bool = True,
            session: Optional[AsyncSession] = None
    ) -> AsyncGenerator[RateLimitRule, None]:
        async with use_session_or_create(session) as sess:
            for sub in subject:
                if trace:
                    for node in self.service.trace():
                        async for p in self._get_rules_by_subject(node, sub, sess):
                            yield p
                else:
                    async for p in self._get_rules_by_subject(self.service, sub, sess):
                        yield p

    async def get_rate_limit_rules(self, *, trace: bool = True,
                                   session: Optional[AsyncSession] = None) -> AsyncGenerator[RateLimitRule, None]:
        async with use_session_or_create(session) as sess:
            if trace:
                for node in self.service.trace():
                    async for p in self._get_rules_by_subject(node, None, sess):
                        yield p
            else:
                async for p in self._get_rules_by_subject(self.service, None, sess):
                    yield p

    @classmethod
    async def get_all_rate_limit_rules_by_subject(
            cls, *subject: str,
            session: Optional[AsyncSession] = None
    ) -> AsyncGenerator[RateLimitRule, None]:
        async with use_session_or_create(session) as sess:
            for sub in subject:
                async for x in cls._get_rules_by_subject(None, sub, sess):
                    yield x

    @classmethod
    async def get_all_rate_limit_rules(
            cls,
            *, session: Optional[AsyncSession] = None
    ) -> AsyncGenerator[RateLimitRule, None]:
        async with use_session_or_create(session) as sess:
            async for x in cls._get_rules_by_subject(None, None, sess):
                yield x

    @staticmethod
    async def _fire_service_add_rate_limit_rule(rule: RateLimitRule):
        for node in rule.service.travel():
            await fire_event(EventType.service_add_rate_limit_rule, {
                "service": node,
                "rule": rule
            })

    @staticmethod
    async def _fire_service_remove_rate_limit_rule(rule: RateLimitRule):
        for node in rule.service.travel():
            await fire_event(EventType.service_remove_rate_limit_rule, {
                "service": node,
                "rule": rule
            })

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int,
                                  *, session: Optional[AsyncSession] = None):
        async with use_session_or_create(session) as sess:
            orm = RateLimitRuleOrm(subject=subject, service=self.service.qualified_name,
                                   time_span=int(time_span.total_seconds()),
                                   limit=limit)
            sess.add(orm)
            await sess.commit()

            await sess.refresh(orm)

            rule = RateLimitRule(orm.id, self.service, subject, time_span, limit)
            await self._fire_service_add_rate_limit_rule(rule)

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: int,
                                     *, session: Optional[AsyncSession] = None) -> bool:
        async with use_session_or_create(session) as sess:
            orm = await sess.get(RateLimitRuleOrm, rule_id)
            if orm is None:
                return False

            stmt = delete(RateLimitTokenOrm).where(
                RateLimitTokenOrm.rule_id == rule_id
            )
            await sess.execute(stmt)

            await sess.delete(orm)
            await sess.commit()

            from ..methods import get_service_by_qualified_name
            service = get_service_by_qualified_name(orm.service)

            rule = RateLimitRule(orm.id, service, orm.subject, timedelta(seconds=orm.time_span), orm.limit)
            await cls._fire_service_remove_rate_limit_rule(rule)

            return True

    @staticmethod
    async def _acquire_token(rule: RateLimitRule, user: str,
                             *, session: Optional[AsyncSession] = None) -> Optional[RateLimitToken]:
        now = datetime.utcnow()

        async with use_session_or_create(session) as sess:
            stmt = select(func.count()).where(
                RateLimitTokenOrm.rule_id == rule.id,
                RateLimitTokenOrm.user == user,
                RateLimitTokenOrm.acquire_time >= now - rule.time_span
            )
            cnt = (await sess.execute(stmt)).scalar_one()

            if cnt >= rule.limit:
                return None

            x = RateLimitTokenOrm(rule_id=rule.id, user=user)
            sess.add(x)
            await sess.commit()

            await sess.refresh(x)

            return RateLimitToken(x.id, x.rule_id, x.user, x.acquire_time)

    @staticmethod
    async def _retire_token(token: RateLimitToken, *, session: Optional[AsyncSession] = None):
        async with use_session_or_create(session) as sess:
            stmt = delete(RateLimitRuleOrm).where(RateLimitRuleOrm.id == token.id)
            await sess.execute(stmt)
            await sess.commit()

    async def acquire_token_for_rate_limit(self, *subject: str, user: str,
                                           session: Optional[AsyncSession] = None) -> bool:
        async with use_session_or_create(session) as sess:
            tokens = []

            async for rule in self.get_rate_limit_rules_by_subject(*subject, session=sess):
                token = await self._acquire_token(rule, user, session=sess)
                if token is not None:
                    logger.trace(f"[rate limit] token acquired for rule {rule.id} "
                                 f"(service: {rule.service}, subject: {rule.subject})")
                    tokens.append(token)
                else:
                    logger.trace(f"[rate limit] limit reached for rule {rule.id} "
                                 f"(service: {rule.service}, subject: {rule.subject})")
                    for t in tokens:
                        await self._retire_token(t, session=sess)
                        logger.trace(f"[rate limit] token retired for rule {rule.id} "
                                     f"(service: {rule.service}, subject: {rule.subject})")
                    return False

            # 未设置rule
            return True

    @classmethod
    async def clear_rate_limit_tokens(cls, *, session: Optional[AsyncSession] = None):
        async with use_session_or_create(session) as sess:
            stmt = delete(RateLimitTokenOrm)
            result = await sess.execute(stmt)
            await sess.commit()
            logger.trace(f"deleted {result.rowcount} rate limit token(s)")


require('nonebot_plugin_apscheduler')
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", minute="*/10", id="delete_outdated_tokens")
async def _delete_outdated_tokens():
    async with AsyncSession(get_engine()) as session:
        now = datetime.utcnow()
        rowcount = 0
        async for rule in await session.stream_scalars(select(RateLimitRuleOrm)):
            stmt = (delete(RateLimitTokenOrm)
                    .where(RateLimitTokenOrm.acquire_time < now + timedelta(seconds=rule.time_span))
                    .execution_options(synchronize_session=False))
            result = await session.execute(stmt)
            await session.commit()

            rowcount += result.rowcount

        logger.trace(f"deleted {rowcount} outdated rate limit token(s)")
