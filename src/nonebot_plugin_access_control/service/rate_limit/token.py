from nonebot_plugin_datastore.db import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from nonebot_plugin_access_control.models.rate_limit import RateLimitTokenOrm


class RateLimitToken:
    def __init__(self, orm: RateLimitTokenOrm):
        self.orm = orm

    async def retire(self):
        async with AsyncSession(get_engine()) as session:
            await session.delete(self.orm)
            await session.commit()
