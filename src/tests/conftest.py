import pytest
import pytest_asyncio
from nonebug import NONEBOT_INIT_KWARGS
from sqlalchemy import delete


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "log_level": "TRACE",
        "sqlalchemy_database_url": "sqlite+aiosqlite:///:memory:",
        "alembic_startup_check": False,
        "access_control_reply_on_permission_denied_enabled": False,
        "access_control_reply_on_rate_limited_enabled": False,
    }


@pytest.fixture(scope="session", autouse=True)
def _prepare_nonebot():
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter

    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)

    nonebot.require("nonebot_plugin_access_control")
    nonebot.require("nonebot_plugin_ac_demo")


_orm_inited = False


@pytest_asyncio.fixture(autouse=True)
async def _init_orm(_prepare_nonebot):
    from nonebot_plugin_orm import init_orm, get_session
    from nonebot_plugin_access_control.repository.orm.permission import PermissionOrm
    from nonebot_plugin_access_control.repository.orm.rate_limit import RateLimitRuleOrm, RateLimitTokenOrm

    global _orm_inited

    if not _orm_inited:
        await init_orm()
        _orm_inited = True

    async with get_session() as sess:
        await sess.execute(delete(PermissionOrm))
        await sess.execute(delete(RateLimitRuleOrm))
        await sess.execute(delete(RateLimitTokenOrm))
        await sess.commit()
