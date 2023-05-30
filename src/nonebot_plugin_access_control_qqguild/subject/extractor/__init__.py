from nonebot.adapters.qqguild import Bot, Event
from nonebot.adapters.qqguild.event import MessageEvent

from nonebot_plugin_access_control.subject import SubjectExtractor


class QQGuildSubjectExtractor(SubjectExtractor[Bot, Event]):
    def get_adapter_shortname(self) -> str:
        return 'qqguild'

    def get_adapter_fullname(self) -> str:
        return 'QQ Guild'

    def is_platform_supported(self, platform: str) -> bool:
        return platform == 'qqguild'

    def extract(self, bot: Bot, event: Event):
        li = []

        if isinstance(event, MessageEvent):
            user_id = event.author.id
            if user_id is not None:
                li.append(f"qqguild:{user_id}")

            channel_id = event.channel_id
            if channel_id is not None:
                li.append(f"qqguild:c{channel_id}")

            guild_id = event.guild_id
            if guild_id is not None:
                li.append(f"qqguild:g{guild_id}")

        li.append("qqguild")
        li.append("all")

        return li
