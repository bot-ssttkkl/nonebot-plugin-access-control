from typing import TYPE_CHECKING, Optional

from nonebot import Bot
from nonebot.internal.adapter import Event

from nonebot_plugin_access_control_api.subject.model import SubjectModel
from nonebot_plugin_access_control_api.subject.manager import SubjectManager

if TYPE_CHECKING:
    from nonebot.adapters.kaiheila.event import User
    from nonebot.adapters.kaiheila.event import Event as KaiheilaEvent

OFFER_BY = "nonebot_plugin_access_control"


def extract_kaiheila_role(bot: Bot, event: Event, manager: SubjectManager):
    if bot.type != "Kaiheila":
        return

    event: KaiheilaEvent

    guild_id: Optional[str] = event.extra.guild_id
    getattr(event, "group_id", None) or getattr(event.extra.body, "channel_id", None)
    author: Optional["User"] = event.extra.author

    if author is not None:
        li = []

        for role in sorted(author.roles):
            li.append(
                SubjectModel(
                    f"kaiheila:g{guild_id}.role_{role}", OFFER_BY, "kaiheila:guild.role"
                )
            )

        # 添加在platform:guild:channel之前
        manager.insert_before("platform:guild:channel", *li)
