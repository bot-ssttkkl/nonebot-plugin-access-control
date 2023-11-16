from nonebot import require

from nonebot_plugin_access_control_api.context import context

require("nonebot_plugin_apscheduler")

from datetime import datetime
from typing import Optional, NamedTuple

from nonebot_plugin_apscheduler import scheduler
from apscheduler.triggers.interval import IntervalTrigger

from nonebot_plugin_access_control_api.models.rate_limit import (
    RateLimitRule,
    RateLimitSingleToken,
)

from .interface import IRateLimitTokenRepository


class StorageKey(NamedTuple):
    rule_id: str
    user: str


def _handle_expired(
    tokens: tuple[RateLimitSingleToken, ...]
) -> tuple[RateLimitSingleToken, ...]:
    now = datetime.utcnow()
    return tuple(filter(lambda x: x.expire_time > now, tokens))


@context.bind_singleton_to(IRateLimitTokenRepository)
class InmemoryTokenRepository(IRateLimitTokenRepository):
    def __init__(self):
        self.id_cnt = 0
        self.data: dict[StorageKey, tuple[RateLimitSingleToken, ...]] = {}

        scheduler.add_job(
            self.delete_outdated_tokens,
            IntervalTrigger(minutes=1),
            id="delete_outdated_tokens_inmemory",
        )

    def next_id(self) -> int:
        self.id_cnt += 1
        return self.id_cnt

    async def get_first_expire_token(
        self, rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        key = StorageKey(rule.id, user)
        tokens = _handle_expired(self.data.get(key) or ())
        self.data[key] = tokens

        with_min_expire_time = None
        for x in tokens:
            if (
                with_min_expire_time is None
                or x.expire_time < with_min_expire_time.expire_time
            ):
                with_min_expire_time = x
        return with_min_expire_time

    async def acquire_token(
        self, rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        key = StorageKey(rule.id, user)
        tokens = _handle_expired(self.data.get(key) or ())
        self.data[key] = tokens

        if len(tokens) >= rule.limit:
            return None

        acquire_time = datetime.utcnow()
        expire_time = acquire_time + rule.time_span

        token = RateLimitSingleToken(
            self.next_id(), rule.id, user, acquire_time, expire_time
        )
        self.data[key] = (*tokens, token)
        return token

    async def retire_token(self, token: RateLimitSingleToken):
        key = StorageKey(token.rule_id, token.user)
        tokens = _handle_expired(self.data.get(key) or ())
        self.data[key] = tuple(filter(lambda x: x.id != token.id, tokens))

    async def delete_outdated_tokens(self):
        del_keys = set()

        for k in self.data:
            self.data[k] = _handle_expired(self.data[k])
            if len(self.data[k]) == 0:
                del_keys.add(k)

        for k in del_keys:
            del self.data[k]

    async def clear_token(self):
        self.data = {}
