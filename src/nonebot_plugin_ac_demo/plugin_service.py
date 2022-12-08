from nonebot import require

require("nonebot_plugin_ac_demo")

from nonebot_plugin_access_control.service import create_plugin_service

plugin_service = create_plugin_service("nonebot_plugin_ac_demo")