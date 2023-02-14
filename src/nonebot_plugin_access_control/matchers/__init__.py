from datetime import timedelta
from io import StringIO
from typing import Dict, Tuple, Optional

from nonebot import on_command
from nonebot.internal.adapter import Message
from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .handle_error import handle_error
from .parser import parser
from ..service import get_services_by_subject, Service, get_service_by_qualified_name
from ..service.methods import get_all_permissions
from ..utils.tree import get_tree_summary


def parse_integer(text: str) -> int:
    num = 0
    for c in text:
        c_ord = ord(c) - ord('0')
        if 0 <= c_ord <= 9:
            num = num * 10 + c_ord
        else:
            break
    return num


cmd = on_command("ac", permission=SUPERUSER)


@cmd.handle()
@handle_error()
async def _(matcher: Matcher, arg_msg: Message = CommandArg()):
    args = list(filter(lambda x: len(x) > 0, arg_msg.extract_plain_text().split(' ')))
    if len(args) == 0:
        await handle_help(matcher)
        return
    else:
        if args[0] == 'help':
            await handle_help(matcher)
            return
        elif args[0] == 'subject':
            if len(args) == 5 and args[2] == 'allow' and args[3] == 'service':
                await handle_subject_allow_service(matcher, args[1], args[4])
                return

            if len(args) == 5 and args[2] == 'deny' and args[3] == 'service':
                await handle_subject_deny_service(matcher, args[1], args[4])
                return

            if len(args) == 5 and args[2] == 'rm' and args[3] == 'service':
                await handle_subject_remove_service(matcher, args[1], args[4])
                return

            if len(args) == 4 and args[2] == 'ls' and args[3] == 'service':
                if args[1] == '*':
                    await handle_all_subjects_ls_service(matcher)
                else:
                    await handle_subject_ls_service(matcher, args[1])
                return

            # subject <主体> limit service <服务> to <次数> each <时间间隔>
            if len(args) == 9 and args[2] == 'limit' and args[3] == 'service' and args[5] == 'to' and args[7] == 'each':
                subject = args[1]
                service = args[4]
                limit = parse_integer(args[6])
                time_span = args[8]

                if (time_span.endswith('s')
                        or time_span.endswith('sec')
                        or time_span.endswith('second')
                        or time_span.endswith('seconds')):
                    time_span = timedelta(seconds=parse_integer(args[8]))
                elif (time_span.endswith('m')
                      or time_span.endswith('min')
                      or time_span.endswith('minute')
                      or time_span.endswith('minutes')):
                    time_span = timedelta(minutes=parse_integer(args[8]))
                elif (time_span.endswith('h')
                      or time_span.endswith('hour')
                      or time_span.endswith('hours')):
                    time_span = timedelta(hours=parse_integer(args[8]))
                elif (time_span.endswith('d')
                      or time_span.endswith('day')
                      or time_span.endswith('days')):
                    time_span = timedelta(days=parse_integer(args[8]))
                else:
                    await matcher.send("请指定时间单位（sec/min/hour/day）")

                await handle_subject_limit_service(matcher, subject, service, limit, time_span)
                return

            if len(args) == 5 and args[2] == 'rm' and args[3] == 'limit':
                ...
                return

            if len(args) == 4 and args[2] == 'ls' and args[3] == 'limit':
                if args[1] == '*':
                    ...
                else:
                    ...
                return
        elif args[0] == 'service':
            if len(args) == 3 and args[2] == 'ls':
                await handle_service_ls_subservice(matcher, args[1])
                return

            if len(args) == 4 and args[2] == 'ls' and args[3] == 'subject':
                await handle_service_ls_subject(matcher, args[1])
                return

    await matcher.send("未知指令，请使用/ac help查看帮助")


