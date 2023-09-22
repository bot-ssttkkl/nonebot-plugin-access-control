"""
nonebot-plugin-access-control

@Author         : ssttkkl
@License        : MIT
@GitHub         : https://github.com/ssttkkl/nonebot-access-control
"""
from nonebot import require
from nonebot.plugin import PluginMetadata

from .config import conf, Config

require("nonebot_plugin_alconna")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_datastore")
require("nonebot_plugin_session")

from nonebot_plugin_session import __plugin_meta__ as plugin_session_meta

from . import matchers
from . import patcher

__plugin_meta__ = PluginMetadata(
    name="权限控制",
    description="对功能进行权限控制以及调用次数限制",
    usage=matchers.cmd.__help_text__,
    type="application",
    homepage="https://github.com/bot-ssttkkl/nonebot-access-control",
    config=Config,
    supported_adapters=plugin_session_meta.supported_adapters
)
