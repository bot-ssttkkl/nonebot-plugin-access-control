from asyncio import sleep
from datetime import timedelta

import pytest
from nonebug import App

from .utils.event import fake_ob11_group_message_event, SELF_ID


@pytest.mark.asyncio
async def test_rate_limit(app: App):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot_plugin_ac_demo.matcher_demo import a_matcher, b_matcher, c_matcher, group1
    from nonebot_plugin_access_control_api.service import get_nonebot_service

    # service: nonebot
    # subject: all
    # span: 1s
    # limit: 1
    await get_nonebot_service().add_rate_limit_rule("all", timedelta(seconds=1), 2)
    # service: nonebot_plugin_ac_demo.group1
    # subject: qq
    # span: 2s
    # limit: 2
    await group1.add_rate_limit_rule("qq:23456", timedelta(seconds=1), 1)

    async with app.test_matcher(a_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/a")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "a")

    await sleep(0.5)

    async with app.test_matcher(b_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/b")
        ctx.receive_event(bot, event)

    async with app.test_matcher(c_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/c")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "c")

    await sleep(0.6)

    async with app.test_matcher(b_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/b")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "b")
