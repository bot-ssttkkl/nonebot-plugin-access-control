from typing import TYPE_CHECKING, Optional, Sequence, List

from nonebot import Bot
from nonebot.internal.adapter import Event

from ...model import SubjectModel

if TYPE_CHECKING:
    from nonebot.adapters.kaiheila.event import User, Event as KaiheilaEvent

OFFER_BY = "nonebot_plugin_access_control"


def extract_kaiheila_role(bot: Bot, event: Event, current: Sequence[SubjectModel]) -> Sequence[SubjectModel]:
    if bot.type != "Kaiheila":
        return current

    event: KaiheilaEvent

    guild_id: Optional[str] = event.extra.guild_id
    channel_id: Optional[str] = getattr(event, "group_id", None) or getattr(event.extra.body, "channel_id", None)
    author: Optional['User'] = event.extra.author

    if author is not None:
        li = []

        for role in sorted(author.roles):
            li.append(SubjectModel(f"kaiheila:g{guild_id}.role_{role}", OFFER_BY,
                                   f"kaiheila:guild.role"))

        # 添加在platform_guild_channel之前
        idx = 0
        for i in range(len(current)):
            if current[i].tag == "platform:guild:channel":
                idx = i
                break

        current = [*current[:idx], *li, *current[idx:]]

    return current
