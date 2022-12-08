from nonebot import on_command
from nonebot.internal.matcher import Matcher

from .plugin_service import plugin_service

group1 = plugin_service.create_subservice("group1")


@on_command('a', rule=group1.create_subservice("a")).handle()
async def _(matcher: Matcher):
    await matcher.send("a")


@on_command('b', rule=group1.create_subservice("b")).handle()
async def _(matcher: Matcher):
    await matcher.send("b")


@on_command('c', rule=plugin_service.create_subservice("c")).handle()
async def _(matcher: Matcher):
    await matcher.send("c")
