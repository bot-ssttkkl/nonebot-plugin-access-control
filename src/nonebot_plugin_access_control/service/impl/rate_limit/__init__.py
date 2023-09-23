from datetime import timedelta
from typing import AsyncGenerator, TypeVar, Generic, Collection
from typing import Optional

from nonebot import logger, Bot
from nonebot.internal.adapter import Event
from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import delete, select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from .token import get_token_storage
from .token.datastore import DataStoreTokenStorage
from ...interface import IService
from ...interface.rate_limit import IServiceRateLimit, IRateLimitToken, AcquireTokenResult
from ...rate_limit import RateLimitRule, RateLimitSingleToken
from ....errors import AccessControlBadRequestError, AccessControlQueryError
from ....event_bus import T_Listener, EventType, on_event, fire_event
from ....models import RateLimitTokenOrm, RateLimitRuleOrm
from ....subject import extract_subjects
from ....utils.session import use_session_or_create

T_Service = TypeVar("T_Service", bound=IService)


class RateLimitTokenImpl(IRateLimitToken):
    def __init__(self, tokens: Collection[RateLimitSingleToken], service: "ServiceRateLimitImpl"):
        self.tokens = tokens
        self.service = service

    async def retire(self):
        async with AsyncSession(get_engine()) as sess:
            for t in self.tokens:
                await self.service._retire_token(t, session=sess)


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
            stmt = stmt.where(RateLimitRuleOrm.service == service.qualified_name)
        if subject is not None:
            stmt = stmt.where(RateLimitRuleOrm.subject == subject)

        async for x in await session.stream_scalars(stmt):
            s = service
            if s is None:
                from ...methods import get_service_by_qualified_name
                s = get_service_by_qualified_name(x.service)
            if s is not None:
                yield RateLimitRule(x.id, s, x.subject, timedelta(seconds=x.time_span), x.limit, x.overwrite)

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
                            if p.overwrite:
                                return
                else:
                    async for p in self._get_rules_by_subject(self.service, sub, sess):
                        yield p
                        if p.overwrite:
                            return

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

    async def add_rate_limit_rule(self, subject: str, time_span: timedelta, limit: int, overwrite: bool = False,
                                  *, session: Optional[AsyncSession] = None) -> RateLimitRule:
        async with use_session_or_create(session) as sess:
            if overwrite:
                stmt = select(func.count()).where(
                    RateLimitRuleOrm.subject == subject,
                    RateLimitRuleOrm.service == self.service.qualified_name
                )
                cnt = (await sess.execute(stmt)).scalar_one()

                if cnt > 0:
                    raise AccessControlQueryError('已存在对该实体与服务的限流规则，不允许再添加覆写规则')

            orm = RateLimitRuleOrm(subject=subject, service=self.service.qualified_name,
                                   time_span=int(time_span.total_seconds()),
                                   limit=limit, overwrite=overwrite)
            sess.add(orm)
            await sess.commit()

            await sess.refresh(orm)

            rule = RateLimitRule(orm.id, self.service, subject, time_span, limit, overwrite)
            await self._fire_service_add_rate_limit_rule(rule)

            return rule

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: str,
                                     *, session: Optional[AsyncSession] = None) -> bool:
        async with use_session_or_create(session) as sess:
            orm = await sess.get(RateLimitRuleOrm, rule_id)
            if orm is None:
                return False

            await sess.delete(orm)
            await sess.commit()

            from ...methods import get_service_by_qualified_name
            service = get_service_by_qualified_name(orm.service)

            rule = RateLimitRule(orm.id, service, orm.subject, timedelta(seconds=orm.time_span), orm.limit,
                                 orm.overwrite)
            await cls._fire_service_remove_rate_limit_rule(rule)

            return True

    @staticmethod
    async def _get_first_expire_token(rule: RateLimitRule, user: str,
                                      *, session: Optional[AsyncSession] = None) -> Optional[RateLimitSingleToken]:
        return await get_token_storage(session=session).get_first_expire_token(rule, user)

    @staticmethod
    async def _acquire_token(rule: RateLimitRule, user: str,
                             *, session: Optional[AsyncSession] = None) -> Optional[RateLimitSingleToken]:
        x = await get_token_storage(session=session).acquire_token(rule, user)
        if x is not None:
            logger.trace(f"[rate limit] token {x.id} acquired for rule {x.rule_id} by user {x.user} "
                         f"(service: {rule.service})")
        return x

    @staticmethod
    async def _retire_token(token: RateLimitSingleToken, *, session: Optional[AsyncSession] = None):
        await get_token_storage(session=session).retire_token(token)
        logger.trace(f"[rate limit] token {token.id} retired for rule {token.rule_id} by user {token.user}")

    async def acquire_token_for_rate_limit(self, bot: Bot, event: Event,
                                           *, session: Optional[AsyncSession] = None) -> Optional[RateLimitTokenImpl]:
        result = await self.acquire_token_for_rate_limit_receiving_result(bot, event, session=session)
        return result.token

    async def acquire_token_for_rate_limit_receiving_result(
            self,
            bot: Bot, event: Event,
            *, session: Optional[AsyncSession] = None
    ) -> AcquireTokenResult:
        return await self.acquire_token_for_rate_limit_by_subjects_receiving_result(*extract_subjects(bot, event),
                                                                                    session=session)

    async def acquire_token_for_rate_limit_by_subjects(
            self, *subject: str,
            session: Optional[AsyncSession] = None
    ) -> Optional[RateLimitTokenImpl]:
        result = await self.acquire_token_for_rate_limit_by_subjects_receiving_result(*subject, session=session)
        return result.token

    async def acquire_token_for_rate_limit_by_subjects_receiving_result(
            self, *subject: str,
            session: Optional[AsyncSession] = None
    ) -> AcquireTokenResult:
        assert len(subject) > 0, "require at least one subject"
        user = subject[0]

        async with use_session_or_create(session) as sess:
            tokens = []
            violating_rules = []

            # 先获取所有rule，再对每个rule获取token
            rules = [x async for x in self.get_rate_limit_rules_by_subject(*subject, session=sess)]
            for rule in rules:
                token = await self._acquire_token(rule, user, session=sess)
                if token is not None:
                    tokens.append(token)
                else:
                    logger.debug(f"[rate limit] limit reached for rule {rule.id} "
                                 f"(service: {rule.service}, subject: {rule.subject})")
                    violating_rules.append(rule)

                if rule.overwrite:
                    break

            success = len(violating_rules) == 0
            if not success:
                for t in tokens:
                    await self._retire_token(t, session=sess)

                first_expire_token = None
                for rule in violating_rules:
                    _first_expire_token = await self._get_first_expire_token(rule, user, session=session)
                    if first_expire_token is None or _first_expire_token.expire_time < first_expire_token.expire_time:
                        first_expire_token = _first_expire_token

                return AcquireTokenResult(
                    success=False,
                    violating=violating_rules,
                    available_time=first_expire_token.expire_time
                )
            else:
                return AcquireTokenResult(
                    success=True,
                    token=RateLimitTokenImpl(tokens, self)
                )

    @classmethod
    async def clear_rate_limit_tokens(cls, *, session: Optional[AsyncSession] = None):
        async with use_session_or_create(session) as sess:
            stmt = delete(RateLimitTokenOrm)
            result = await sess.execute(stmt)
            await sess.commit()
            logger.debug(f"deleted {result.rowcount} rate limit token(s)")
