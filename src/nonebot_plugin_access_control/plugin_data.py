from nonebot_plugin_datastore import get_plugin_data
from nonebot_plugin_datastore.db import get_engine, post_db_init

plugin_data = get_plugin_data()

PluginModel = plugin_data.Model


@post_db_init
async def create_table():
    async with get_engine().begin() as conn:
        await conn.run_sync(lambda conn: plugin_data.metadata.create_all(conn))


__all__ = ("plugin_data", "PluginModel")
