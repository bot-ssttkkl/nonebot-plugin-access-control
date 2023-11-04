from typing import TYPE_CHECKING

from arclet.alconna import Args, Option, Alconna, Subcommand, store_true

if TYPE_CHECKING:
    from .handler.utils.env import T_ENV

alc_ac = Alconna(
    "ac",
    Subcommand(
        "permission",
        Subcommand(
            "allow",
            Option("--srv|--service", Args["service", str]),
            Option("--sbj|--subject", Args["subject", str]),
        ),
        Subcommand(
            "deny",
            Option("--srv|--service", Args["service", str]),
            Option("--sbj|--subject", Args["subject", str]),
        ),
        Subcommand(
            "rm",
            Option("--srv|--service", Args["service", str]),
            Option("--sbj|--subject", Args["subject", str]),
        ),
        Subcommand(
            "ls",
            Option("--srv|--service", Args["service;?", str]),
            Option("--sbj|--subject", Args["subject;?", str]),
        ),
    ),
    Subcommand(
        "limit",
        Subcommand(
            "add",
            Option("--srv|--service", Args["service", str]),
            Option("--sbj|--subject", Args["subject", str]),
            Option("--lim|--limit", Args["limit", int]),
            Option("--span", Args["span", str]),
            Option("--overwrite", action=store_true, default=False),
        ),
        Subcommand("rm", Args["limit_rule_id", str]),
        Subcommand(
            "ls",
            Option("--srv|--service", Args["service;?", str]),
            Option("--sbj|--subject", Args["subject;?", str]),
        ),
        Subcommand(
            "reset",
        ),
    ),
    Subcommand(
        "service",
        Subcommand(
            "ls",
            Option("--srv|--service", Args["service;?", str]),
        ),
    ),
    Subcommand("subject"),
    Subcommand("help"),
)


def help_ac(env: "T_ENV" = "nonebot") -> str:
    result = ""

    if env == "nonebot":
        result += "进行控制的指令为`/ac`，仅超级用户可用。"
        result += "（通过在配置文件中设置`SUPERUSERS`变量可配置超级用户）\n\n"

    if env == "nonebot":
        cmd_start = "/ac "
    else:
        cmd_start = ""

    result += f"""
- 帮助
    - `{cmd_start}help`：显示此帮助
- 权限控制
    - `{cmd_start}permission allow --sbj <主体> --srv <服务>`：为主体启用服务
    - `{cmd_start}permission deny --sbj <主体> --srv <服务>`：为主体禁用服务
    - `{cmd_start}permission rm --sbj <主体> --srv <服务>`：为主体删除服务权限配置
    - `{cmd_start}permission ls`：列出所有已配置的权限
    - `{cmd_start}permission ls --sbj <主体>`：列出主体已配置的服务权限
    - `{cmd_start}permission ls --srv <服务>`：列出服务已配置的主体权限
    - `{cmd_start}permission ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的权限
- 流量限制
    - `{cmd_start}limit add --sbj <主体> --srv <服务> --limit <次数> --span <时间间隔> [--overwrite]`：为主体与服务添加限流规则
    - `{cmd_start}limit rm <规则ID>`：删除限流规则
    - `{cmd_start}limit ls`：列出所有已配置的限流规则
    - `{cmd_start}limit ls --sbj <主体>`：列出主体已配置的限流规则
    - `{cmd_start}limit ls --srv <服务>`：列出服务已配置的限流规则
    - `{cmd_start}limit ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的限流规则
    - `{cmd_start}limit reset`：重置限流计数
- 服务查看
    - `{cmd_start}service ls`：列出所有服务与子服务层级
    - `{cmd_start}service ls --srv <服务>`：列出服务的子服务层级
- 主体测试
    - `{cmd_start}subject`：列出消息发送者的所有主体

其中`<服务>`的格式如下：

- `nonebot`：对整个NoneBot进行开关
- `<插件名>`：对整个插件进行开关
- `<插件名>.<子服务名>.<子服务名>.....<子服务名>`：对插件内的某个子服务进行开关
    """.strip()  # noqa: E501

    return result
