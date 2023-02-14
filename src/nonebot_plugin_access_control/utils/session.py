from contextlib import asynccontextmanager
from typing import Optional

from nonebot_plugin_datastore.db import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession


@asynccontextmanager
async def use_session_or_create(session: Optional[AsyncSession]):
    session_provided = session is not None
    if not session_provided:
        session = AsyncSession(get_engine())

    yield session

    if not session_provided:
        await session.close()
