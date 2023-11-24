import pytest
from nonebug import App

from .utils.ob11_event import SELF_ID, fake_ob11_group_message_event


@pytest.mark.asyncio
async def test_permission(app: App):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot_plugin_access_control_api.service import get_nonebot_service

    from nonebot_plugin_ac_demo.matcher_demo import (
        group1,
        a_matcher,
        b_matcher,
        b_service,
        c_matcher,
    )

    # service: nonebot_plugin_ac_demo.group1
    # subject: qq
    # allow
    await group1.set_permission("qq", True)
    # service: nonebot_plugin_ac_demo.group.b
    # subject: qq:23456
    # deny
    await b_service.set_permission("qq:23456", False)

    async with app.test_matcher(a_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/a")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "a")

    async with app.test_matcher(b_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/b")
        ctx.receive_event(bot, event)

    async with app.test_matcher(c_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/c")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "c")

    # service: nonebot
    # subject: all
    # deny
    await get_nonebot_service().set_permission("all", False)

    async with app.test_matcher(a_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/a")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "a")

    async with app.test_matcher(b_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/b")
        ctx.receive_event(bot, event)

    async with app.test_matcher(c_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/c")
        ctx.receive_event(bot, event)
