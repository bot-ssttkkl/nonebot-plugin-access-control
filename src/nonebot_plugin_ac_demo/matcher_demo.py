from nonebot import on_command
from nonebot.internal.matcher import Matcher
from nonebot_plugin_access_control_api.service.contextvars import (
    current_rate_limit_token,
)

from .plugin_service import plugin_service

group1 = plugin_service.create_subservice("group1")

a_matcher = on_command("a", priority=99)
a_service = group1.create_subservice("a")
a_service.patch_matcher(a_matcher)


@a_matcher.handle()
async def _(matcher: Matcher):
    await matcher.send("a")


b_matcher = on_command("b", priority=99)
b_service = group1.create_subservice("b")


@b_matcher.handle()
@b_service.patch_handler()
async def _(matcher: Matcher):
    await matcher.send("b")


c_matcher = on_command("c", priority=99)
c_service = plugin_service.create_subservice("c")


@c_matcher.handle()
@c_service.patch_handler()
async def _(matcher: Matcher):
    await matcher.send("c")


d_counter = 0

d_matcher = on_command("d", priority=99)
d_service = plugin_service.create_subservice("d")


@d_matcher.handle()
@d_service.patch_handler()
async def _(matcher: Matcher):
    global d_counter
    d_counter += 1
    if d_counter % 2 == 0:
        await current_rate_limit_token.get().retire()
        await matcher.send("retired")
    else:
        await matcher.send("d")
