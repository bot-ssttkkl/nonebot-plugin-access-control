import contextvars
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from nonebot_plugin_orm import get_session
from sqlalchemy.ext.asyncio import AsyncSession

_ac_current_session = contextvars.ContextVar("ac_current_session")


@asynccontextmanager
async def use_ac_session() -> AbstractAsyncContextManager[AsyncSession]:
    try:
        yield _ac_current_session.get()
    except LookupError:
        session = get_session()
        token = _ac_current_session.set(session)

        yield session

        await session.close()
        _ac_current_session.reset(token)
