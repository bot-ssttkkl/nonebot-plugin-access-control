from typing import Protocol, Optional

from ....rate_limit import RateLimitRule, RateLimitSingleToken


class TokenStorage(Protocol):
    async def get_first_expire_token(
        self, rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        ...

    async def acquire_token(
        self, rule: RateLimitRule, user: str
    ) -> Optional[RateLimitSingleToken]:
        ...

    async def retire_token(self, token: RateLimitSingleToken):
        ...
