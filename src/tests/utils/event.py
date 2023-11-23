import time
from random import randint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent

SELF_ID = 12345


def fake_ob11_group_message_event(content: str, user_id: int = 23456, group_id=34567) -> "GroupMessageEvent":
    from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent
    from nonebot.adapters.onebot.v11.event import Sender

    return GroupMessageEvent(
        time=int(time.time()),
        self_id=SELF_ID,
        message=Message(content),
        post_type="message",
        message_type="group",
        sub_type="",
        user_id=user_id,
        message_id=randint(1, 10000),
        original_message=Message(content),
        raw_message=content,
        font=0,
        sender=Sender(user_id=user_id, nickname=str(user_id)),
        group_id=group_id)
