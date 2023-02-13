from argparse import Namespace
from io import StringIO
from typing import cast, Dict, Tuple, Optional

from nonebot import on_shell_command
from nonebot.exception import ParserExit
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .handle_error import handle_error
from .parser import parser
from ..service import get_services_by_subject, Service, get_service_by_qualified_name
from ..service.methods import get_all_permissions
from ..utils.tree import get_tree_summary

cmd = on_shell_command("ac", parser=parser, permission=SUPERUSER)


@cmd.handle()
@handle_error()
async def _(matcher: Matcher, event: Event, state: T_State):
    args = state["_args"]
    if isinstance(args, ParserExit):
        await matcher.finish(args.message)

    args = cast(Namespace, args)

    if args.subcommand is None or args.subcommand == 'help':
        await handle_help(matcher)
    elif args.subcommand == 'ls':
        await handle_ls(matcher)
    elif args.subcommand == 'subject':
        if args.action == 'ls':
            if args.target == 'service':
                await handle_subject_ls_service(matcher, args.subject)
        elif args.action == 'allow':
            if args.target == 'service':
                await handle_subject_allow_service(matcher, args.subject, args.service)
        elif args.action == 'deny':
            if args.target == 'service':
                await handle_subject_deny_service(matcher, args.subject, args.service)
        elif args.action == 'remove' or args.action == 'rm':
            if args.target == 'service':
                await handle_subject_remove_service(matcher, args.subject, args.service)
    elif args.subcommand == 'service':
        if args.action == 'ls':
            if args.target is None:
                await handle_service_ls_subservice(matcher, args.service)
            elif args.target == 'subject':
                await handle_service_ls_subject(matcher, args.service)
        elif args.action == 'allow':
            if args.target == 'subject':
                await handle_subject_allow_service(matcher, args.subject, args.service)
        elif args.action == 'deny':
            if args.target == 'subject':
                await handle_subject_deny_service(matcher, args.subject, args.service)
        elif args.action == 'remove' or args.action == 'rm':
            if args.target == 'subject':
                await handle_subject_remove_service(matcher, args.subject, args.service)


help_text = """
/ac help：显示此帮助
/ac ls：列出所有权限配置
/ac subject <主体> allow service <服务>：为主体启用服务
/ac subject <主体> deny service <服务>：为主体禁用服务
/ac subject <主体> rm service <服务>：为主体删除服务权限配置
/ac subject <主体> ls service：列出主体已配置的服务权限
/ac service <服务> ls：列出服务的子服务层级
/ac service <服务> ls subject：列出服务已配置的主体权限
""".strip()


async def handle_help(matcher: Matcher):
    await matcher.send(help_text)


async def handle_ls(matcher: Matcher):
    services = [x async for x in get_all_permissions()]
    if len(services) != 0:
        # 按照服务全称排序
        services = sorted(services, key=lambda x: x[0].qualified_name, reverse=True)
        msg = '\n'.join(map(lambda x: x[0].qualified_name + (' allow' if x[1] else ' deny'), services))
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
