from typing import TYPE_CHECKING, Optional, Sequence

from nonebot import Bot
from nonebot.internal.adapter import Event

if TYPE_CHECKING:
    from nonebot.adapters.kaiheila.event import User, Event as KaiheilaEvent


def extract_kaiheila_role(bot: Bot, event: Event, current: Sequence[str]) -> Sequence[str]:
    if bot.type != "Kaiheila":
        return current

    li = [*current]

    event: KaiheilaEvent

    guild_id: Optional[str] = event.extra.guild_id
    channel_id: Optional[str] = getattr(event, "group_id", None) or getattr(event.extra.body, "channel_id", None)
    author: Optional['User'] = event.extra.author

    if author is not None:
        # 添加qqguild:role_xxx的subject（在"kaiheila:g{guild_id}:c{channel_id}"之前）
        idx = li.index(f"kaiheila:g{guild_id}:c{channel_id}")
        for role in reversed(sorted(author.roles)):
            li.insert(idx, f"kaiheila:g{guild_id}:role_{role}")

    return li
