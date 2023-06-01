from nonebot import on_command
from nonebot.internal.matcher import Matcher

from .plugin_service import plugin_service

group1 = plugin_service.create_subservice("group1")

a_matcher = on_command('a', priority=99)
a_service = group1.create_subservice('a')
a_service.patch_matcher(a_matcher)


@a_matcher.handle()
async def _(matcher: Matcher):
    await matcher.send("a")


b_matcher = on_command('b', priority=99)
b_service = group1.create_subservice('b')
b_service.patch_matcher(b_matcher)


@b_matcher.handle()
async def _(matcher: Matcher):
    await matcher.send("b")


c_matcher = on_command('c', priority=99)
c_service = plugin_service.create_subservice('c')


@c_matcher.handle()
@c_service.patch_handler()
async def _(matcher: Matcher):
    await matcher.send("c")
