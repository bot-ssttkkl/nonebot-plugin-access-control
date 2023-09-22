from typing import TYPE_CHECKING, Optional, Sequence

from nonebot import Bot
from nonebot.internal.adapter import Event

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11.event import Sender


def extract_onebot_v11_group_role(bot: Bot, event: Event, current: Sequence[str]) -> Sequence[str]:
    if bot.type != "OneBot V11":
        return current

    li = [*current]

    group_id = getattr(event, "group_id", None)
    sender: Optional['Sender'] = getattr(event, "sender", None)

    if group_id is not None and sender is not None:
        # 添加群管理/群主的subject
        idx = li.index("qq:g{group_id}")
        if sender.role == 'owner':
            li.insert(idx + 1, f"qq:group_owner")
            li.insert(idx + 1, f"qq:g{group_id}.group_owner")

        if sender.role == 'owner' or sender.role == 'admin':
            li.insert(idx + 1, f"qq:group_admin")
            li.insert(idx + 1, f"qq:g{group_id}.group_admin")

    return li
