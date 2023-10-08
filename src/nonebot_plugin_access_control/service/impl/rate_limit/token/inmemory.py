from nonebot import require

require("nonebot_plugin_apscheduler")

from datetime import datetime
from typing import Optional, NamedTuple

from apscheduler.triggers.interval import IntervalTrigger
from nonebot_plugin_apscheduler import scheduler

from .interface import TokenStorage
from ....rate_limit import RateLimitRule, RateLimitSingleToken


class StorageKey(NamedTuple):
    rule_id: str
    user: str


def _handle_expired(
    tokens: tuple[RateLimitSingleToken, ...]
) -> tuple[RateLimitSingleToken, ...]:
    now = datetime.utcnow()
    return tuple(filter(lambda x: x.expire_time > now, tokens))


class InmemoryTokenStorage(TokenStorage):
    def __init__(self):
        self.id_cnt = 0
        self.data: dict[StorageKey, tuple[RateLimitSingleToken, ...]] = {}

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

        for k in inmemory_storage.data:
            inmemory_storage.data[k] = _handle_expired(inmemory_storage.data[k])
            if len(inmemory_storage.data[k]) == 0:
                del_keys.add(k)

        for k in del_keys:
            del inmemory_storage.data[k]


inmemory_storage = InmemoryTokenStorage()

scheduler.scheduled_job(
    IntervalTrigger(minutes=1), id="delete_outdated_tokens_inmemory"
)(inmemory_storage.delete_outdated_tokens)


def get_inmemory_token_storage(**kwargs) -> TokenStorage:
    return inmemory_storage
