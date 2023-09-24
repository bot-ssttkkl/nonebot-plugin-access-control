"""
nonebot-plugin-access-control

@Author         : ssttkkl
@License        : MIT
@GitHub         : https://github.com/ssttkkl/nonebot-access-control
"""
from nonebot import require

require("ssttkkl_nonebot_utils")

from nonebot.plugin import PluginMetadata

from .alc import help_ac
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="权限控制",
    description="对功能进行权限控制以及调用次数限制",
    usage=help_ac(),
    type="application",
    homepage="https://github.com/bot-ssttkkl/nonebot-access-control",
    config=Config,
    supported_adapters={
        "~onebot.v11",
        "~onebot.v12",
        "~console",
        "~kaiheila",
        "~qqguild",
        "~telegram",
        "~feishu",
    },
)

from . import patcher
from . import matcher
