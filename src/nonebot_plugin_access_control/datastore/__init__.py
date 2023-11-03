"""
用于将datastore数据库迁移到最新版本后再进行数据迁移
"""

from pathlib import Path

from nonebot import require

try:
    require("nonebot_plugin_datastore")

    from nonebot_plugin_datastore import get_plugin_data

    plugin_data = get_plugin_data("nonebot_plugin_access_control")

    migrations_dir = Path(__file__).parent / "migrations"
    plugin_data.set_migration_dir(migrations_dir)

    # 保证将插件加入datastore的待迁移列表
    plugin_data.Model  # noqa
except:  # noqa: E722
    # keep silent
    pass
