from datetime import timedelta
from io import StringIO
from typing import Optional

import pytimeparser
from arclet.alconna import Alconna, Subcommand, Args, Option, store_true, OptionResult
from nonebot.internal.matcher import Matcher, current_bot, current_event
from nonebot.internal.params import Depends
from nonebot_plugin_alconna import on_alconna, Match, AlconnaMatch, Check, assign, Query

from .handle_error import handle_error
from ..service import Service, get_service_by_qualified_name
from ..service.rate_limit import RateLimitRule
from ..subject import extract_subjects
from ..utils.tree import get_tree_summary

cmd = on_alconna(
    Alconna(
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
            Subcommand(
                "rm",
                Args["limit_rule_id", str]
            ),
            Subcommand(
                "ls",
                Option("--srv|--service", Args["service;?", str]),
                Option("--sbj|--subject", Args["subject;?", str]),
            ),
            Subcommand(
                "reset",
            )
        ),
        Subcommand(
            "service",
            Subcommand(
                "ls",
                Option("--srv|--service", Args["service;?", str]),
            )
        ),
        Subcommand(
            "subject"
        ),
        Subcommand(
            "help"
        )
    ),
    use_cmd_start=True,
    use_cmd_sep=False,
    priority=1,
    block=True
)

cmd.__help_text__ = """
进行控制的指令为`/ac`，仅超级用户可用。（通过在配置文件中设置`SUPERUSERS`变量可配置超级用户）

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
""".strip()


async def _get_service(matcher: Matcher, service_name: str) -> Service:
    service = get_service_by_qualified_name(service_name)

    if service is None:
        await matcher.finish("service not found")
    else:
        return service


async def require_subject_and_service(
        matcher: Matcher,
        subject: Match[str] = AlconnaMatch("subject"),
        service_name: Match[str] = AlconnaMatch("service"),
):
    if not subject.available or not service_name.available:
        await matcher.finish("请指定subject与service")


@cmd.handle([Check(assign("permission.allow")), Depends(require_subject_and_service)])
@handle_error()
async def handle_permission_allow(
        matcher: Matcher,
        subject: Match[str] = AlconnaMatch("subject"),
        service_name: Match[str] = AlconnaMatch("service"),
):
    service = await _get_service(matcher, service_name.result)
    await service.set_permission(subject.result, True)
    await matcher.send("ok")
    await matcher.finish()


@cmd.handle([Check(assign("permission.deny")), Depends(require_subject_and_service)])
@handle_error()
async def handle_permission_deny(
        matcher: Matcher,
        subject: Match[str] = AlconnaMatch("subject"),
        service_name: Match[str] = AlconnaMatch("service"),
):
    service = await _get_service(matcher, service_name.result)
    await service.set_permission(subject.result, False)
    await matcher.send("ok")
    await matcher.finish()


@cmd.handle([Check(assign("permission.rm")), Depends(require_subject_and_service)])
@handle_error()
async def handle_permission_rm(
        matcher: Matcher,
        subject: Match[str] = AlconnaMatch("subject"),
        service_name: Match[str] = AlconnaMatch("service"),
):
    service = await _get_service(matcher, service_name.result)
    await service.remove_permission(subject.result)
    await matcher.send("ok")
    await matcher.finish()


@cmd.handle([Check(assign("permission.ls"))])
@handle_error()
async def handle_permission_ls(
        matcher: Matcher,
        subject: Match[str] = AlconnaMatch("subject"),
        service_name: Match[str] = AlconnaMatch("service"),
):
    if not service_name.available and not subject.available:
        permissions = [x async for x in Service.get_all_permissions()]
    elif not service_name.available:
        permissions = [x async for x in Service.get_all_permissions_by_subject(subject.result)]
    else:
        service = await _get_service(matcher, service_name.result)
        if not subject.available:
            permissions = [x async for x in service.get_permissions()]
        else:
            permissions = [await service.get_permission_by_subject(subject.result)]

    if len(permissions) != 0:
        # 按照服务全称、先allow再deny、subject排序
        permissions = sorted(permissions, key=lambda x: (x.service.qualified_name, x.allow, x.subject))

        for i in range(0, len(permissions), 20):
            j = min(i + 20, len(permissions))
            with StringIO() as sio:
                for p in permissions[i:j]:
                    sio.write(f"\'{p.service.qualified_name}\'")

                    if p.allow:
                        sio.write(" allow ")
                    else:
                        sio.write(" deny ")

                    sio.write(f"\'{p.subject}\'")
                    if service_name is not None and p.service.qualified_name != service_name:
                        sio.write(f" (inherited from \'{p.service.qualified_name}\')")
                    sio.write('\n')
                await matcher.send(sio.getvalue().strip())
    else:
        await matcher.send("empty")
    await matcher.finish()


