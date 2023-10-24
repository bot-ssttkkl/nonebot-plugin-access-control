from datetime import timedelta
from typing import TypeVar, Generic
from collections.abc import AsyncGenerator, Collection
from typing import Optional

from nonebot import logger, Bot
from nonebot.internal.adapter import Event
from sqlalchemy import delete, select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from .token import get_token_storage
from ...interface import IService
from ...interface.rate_limit import (
    IServiceRateLimit,
    IRateLimitToken,
    AcquireTokenResult,
)
from ...rate_limit import RateLimitRule, RateLimitSingleToken
from ....errors import AccessControlQueryError
from ....event_bus import T_Listener, EventType, on_event, fire_event
from ....models import RateLimitTokenOrm, RateLimitRuleOrm
from ....subject import extract_subjects
from ....utils.session import use_ac_session

T_Service = TypeVar("T_Service", bound=IService)


class RateLimitTokenImpl(IRateLimitToken):
    def __init__(
        self, tokens: Collection[RateLimitSingleToken], service: "ServiceRateLimitImpl"
    ):
        self.tokens = tokens
        self.service = service

    async def retire(self):
        for t in self.tokens:
            await self.service._retire_token(t)


class ServiceRateLimitImpl(Generic[T_Service], IServiceRateLimit):
    def __init__(self, service: T_Service):
        self.service = service

    def on_add_rate_limit_rule(self, func: Optional[T_Listener] = None):
        return on_event(
            EventType.service_add_rate_limit_rule,
            lambda service: service == self.service,
            func,
        )

    def on_remove_rate_limit_rule(self, func: Optional[T_Listener] = None):
        return on_event(
            EventType.service_remove_rate_limit_rule,
            lambda service: service == self.service,
            func,
        )

    @staticmethod
    async def _get_rules_by_subject(
        service: Optional[T_Service], subject: Optional[str]
    ) -> AsyncGenerator[RateLimitRule, None]:
        async with use_ac_session() as session:
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
                    yield RateLimitRule(
                        x.id,
                        s,
                        x.subject,
                        timedelta(seconds=x.time_span),
                        x.limit,
                        x.overwrite,
                    )

    async def get_rate_limit_rules_by_subject(
        self, *subject: str, trace: bool = True
    ) -> AsyncGenerator[RateLimitRule, None]:
        for sub in subject:
            if trace:
                for node in self.service.trace():
                    async for p in self._get_rules_by_subject(node, sub):
                        yield p
                        if p.overwrite:
                            return
            else:
                async for p in self._get_rules_by_subject(self.service, sub):
                    yield p
                    if p.overwrite:
                        return

    async def get_rate_limit_rules(
        self, *, trace: bool = True
    ) -> AsyncGenerator[RateLimitRule, None]:
        if trace:
            for node in self.service.trace():
                async for p in self._get_rules_by_subject(node, None):
                    yield p
        else:
            async for p in self._get_rules_by_subject(self.service, None):
                yield p

    @classmethod
    async def get_all_rate_limit_rules_by_subject(
        cls, *subject: str
    ) -> AsyncGenerator[RateLimitRule, None]:
        for sub in subject:
            async for x in cls._get_rules_by_subject(None, sub):
                yield x

    @classmethod
    async def get_all_rate_limit_rules(cls) -> AsyncGenerator[RateLimitRule, None]:
        async for x in cls._get_rules_by_subject(None, None):
            yield x

    @staticmethod
    async def _fire_service_add_rate_limit_rule(rule: RateLimitRule):
        for node in rule.service.travel():
            await fire_event(
                EventType.service_add_rate_limit_rule, {"service": node, "rule": rule}
            )

    @staticmethod
    async def _fire_service_remove_rate_limit_rule(rule: RateLimitRule):
        for node in rule.service.travel():
            await fire_event(
                EventType.service_remove_rate_limit_rule,
                {"service": node, "rule": rule},
            )

    async def add_rate_limit_rule(
        self, subject: str, time_span: timedelta, limit: int, overwrite: bool = False
    ) -> RateLimitRule:
        async with use_ac_session() as sess:
            if overwrite:
                stmt = select(func.count()).where(
                    RateLimitRuleOrm.subject == subject,
                    RateLimitRuleOrm.service == self.service.qualified_name,
                )
                cnt = (await sess.execute(stmt)).scalar_one()

                if cnt > 0:
                    raise AccessControlQueryError("已存在对该实体与服务的限流规则，不允许再添加覆写规则")

            orm = RateLimitRuleOrm(
                subject=subject,
                service=self.service.qualified_name,
                time_span=int(time_span.total_seconds()),
                limit=limit,
                overwrite=overwrite,
            )
            sess.add(orm)
            await sess.commit()

            await sess.refresh(orm)

            rule = RateLimitRule(
                orm.id, self.service, subject, time_span, limit, overwrite
            )
            await self._fire_service_add_rate_limit_rule(rule)

            return rule

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: str) -> bool:
        async with use_ac_session() as sess:
            orm = await sess.get(RateLimitRuleOrm, rule_id)
            if orm is None:
                return False

            await sess.delete(orm)
            await sess.commit()

            from ...methods import get_service_by_qualified_name

            service = get_service_by_qualified_name(orm.service)

            rule = RateLimitRule(
                orm.id,
                service,
                orm.subject,
                timedelta(seconds=orm.time_span),
                orm.limit,
                orm.overwrite,
            )
            await cls._fire_service_remove_rate_limit_rule(rule)

            return True

    @staticmethod
    async def _get_first_expire_token(
        rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        return await get_token_storage().get_first_expire_token(rule, user)

    @staticmethod
    async def _acquire_token(
        rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        x = await get_token_storage().acquire_token(rule, user)
        if x is not None:
            logger.trace(
                f"[rate limit] token {x.id} acquired "
                f"for rule {x.rule_id} by user {x.user} "
                f"(service: {rule.service})"
            )
        return x

    @staticmethod
    async def _retire_token(token: RateLimitSingleToken):
        await get_token_storage().retire_token(token)
        logger.trace(
            f"[rate limit] token {token.id} retired for "
            f"rule {token.rule_id} by user {token.user}"
        )

    async def acquire_token_for_rate_limit(
        self, bot: Bot, event: Event, *, session: Optional[AsyncSession] = None
    ) -> Optional[RateLimitTokenImpl]:
        result = await self.acquire_token_for_rate_limit_receiving_result(
            bot, event, session=session
        )
        return result.token

    async def acquire_token_for_rate_limit_receiving_result(
        self, bot: Bot, event: Event, *, session: Optional[AsyncSession] = None
    ) -> AcquireTokenResult:
        return await self.acquire_token_for_rate_limit_by_subjects_receiving_result(
            *extract_subjects(bot, event)
        )

    async def acquire_token_for_rate_limit_by_subjects(
        self, *subject: str, session: Optional[AsyncSession] = None
    ) -> Optional[RateLimitTokenImpl]:
        result = await self.acquire_token_for_rate_limit_by_subjects_receiving_result(
            *subject
        )
        return result.token

    async def acquire_token_for_rate_limit_by_subjects_receiving_result(
        self, *subject: str
    ) -> AcquireTokenResult:
        assert len(subject) > 0, "require at least one subject"
        user = subject[0]

        tokens = []
        violating_rules = []

        # 先获取所有rule，再对每个rule获取token
        rules = [x async for x in self.get_rate_limit_rules_by_subject(*subject)]
        for rule in rules:
            token = await self._acquire_token(rule, user)
            if token is not None:
                tokens.append(token)
            else:
                logger.debug(
                    f"[rate limit] limit reached for rule {rule.id} "
                    f"(service: {rule.service}, subject: {rule.subject})"
                )
                violating_rules.append(rule)

            if rule.overwrite:
                break

        success = len(violating_rules) == 0
        if not success:
            for t in tokens:
                await self._retire_token(t)

            first_expire_token = None
            for rule in violating_rules:
                _first_expire_token = await self._get_first_expire_token(rule, user)
                if (
                    first_expire_token is None
                    or _first_expire_token.expire_time < first_expire_token.expire_time
                ):
                    first_expire_token = _first_expire_token

            return AcquireTokenResult(
                success=False,
                violating=violating_rules,
                available_time=first_expire_token.expire_time,
            )
        else:
            return AcquireTokenResult(
                success=True, token=RateLimitTokenImpl(tokens, self)
            )

    @classmethod
    async def clear_rate_limit_tokens(cls):
        async with use_ac_session() as sess:
            stmt = delete(RateLimitTokenOrm)
            result = await sess.execute(stmt)
            await sess.commit()
            logger.debug(f"deleted {result.rowcount} rate limit token(s)")
