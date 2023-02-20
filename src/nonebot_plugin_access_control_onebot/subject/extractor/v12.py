from typing import Set, List

from nonebot import get_driver
from nonebot.adapters.onebot.v12 import Bot, Event

from nonebot_plugin_access_control.subject import SubjectExtractor
from nonebot_plugin_access_control.utils.superuser import is_superuser


class OneBotV12SubjectExtractor(SubjectExtractor[Bot, Event]):
    def __init__(self):
        self._supported_platform: Set[str] = set()

        driver = get_driver()

        @driver.on_bot_connect
        async def _(bot: Bot):
            self._supported_platform.add(bot.platform)

    def get_adapter_shortname(self) -> str:
        return 'onebot'

    def get_adapter_fullname(self) -> str:
        return 'OneBot V12'

    def is_platform_supported(self, platform: str) -> bool:
        return platform in self._supported_platform

    def extract(self, bot: Bot, event: Event) -> List[str]:
        user_id = getattr(event, "user_id", None)
        group_id = getattr(event, "group_id", None)
        channel_id = getattr(event, "channel_id", None)
        guild_id = getattr(event, "guild_id", None)

        li = []

        if user_id is not None:
            li.append(f"{bot.platform}:{user_id}")
            li.append(f"onebot:{user_id}")
            if is_superuser(bot, event):
                li.append("superuser")

        if group_id is not None:
            li.append(f"{bot.platform}:g{group_id}")
            li.append(f"onebot:g{group_id}")

        if channel_id is not None:
            li.append(f"{bot.platform}:c{channel_id}")
            li.append(f"onebot:c{channel_id}")

        if guild_id is not None:
            li.append(f"{bot.platform}:g{guild_id}")
            li.append(f"onebot:g{guild_id}")

        li.append(f"{bot.platform}")
        li.append("onebot")
        li.append("all")

        return li
