from typing import TYPE_CHECKING, Optional, Sequence

from nonebot import Bot
from nonebot.internal.adapter import Event

from ...SubjectModel import SubjectModel

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11.event import Sender

OFFER_BY = "nonebot_plugin_access_control"


def extract_onebot_v11_group_role(bot: Bot, event: Event, current: Sequence[SubjectModel]) -> Sequence[SubjectModel]:
    if bot.type != "OneBot V11":
        return current

    group_id = getattr(event, "group_id", None)
    sender: Optional['Sender'] = getattr(event, "sender", None)

    if group_id is not None and sender is not None:
        li = []

        if sender.role == 'owner':
            li.append(SubjectModel(f"qq:g{group_id}.group_owner", OFFER_BY,
                                   f"qq:group.group_owner"))
            li.append(SubjectModel(f"qq:group_owner", OFFER_BY,
                                   f"qq:group_owner"))

        if sender.role == 'owner' or sender.role == 'admin':
            li.append(SubjectModel(f"qq:g{group_id}.group_admin", OFFER_BY,
                                   f"qq:group.group_admin"))
            li.append(SubjectModel(f"qq:group_admin", OFFER_BY,
                                   f"qq:group_admin"))

        # 添加在platform_group之前
        idx = 0
        for i in range(len(current)):
            if current[i].tag == "platform:group":
                idx = i
                break

        current = [*current[:idx], *li, *current[idx:]]

    return current
