from nonebot import require

require("nonebot_plugin_datastore")

from nonebot_plugin_datastore import get_plugin_data

plugin_data = get_plugin_data()

__all__ = ("plugin_data",)
