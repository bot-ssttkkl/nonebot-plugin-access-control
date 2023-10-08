from contextlib import asynccontextmanager
from typing import Optional, AsyncContextManager

from nonebot_plugin_orm import get_session
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def use_session_or_create(session: Optional[AsyncSession]) -> AsyncContextManager[AsyncSession]:
    session_provided = session is not None
    if not session_provided:
        session = get_session()

    yield session

    if not session_provided:
        await session.close()
