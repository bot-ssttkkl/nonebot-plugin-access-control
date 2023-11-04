"""
用于将datastore数据库迁移到最新版本后再进行数据迁移
"""

from pathlib import Path

from nonebot import require
from pkg_resources import DistributionNotFound, get_distribution


def _prepare():
    try:
        get_distribution("nonebot_plugin_datastore")
    except DistributionNotFound:
        return

    require("nonebot_plugin_datastore")

    from nonebot_plugin_datastore import get_plugin_data

    plugin_data = get_plugin_data("nonebot_plugin_access_control")

    migrations_dir = Path(__file__).parent / "migrations"
    plugin_data.set_migration_dir(migrations_dir)

    # 保证将插件加入datastore的待迁移列表
    plugin_data.Model  # noqa


_prepare()
