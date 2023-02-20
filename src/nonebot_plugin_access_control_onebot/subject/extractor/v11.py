from nonebot.adapters.onebot.v11 import Bot, Event

from nonebot_plugin_access_control.subject import SubjectExtractor


class OneBotV11SubjectExtractor(SubjectExtractor[Bot, Event]):
    def get_adapter_shortname(self) -> str:
        return 'onebot'

    def get_adapter_fullname(self) -> str:
        return 'OneBot V11'

    def is_platform_supported(self, platform: str) -> bool:
        return platform == 'qq'

    def extract(self, bot: Bot, event: Event):
        user_id = getattr(event, "user_id", None)
        group_id = getattr(event, "group_id", None)

        li = []

        if user_id is not None:
            li.append(f"qq:{user_id}")
            li.append(f"onebot:{user_id}")

        if group_id is not None:
            li.append(f"qq:g{group_id}")
            li.append(f"onebot:g{group_id}")

        li.append("qq")
        li.append("onebot")
        li.append("all")

        return li
