import pytest
import pytest_asyncio
from nonebug import NONEBOT_INIT_KWARGS, App


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "log_level": "DEBUG",
        "sqlalchemy_database_url": "sqlite+aiosqlite:///:memory:",
        "alembic_startup_check": False,
    }


@pytest_asyncio.fixture(autouse=True)
async def prepare_nonebot(app: App):
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter

    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)

    nonebot.load_plugin("nonebot_plugin_access_control")
    nonebot.load_plugin("nonebot_plugin_ac_demo")

    from nonebot_plugin_orm import init_orm, get_session, Model

    await init_orm()

    # async with get_session() as session:
    #     conn = await session.connection()
    #     await conn.run_sync(Model.metadata.create_all)

    yield app
