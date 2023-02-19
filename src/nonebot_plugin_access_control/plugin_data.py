from nonebot_plugin_datastore import get_plugin_data

plugin_data = get_plugin_data()

PluginModel = plugin_data.Model

__all__ = ("plugin_data", "PluginModel")
