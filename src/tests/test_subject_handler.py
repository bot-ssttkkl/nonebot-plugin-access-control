from io import StringIO

import pytest
from nonebug import App

from tests.utils.ob11_event import SELF_ID, fake_ob11_group_message_event


@pytest.mark.asyncio
async def test_subject_handler(app: App):
    from nonebot import on_command
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_access_control.handler.subject_handler import subject
    from nonebot_plugin_access_control.handler.utils.env import ac_set_nonebot_env

    ac_set_nonebot_env()

    EXPECTED = (
        "qq:g34567:23456\n"
        "qq:23456\n"
        "qq:g34567\n"
        "qq:group\n"
        "group\n"
        "qq\n"
        "all"
    )

    subject_matcher = on_command("subject")

    @subject_matcher.handle()
    async def _():
        with StringIO() as f:
            await subject(f)

            res = f.getvalue()
            assert res.strip() == EXPECTED

    async with app.test_matcher(subject_matcher) as ctx:
        bot = ctx.create_bot(base=Bot, self_id=str(SELF_ID))
        event = fake_ob11_group_message_event("/subject")
        ctx.receive_event(bot, event)
