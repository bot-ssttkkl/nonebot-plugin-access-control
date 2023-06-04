"""
nonebot-plugin-access-control

@Author         : ssttkkl
@License        : MIT
@GitHub         : https://github.com/ssttkkl/nonebot-access-control
"""
from .config import conf, Config

from nonebot.plugin import PluginMetadata

__plugin_metad__ = PluginMetadata(
    name="权限控制",
    description="对功能进行权限控制以及调用次数限制",
    usage="""
进行控制的指令为`/ac`，仅超级用户可用。（通过在配置文件中设置`SUPERUSERS`变量可设置超级用户）

- 帮助
    - `/ac help`：显示此帮助
- 权限控制
    - `/ac permission allow --sbj <主体> --srv <服务>`：为主体启用服务
    - `/ac permission deny --sbj <主体> --srv <服务>`：为主体禁用服务
    - `/ac permission rm --sbj <主体> --srv <服务>`：为主体删除服务权限配置
    - `/ac permission ls`：列出所有已配置的权限
    - `/ac permission ls --sbj <主体>`：列出主体已配置的服务权限
    - `/ac permission ls --srv <服务>`：列出服务已配置的主体权限
    - `/ac permission ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的权限
- 流量限制
    - `/ac limit add --sbj <主体> --srv <服务> --limit <次数> --span <时间间隔> [--overwrite]`：为主体与服务添加限流规则
    - `/ac limit rm <规则ID>`：删除限流规则
    - `/ac limit ls`：列出所有已配置的限流规则
    - `/ac limit ls --sbj <主体>`：列出主体已配置的限流规则
    - `/ac limit ls --srv <服务>`：列出服务已配置的限流规则
    - `/ac limit ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的限流规则
    - `/ac limit reset`：重置限流计数
- 服务查看
    - `/ac service ls`：列出所有服务与子服务层级
    - `/ac service ls --srv <服务>`：列出服务的子服务层级
- 主体测试
    - `/ac subject`：列出消息发送者的所有主体

其中`<服务>`的格式如下：

- `nonebot`：对整个NoneBot进行开关
- `<插件名>`：对整个插件进行开关
- `<插件名>.<子服务名>.<子服务名>.....<子服务名>`：对插件内的某个子服务进行开关（需参照下文对插件进行配置）
    """.strip(),
    type="application",
    homepage="https://github.com/ssttkkl/nonebot-access-control",
    config=Config,
    supported_adapters=None
)

from nonebot import require

require("nonebot_plugin_datastore")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_session")

from .service import get_nonebot_service

from nonebot import logger, get_driver, get_loaded_plugins

if conf.access_control_auto_patch_enabled:
    @get_driver().on_startup
    def _():
        nonebot_service = get_nonebot_service()

        patched_plugins = []

        for plugin in get_loaded_plugins():
            if plugin.name == 'nonebot_plugin_access_control' or plugin.name in conf.access_control_auto_patch_ignore:
                continue

            service = nonebot_service.get_or_create_plugin_service(plugin.name)
            if service.auto_created:
                for matcher in plugin.matcher:
                    service.patch_matcher(matcher)
                patched_plugins.append(plugin)

        logger.opt(colors=True).success(
            "auto patched plugin(s): " + ', '.join([f'<y>{p.name}</y>' for p in patched_plugins]))

from . import matchers
