"""
nonebot-plugin-access-control

@Author         : ssttkkl
@License        : MIT
@GitHub         : https://github.com/ssttkkl/nonebot-access-control
"""
from nonebot import require

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_orm")
require("nonebot_plugin_session")
require("ssttkkl_nonebot_utils")

from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from .alc import help_ac
from .config import Config
from . import orm_migrations

__plugin_meta__ = PluginMetadata(
    name="权限控制",
    description="对功能进行权限控制以及调用次数限制",
    usage=help_ac(),
    type="application",
    homepage="https://github.com/bot-ssttkkl/nonebot-access-control",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_session"),
    extra={"orm_version_location": orm_migrations},
)

from . import patcher  # noqa
from . import matcher  # noqa
from . import datastore  # noqa
