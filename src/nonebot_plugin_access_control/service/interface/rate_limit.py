from abc import ABC, abstractmethod
from datetime import datetime
from datetime import timedelta
from typing import Optional
from collections.abc import AsyncGenerator
from typing import NamedTuple
from collections.abc import Sequence

from nonebot import Bot
from nonebot.internal.adapter import Event

from ..rate_limit import RateLimitRule
from ...event_bus import T_Listener


class IRateLimitToken:
    async def retire(self):
        ...


class AcquireTokenResult(NamedTuple):
    success: bool
    token: Optional[IRateLimitToken] = None
    violating: Optional[Sequence[RateLimitRule]] = None
    available_time: Optional[datetime] = None


class IServiceRateLimit(ABC):
    @abstractmethod
    def on_add_rate_limit_rule(self, func: Optional[T_Listener] = None):
        raise NotImplementedError()

    @abstractmethod
    def on_remove_rate_limit_rule(self, func: Optional[T_Listener] = None):
        raise NotImplementedError()

    @abstractmethod
    def get_rate_limit_rules_by_subject(
        self, *subject: str, trace: bool = True
    ) -> AsyncGenerator[RateLimitRule, None]:
        ...

    @abstractmethod
    def get_rate_limit_rules(
        self, *, trace: bool = True
    ) -> AsyncGenerator[RateLimitRule, None]:
        ...

    @classmethod
    @abstractmethod
    def get_all_rate_limit_rules_by_subject(
        cls, *subject: str
    ) -> AsyncGenerator[RateLimitRule, None]:
        ...

    @classmethod
    @abstractmethod
    def get_all_rate_limit_rules(cls) -> AsyncGenerator[RateLimitRule, None]:
        ...

    @abstractmethod
    async def add_rate_limit_rule(
        self, subject: str, time_span: timedelta, limit: int, overwrite: bool = False
    ) -> RateLimitRule:
        ...

    @classmethod
    async def remove_rate_limit_rule(cls, rule_id: str) -> bool:
        ...

    @abstractmethod
    async def acquire_token_for_rate_limit(
        self, bot: Bot, event: Event
    ) -> Optional[IRateLimitToken]:
        ...

    @abstractmethod
    async def acquire_token_for_rate_limit_receiving_result(
        self, bot: Bot, event: Event
    ) -> AcquireTokenResult:
        ...

    @abstractmethod
    async def acquire_token_for_rate_limit_by_subjects(
        self, *subject: str
    ) -> Optional[IRateLimitToken]:
        ...

    @abstractmethod
    async def acquire_token_for_rate_limit_by_subjects_receiving_result(
        self, bot: Bot, event: Event
    ) -> AcquireTokenResult:
        ...

    @classmethod
    @abstractmethod
    async def clear_rate_limit_tokens(cls):
        ...
