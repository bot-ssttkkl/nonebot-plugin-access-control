from contextlib import asynccontextmanager
from typing import AsyncContextManager

from nonebot import get_driver
from nonebot import logger, Driver
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import registry
from sqlalchemy.orm import sessionmaker

from ..config import conf


class DataSourceNotReadyError(RuntimeError):
    pass


class DataSource:
    def __init__(self, driver: Driver, url: str, **kwargs):
        self._engine = None
        self._sessionmaker = None

        self._registry = registry()

        # 仅当TRACE模式时回显sql语句
        kwargs.setdefault("echo", driver.config.log_level == 'TRACE')
        kwargs.setdefault("future", True)

        @driver.on_startup
        async def on_startup():
            self._engine = create_async_engine(url, **kwargs)

            async with self._engine.begin() as conn:
                await conn.run_sync(self._registry.metadata.create_all)

            # expire_on_commit=False will prevent attributes from being expired
            # after commit.
            self._sessionmaker = sessionmaker(
                self._engine, expire_on_commit=False, class_=AsyncSession
            )
            logger.success("data source initialized")

        @driver.on_shutdown
        async def on_shutdown():
            await self._engine.dispose()

            self._engine = None
            self._sessionmaker = None

            logger.success("data source disposed")

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise DataSourceNotReadyError()
        return self._engine

    @property
    def registry(self) -> registry:
        return self._registry

    @asynccontextmanager
    async def start_session(self) -> AsyncContextManager[AsyncSession]:
        if self._sessionmaker is None:
            raise DataSourceNotReadyError()

        async with self._sessionmaker() as session:
            yield session


data_source = DataSource(get_driver(), conf.access_control_database_conn_url)

__all__ = ("data_source", "DataSource", "DataSourceNotReadyError")
