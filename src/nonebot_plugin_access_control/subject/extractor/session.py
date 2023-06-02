from typing import List

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot_plugin_session import extract_session, SessionLevel

from .base import SubjectExtractor
from ...utils.superuser import is_superuser


class SessionSubjectExtractor(SubjectExtractor[Bot, Event]):
    @classmethod
    def bot_type(cls) -> str:
        return ''

    def extract(self, bot: Bot, event: Event) -> List[str]:
        session = extract_session(bot, event)

        li = []

        if session.level == SessionLevel.LEVEL3:
            user_id = session.id1
            channel_id = session.id2
            guild_id = session.id3

            li.append(f"{session.platform}:g{guild_id}:c{channel_id}:{user_id}")
            li.append(f"{session.platform}:c{channel_id}:{user_id}")
            li.append(f"{session.platform}:g{guild_id}:{user_id}")

            li.append(f"{session.platform}:{user_id}")
            if is_superuser(bot, event):
                li.append("superuser")

            li.append(f"{session.platform}:g{guild_id}:c{channel_id}")
            li.append(f"{session.platform}:c{channel_id}")
            li.append(f"{session.platform}:g{guild_id}")
            li.append(f"{session.platform}:channel")
        elif session.level == SessionLevel.LEVEL2:
            user_id = session.id1
            group_id = session.id2

            li.append(f"{session.platform}:g{group_id}:{user_id}")
            li.append(f"{session.platform}:{user_id}")

            if is_superuser(bot, event):
                li.append("superuser")

            li.append(f"{session.platform}:g{group_id}")
            li.append(f"{session.platform}:group")
        elif session.level == SessionLevel.LEVEL1:
            user_id = session.id1

            li.append(f"{session.platform}:{user_id}")

            if is_superuser(bot, event):
                li.append("superuser")

            li.append(f"{session.platform}:private")

        li.append(session.platform)
        li.append("all")

        return li
