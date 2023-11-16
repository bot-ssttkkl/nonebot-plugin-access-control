from typing import TYPE_CHECKING, Optional

from nonebot import Bot
from nonebot.internal.adapter import Event

from nonebot_plugin_access_control_api.subject.model import SubjectModel
from nonebot_plugin_access_control_api.subject.manager import SubjectManager

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11.event import Sender

OFFER_BY = "nonebot_plugin_access_control"


def extract_onebot_v11_group_role(bot: Bot, event: Event, manager: SubjectManager):
    if bot.type != "OneBot V11":
        return

    group_id = getattr(event, "group_id", None)
    sender: Optional["Sender"] = getattr(event, "sender", None)

    if group_id is not None and sender is not None:
        li = []

        if sender.role == "owner":
            li.append(
                SubjectModel(
                    f"qq:g{group_id}.group_owner", OFFER_BY, "qq:group.group_owner"
                )
            )
            li.append(SubjectModel("qq:group_owner", OFFER_BY, "qq:group_owner"))

        if sender.role == "owner" or sender.role == "admin":
            li.append(
                SubjectModel(
                    f"qq:g{group_id}.group_admin", OFFER_BY, "qq:group.group_admin"
                )
            )
            li.append(SubjectModel("qq:group_admin", OFFER_BY, "qq:group_admin"))

        # 添加在platform:group之前
        manager.insert_before("platform:group", *li)
