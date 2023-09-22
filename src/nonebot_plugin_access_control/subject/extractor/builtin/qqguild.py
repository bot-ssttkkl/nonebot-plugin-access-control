from typing import TYPE_CHECKING, Optional, Sequence

from nonebot import Bot
from nonebot.internal.adapter import Event

if TYPE_CHECKING:
    from nonebot.adapters.qqguild.event import Member

PRESET_ROLES = {
    2: "guild_admin",
    4: "guild_owner",
    5: "channel_admin"
}


def extract_qqguild_role(bot: Bot, event: Event, current: Sequence[str]) -> Sequence[str]:
    if bot.type != "QQ Guild":
        return current

    is_direct_msg = getattr(event, "src_guild_id", None) is not None
    if is_direct_msg:
        return current

    li = [*current]

    guild_id: Optional[str] = getattr(event, "guild_id", None)
    channel_id: Optional[str] = getattr(event, "channel_id", None)
    member: Optional['Member'] = getattr(event, "member", None)

    if member is not None:
        # 添加qqguild:role_xxx的subject（在"qqguild:g{guild_id}:c{channel_id}"之前）
        idx = li.index(f"qqguild:g{guild_id}:c{channel_id}")
        for role in reversed(sorted(member.roles)):
            if role in PRESET_ROLES:
                li.insert(idx, f"qqguild:{PRESET_ROLES[role]}")
                li.insert(idx, f"qqguild:g{guild_id}.{PRESET_ROLES[role]}")
                if role == 5:  # 频道管理员
                    li.insert(idx, f"qqguild:c{channel_id}.{PRESET_ROLES[role]}")
                    li.insert(idx, f"qqguild:g{guild_id}:c{channel_id}.{PRESET_ROLES[role]}")
            else:
                li.insert(idx, f"qqguild:g{guild_id}.role_{role}")

    return li
