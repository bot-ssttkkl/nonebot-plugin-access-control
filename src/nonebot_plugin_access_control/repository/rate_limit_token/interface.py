from typing import Optional, Protocol

from nonebot_plugin_access_control_api.models.rate_limit import (
    RateLimitRule,
    RateLimitSingleToken,
)


class IRateLimitTokenRepository(Protocol):
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

    async def clear_token(self):
        ...
