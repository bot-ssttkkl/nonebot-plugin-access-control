from typing import TYPE_CHECKING, Optional, Sequence, List

from nonebot import Bot
from nonebot.internal.adapter import Event

from ...model import SubjectModel

if TYPE_CHECKING:
    from nonebot.adapters.qqguild.event import Member

OFFER_BY = "nonebot_plugin_access_control"

PRESET_ROLES = {
    2: "guild_admin",
    4: "guild_owner",
    5: "channel_admin"
}

PRESET_ROLE_PRIORITY = (4, 2, 5)


def extract_qqguild_role(bot: Bot, event: Event, current: Sequence[SubjectModel]) -> Sequence[SubjectModel]:
    if bot.type != "QQ Guild":
        return current

    is_direct_msg = getattr(event, "src_guild_id", None) is not None
    if is_direct_msg:
        return current

    guild_id: Optional[str] = getattr(event, "guild_id", None)
    channel_id: Optional[str] = getattr(event, "channel_id", None)
    member: Optional['Member'] = getattr(event, "member", None)

    if member is not None:
        li = []

        for actual_role in sorted(member.roles):
            if actual_role in PRESET_ROLES:
                # 我们默认优先级高的预置角色（例如服务器主）继承优先级低的（例如频道管理员）
                priority = PRESET_ROLE_PRIORITY.index(actual_role)
                for i in range(priority, len(PRESET_ROLE_PRIORITY)):
                    role = PRESET_ROLE_PRIORITY[i]

                    if role == 5:  # 频道管理员
                        li.append(SubjectModel(f"qqguild:g{guild_id}:c{channel_id}.{PRESET_ROLES[role]}", OFFER_BY,
                                               f"qqguild:guild:channel.{PRESET_ROLES[role]}"))
                        li.append(SubjectModel(f"qqguild:c{channel_id}.{PRESET_ROLES[role]}", OFFER_BY,
                                               f"qqguild:channel:{PRESET_ROLES[role]}"))
                    else:
                        li.append(SubjectModel(f"qqguild:g{guild_id}.{PRESET_ROLES[role]}", OFFER_BY,
                                               f"qqguild:guild.{PRESET_ROLES[role]}"))
                    li.append(SubjectModel(f"qqguild:{PRESET_ROLES[role]}", OFFER_BY,
                                           f"qqguild:{PRESET_ROLES[role]}"))
            else:
                li.append(SubjectModel(f"qqguild:g{guild_id}.role_{actual_role}", OFFER_BY,
                                       f"qqguild:guild.role"))

        # 添加在platform_guild_channel之前
        idx = 0
        for i in range(len(current)):
            if current[i].tag == "platform:guild:channel":
                idx = i
                break

        current = [*current[:idx], *li, *current[idx:]]

    return current
