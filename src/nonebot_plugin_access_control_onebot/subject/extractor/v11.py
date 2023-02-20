from typing import Optional

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.event import Sender

from nonebot_plugin_access_control.subject import SubjectExtractor
from nonebot_plugin_access_control.utils.superuser import is_superuser


class OneBotV11SubjectExtractor(SubjectExtractor[Bot, Event]):
    def get_adapter_shortname(self) -> str:
        return 'onebot'

    def get_adapter_fullname(self) -> str:
        return 'OneBot V11'

    def is_platform_supported(self, platform: str) -> bool:
        return platform == 'qq'

    def extract(self, bot: Bot, event: Event):
        li = []

        user_id = getattr(event, "user_id", None)
        if user_id is not None:
            li.append(f"qq:{user_id}")
            li.append(f"onebot:{user_id}")

            if is_superuser(bot, event):
                li.append("superuser")

        group_id = getattr(event, "group_id", None)
        if group_id is not None:
            li.append(f"qq:g{group_id}")
            li.append(f"onebot:g{group_id}")

            sender: Optional[Sender] = getattr(event, "sender", None)
            if sender is not None:
                if sender.role == 'owner':
                    li.append(f"qq:group_owner")
                    li.append(f"qq:g{group_id}.group_owner")

                if sender.role == 'owner' or sender.role == 'admin':
                    li.append(f"qq:group_admin")
                    li.append(f"qq:g{group_id}.group_admin")

        li.append("qq")
        li.append("onebot")
        li.append("all")

        return li
