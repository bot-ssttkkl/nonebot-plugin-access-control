import pytest
from nonebug import App

from .utils.event import fake_ob11_group_message_event, SELF_ID


@pytest.mark.asyncio
async def test_permission(app: App):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot_plugin_ac_demo.matcher_demo import a_matcher, b_matcher, c_matcher, group1
    from nonebot_plugin_access_control_api.service import get_nonebot_service

    # service: nonebot
    # subject: all
    # deny
    await get_nonebot_service().set_permission("all", False)
    # service: nonebot_plugin_ac_demo.group1
    # subject: qq:23456
    # allow all
    await group1.set_permission("qq:23456", True)

    async with app.test_matcher(a_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/a")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "a")

    async with app.test_matcher(b_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/b")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "b")

    async with app.test_matcher(c_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/c")
        ctx.receive_event(bot, event)
