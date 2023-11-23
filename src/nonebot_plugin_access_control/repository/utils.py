import contextvars
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from nonebot import logger
from nonebot_plugin_orm import get_session
from sqlalchemy.ext.asyncio import AsyncSession

_ac_current_session = contextvars.ContextVar("ac_current_session")


@asynccontextmanager
async def use_ac_session() -> AbstractAsyncContextManager[AsyncSession]:
    try:
        yield _ac_current_session.get()
    except LookupError:
        session = get_session()
        logger.trace("sqlalchemy session was created")
        token = _ac_current_session.set(session)

        try:
            yield session
        finally:
            await session.close()
            logger.trace("sqlalchemy session was closed")
            _ac_current_session.reset(token)
