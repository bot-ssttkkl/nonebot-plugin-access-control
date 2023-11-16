from collections.abc import Collection, AsyncGenerator
from datetime import timedelta
from typing import Optional

from nonebot import logger
from nonebot_plugin_access_control_api.context import context
from nonebot_plugin_access_control_api.event_bus import (
    EventType,
    T_Listener,
    on_event,
    fire_event,
)
from nonebot_plugin_access_control_api.models.rate_limit import (
    RateLimitRule,
    IRateLimitToken,
    AcquireTokenResult,
    RateLimitSingleToken,
)
from nonebot_plugin_access_control_api.service.interface import IService
from nonebot_plugin_access_control_api.service.interface.rate_limit import (
    IServiceRateLimit,
)

from ...repository.rate_limit import IRateLimitRepository
from ...repository.rate_limit_token import IRateLimitTokenRepository


class RateLimitTokenImpl(IRateLimitToken):
    def __init__(
        self, tokens: Collection[RateLimitSingleToken], service: "ServiceRateLimitImpl"
    ):
        self.tokens = tokens
        self.service = service

    async def retire(self):
        for t in self.tokens:
            await self.service._retire_token(t)


class ServiceRateLimitImpl(IServiceRateLimit):
    repo = context.require(IRateLimitRepository)
    token_repo = context.require(IRateLimitTokenRepository)

    def __init__(self, service: IService):
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

    @classmethod
    async def _get_rules_by_subject(
        cls, service: Optional[IService], subject: Optional[str]
    ) -> AsyncGenerator[RateLimitRule, None]:
        async for x in cls.repo.get_rules_by_subject(service, subject):
            yield x

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
        rule = await self.repo.add_rate_limit_rule(
            self.service, subject, time_span, limit, overwrite
        )
        await self._fire_service_add_rate_limit_rule(rule)
        return rule

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: str) -> bool:
        rule = await cls.repo.remove_rate_limit_rule(rule_id)
        if rule is not None:
            await cls._fire_service_remove_rate_limit_rule(rule)
            return True
        else:
            return False

    @classmethod
    async def _get_first_expire_token(
        cls, rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        return await cls.token_repo.get_first_expire_token(rule, user)

    @classmethod
    async def _acquire_token(
        cls, rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        x = await cls.token_repo.acquire_token(rule, user)
        if x is not None:
            logger.trace(
                f"[rate limit] token {x.id} acquired "
                f"for rule {x.rule_id} by user {x.user} "
                f"(service: {rule.service})"
            )
        return x

    @classmethod
    async def _retire_token(cls, token: RateLimitSingleToken):
        repo = cls.token_repo.require(IRateLimitTokenRepository)
        await repo.retire_token(token)
        logger.trace(
            f"[rate limit] token {token.id} retired for "
            f"rule {token.rule_id} by user {token.user}"
        )

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
        await cls.token_repo.clear_token()