help_text = """
/ac help：显示此帮助

/ac subject <主体> allow service <服务>：为主体启用服务
/ac subject <主体> deny service <服务>：为主体禁用服务
/ac subject <主体> rm service <服务>：为主体删除服务权限配置
/ac subject <主体> ls service：列出主体已配置的服务权限
/ac subject * ls service：列出所有已配置的权限

/ac subject <主体> limit service <服务> to <次数> each <时间间隔>：为主体与服务添加限流规则（按照用户限流）
/ac subject <主体> rm limit <规则ID>
/ac subject <主体> ls limit：列出主体已配置的限流规则
/ac subject * ls limit：列出所有已配置的限流规则

/ac service <服务> ls：列出服务的子服务层级
/ac service <服务> ls subject：列出服务已配置的主体权限
""".strip()


async def handle_help(matcher: Matcher):
    await matcher.send(help_text)


async def handle_all_subjects_ls_service(matcher: Matcher):
    services = [x async for x in get_all_permissions()]
    if len(services) != 0:
        # 按照服务全称排序
        services = sorted(services, key=lambda x: x[0].qualified_name, reverse=True)
        msg = '\n'.join(map(lambda x: x[2] + (' allow ' if x[1] else ' deny ') + x[0].qualified_name, services))
    else:
        msg = "empty"
    await matcher.send(msg)


async def handle_subject_ls_service(matcher: Matcher, subject: str):
    services = [x async for x in get_services_by_subject(subject)]
    if len(services) != 0:
        # 按照先allow再deny排序
        services = sorted(services, key=lambda x: x[1], reverse=True)
        msg = '\n'.join(map(lambda x: x[0].qualified_name + (' allow' if x[1] else ' deny'), services))
    else:
        msg = "empty"
    await matcher.send(msg)


async def _get_service(matcher: Matcher, service_name: str) -> Service:
    service = get_service_by_qualified_name(service_name)

    if service is None:
        await matcher.finish("service not found")
    else:
        return service


async def handle_subject_allow_service(matcher: Matcher, subject: str, service_name: str):
    service = await _get_service(matcher, service_name)
    await service.set_permission(subject, True)
    await matcher.send("ok")


async def handle_subject_deny_service(matcher: Matcher, subject: str, service_name: str):
    service = await _get_service(matcher, service_name)
    await service.set_permission(subject, False)
    await matcher.send("ok")


async def handle_subject_remove_service(matcher: Matcher, subject: str, service_name: str):
    service = await _get_service(matcher, service_name)
    await service.remove_permission(subject)
    await matcher.send("ok")


async def handle_service_ls_subject(matcher: Matcher, service_name: str):
    permissions: Dict[str, Tuple[bool, Service]] = {}
    service: Optional[Service] = await _get_service(matcher, service_name)

    while service is not None:
        async for subject, allow in service.get_permissions():
            permissions.setdefault(subject, (allow, service))
        service = service.parent

    if len(permissions) != 0:
        # 按照先allow再deny排序
        ordered_permissions = sorted(
            [(*permissions[k], k) for k in permissions],
            reverse=True,
            key=lambda x: (x[0], x[1].qualified_name, x[2])
        )
        with StringIO() as sio:
            for allow, service, subject in ordered_permissions:
                sio.write(subject)
                if allow:
                    sio.write(" allow")
                else:
                    sio.write(" deny")

                if service.qualified_name != service_name:
                    sio.write(f" (inherited from {service.qualified_name})")
                sio.write('\n')
            msg = sio.getvalue().strip()
    else:
        msg = "empty"
    await matcher.send(msg)


async def handle_service_ls_subservice(matcher: Matcher, service_name: str):
    service = await _get_service(matcher, service_name)
    summary = get_tree_summary(service, lambda x: x.children, lambda x: x.name)
    await matcher.send(summary)


async def handle_subject_limit_service(matcher: Matcher,
                                       subject: str,
                                       service_name: str,
                                       limit: int,
                                       time_span: timedelta):
    if limit == 0:
        await matcher.send('限流次数必须大于0')
    else:
        service = await _get_service(matcher, service_name)
        await service.add_rate_limit_rule(subject, time_span, limit)
        await matcher.send('ok')