def _map_rule(sio: StringIO, rule: RateLimitRule, service_name: Optional[str]):
    sio.write(f"[{rule.id}] \'{rule.service.qualified_name}\' "
              f"limit \'{rule.subject}\' to {rule.limit} time(s) "
              f"every {int(rule.time_span.total_seconds())}s")
    if rule.overwrite:
        sio.write(" (overwrite)")
    if service_name is not None and rule.service.qualified_name != service_name:
        sio.write(f" (inherited from \'{rule.service.qualified_name}\')")


@cmd.handle([Check(assign("limit.add")), Depends(require_subject_and_service)])
@handle_error()
async def handle_limit_add(
        matcher: Matcher,
        subject: Match[str] = AlconnaMatch("subject"),
        service_name: Match[str] = AlconnaMatch("service"),
        limit: Match[int] = AlconnaMatch("limit"),
        time_span: Match[timedelta] = AlconnaMatch("span"),
        overwrite: Query[OptionResult] = Query("limit.add.overwrite")
):
    if not time_span.available:
        await matcher.finish("请使用--span指定限制时间段")
    if not limit.available:
        await matcher.finish("请使用--limit指定限制次数")
    if limit.result <= 0:
        await matcher.finish("limit必须大于0")

    try:
        parsed_time_span = pytimeparser.parse(time_span.result)
    except ValueError:
        await matcher.finish("给定的span不合法")

    service = await _get_service(matcher, service_name.result)
    rule = await service.add_rate_limit_rule(subject.result, parsed_time_span, limit.result,
                                             overwrite.result.value if overwrite.available else False)
    with StringIO() as sio:
        _map_rule(sio, rule, service_name.result)
        await matcher.send(sio.getvalue().strip())
    await matcher.finish()


@cmd.assign("limit.rm")
@handle_error()
async def handle_limit_rm(
        matcher: Matcher,
        rule_id: Match[str] = AlconnaMatch("limit_rule_id"),
):
    if not rule_id.available:
        await matcher.finish("请使用--rule_id指定限流规则ID")

    ok = await Service.remove_rate_limit_rule(rule_id.result)
    if ok:
        await matcher.send('ok')
    else:
        await matcher.send('rule not found')
    await matcher.finish()


@cmd.assign("limit.ls")
@handle_error()
async def handle_limit_ls(
        matcher: Matcher,
        subject: Match[str] = AlconnaMatch("subject"),
        service_name: Match[str] = AlconnaMatch("service"),
):
    if not service_name.available and not subject.available:
        rules = [x async for x in Service.get_all_rate_limit_rules()]
    elif not service_name.available:
        rules = [x async for x in Service.get_all_rate_limit_rules_by_subject(subject.result)]
    else:
        service = await _get_service(matcher, service_name.result)
        if not subject.available:
            rules = [x async for x in service.get_rate_limit_rules()]
        else:
            rules = [x async for x in service.get_rate_limit_rules_by_subject(subject.result)]

    if len(rules) != 0:
        # 按照服务全称、subject排序
        rules = sorted(rules, key=lambda x: (x.service.qualified_name, x.subject, x.id))

        for i in range(0, len(rules), 20):
            j = min(i + 20, len(rules))
            with StringIO() as sio:
                for rule in rules[i:j]:
                    _map_rule(sio, rule, service_name.result)
                    sio.write('\n')
                await matcher.send(sio.getvalue().strip())
    else:
        await matcher.send("empty")
    await matcher.finish()


@cmd.assign("limit.reset")
@handle_error()
async def handle_limit_reset(matcher: Matcher):
    await Service.clear_rate_limit_tokens()
    await matcher.send("ok")
    await matcher.finish()


@cmd.assign("service.ls")
@handle_error()
async def handle_service_ls(
        matcher: Matcher,
        service_name: Match[str] = AlconnaMatch("service"),
):
    service = await _get_service(matcher, service_name.result if service_name.available else "nonebot")
    summary = get_tree_summary(service, lambda x: x.children, lambda x: x.name)

    summary = summary.split('\n')

    for i in range(0, len(summary), 20):
        j = min(i + 20, len(summary))
        with StringIO() as sio:
            for s in summary[i:j]:
                sio.write(s)
                sio.write('\n')
            await matcher.send(sio.getvalue().strip())
    await matcher.finish()


@cmd.assign("subject")
@handle_error()
async def handle_subject(matcher: Matcher):
    bot = current_bot.get()
    event = current_event.get()
    sbj = extract_subjects(bot, event)
    await matcher.send('\n'.join(sbj))
    await matcher.finish()


@cmd.handle()
@handle_error()
async def handle_help(matcher: Matcher):
    await matcher.send(cmd.__help_text__)
    await matcher.finish()
