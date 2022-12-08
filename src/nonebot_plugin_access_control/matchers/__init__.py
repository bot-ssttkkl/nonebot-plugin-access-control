from argparse import Namespace
from typing import cast

from nonebot import on_shell_command
from nonebot.exception import ParserExit
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .handle_error import handle_error
from .parser import parser
from ..service import get_services_by_subject, Service, get_plugin_service

cmd = on_shell_command("ac", parser=parser, permission=SUPERUSER)


@cmd.handle()
@handle_error()
async def _(matcher: Matcher, event: Event, state: T_State):
    args = state["_args"]
    if isinstance(args, ParserExit):
        await matcher.finish(args.message)

    args = cast(Namespace, args)

    if args.subcommand == 'subject':
        if args.action == 'ls':
            await handle_subject_ls_service(matcher, args.subject)
        elif args.action == 'allow':
            await handle_subject_allow_service(matcher, args.subject, args.service)
        elif args.action == 'deny':
            await handle_subject_deny_service(matcher, args.subject, args.service)
        elif args.action == 'remove':
            await handle_subject_remove_service(matcher, args.subject, args.service)
    elif args.subcommand == 'service':
        if args.action == 'ls':
            await handle_service_ls_subject(matcher, args.service)


async def handle_subject_ls_service(matcher: Matcher, subject: str):
    services = [x async for x in get_services_by_subject(subject)]
    if len(services) != 0:
        # 按照先allow再deny排序
        services = sorted(services, key=lambda x: x[1], reverse=True)
        msg = '\n'.join(map(lambda x: x[0].qualified_name + (' allow' if x[1] else ' deny'), services))
    else:
        msg = "empty"
    await matcher.send(msg)


async def _get_service(matcher: Matcher, service: str) -> Service:
    if "." in service:
        plugin_name, service_name = service.split(".")
        service = get_plugin_service(plugin_name).find(service_name)
    else:
        service = get_plugin_service(service)

    if service is None:
        await matcher.finish("service not found")
    else:
        return service


async def handle_subject_allow_service(matcher: Matcher, subject: str, service: str):
    service = await _get_service(matcher, service)
    await service.set_permission(subject, True)
    await matcher.send("ok")


async def handle_subject_deny_service(matcher: Matcher, subject: str, service: str):
    service = await _get_service(matcher, service)
    await service.set_permission(subject, False)
    await matcher.send("ok")


async def handle_subject_remove_service(matcher: Matcher, subject: str, service: str):
    service = await _get_service(matcher, service)
    await service.remove_permission(subject)
    await matcher.send("ok")


async def handle_service_ls_subject(matcher: Matcher, service: str):
    service = await _get_service(matcher, service)
    permissions = [x async for x in service.get_permissions()]
    if len(permissions) != 0:
        # 按照先allow再deny排序
        permissions = sorted(permissions, key=lambda x: x[1], reverse=True)
        msg = '\n'.join(map(lambda x: x[0] + (' allow' if x[1] else ' deny'), permissions))
    else:
        msg = "empty"
    await matcher.send(msg)
