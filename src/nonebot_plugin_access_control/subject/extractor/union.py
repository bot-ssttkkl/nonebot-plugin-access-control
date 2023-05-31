from typing import Dict, List

from nonebot import Bot, logger
from nonebot.internal.adapter import Event
from nonebot_plugin_session import extract_session

from nonebot_plugin_access_control.subject.extractor.base import SubjectExtractor
from nonebot_plugin_access_control.utils.superuser import is_superuser


class UnionSubjectExtractor(SubjectExtractor[Bot, Event]):
    def __init__(self):
        self._extractors: Dict[str, SubjectExtractor] = {}

    def register(self, extractor: SubjectExtractor):
        self._extractors[extractor.get_adapter_fullname()] = extractor
        logger.trace(f"registered subject extractor for {extractor.get_adapter_fullname()}")

    def get_adapter_shortname(self) -> str:
        return ''

    def get_adapter_fullname(self) -> str:
        return ''

    def is_platform_supported(self, platform: str) -> bool:
        for extractor in self._extractors.values():
            if extractor.is_platform_supported(platform):
                return True
        return False

    def extract(self, bot: Bot, event: Event) -> List[str]:
        adapter = bot.adapter.get_name()
        subject_extractor = self._extractors.get(adapter, None)
        if subject_extractor is not None:
            return subject_extractor.extract(bot, event)

        session = extract_session(bot, event)

        li = []

        user_id = session.id1
        channel_id = session.id2
        guild_id = session.id3

        if user_id is not None:
            if channel_id is not None:
                if guild_id is not None:
                    li.append(f"{session.platform}:g{guild_id}:c{channel_id}:{user_id}")
                    li.append(f"{session.platform}:c{channel_id}:{user_id}")
                else:
                    li.append(f"{session.platform}:g{channel_id}:{user_id}")

            li.append(f"{session.platform}:{user_id}")
            if is_superuser(bot, event):
                li.append("superuser")

        if channel_id is not None:
            if guild_id is not None:
                li.append(f"{session.platform}:g{guild_id}:c{channel_id}")
                li.append(f"{session.platform}:c{channel_id}")
            else:
                li.append(f"{session.platform}:g{channel_id}")

        if guild_id is not None:
            li.append(f"{session.platform}:g{guild_id}")

        if user_id is not None and channel_id is None and guild_id is None:
            li.append(f"{session.platform}:private")

        if user_id is not None and channel_id is not None and guild_id is None:
            li.append(f"{session.platform}:group")

        if user_id is not None and channel_id is not None and guild_id is not None:
            li.append(f"{session.platform}:channel")

        li.append(session.platform)
        li.append("all")

        return li


union_subject_extractor = UnionSubjectExtractor()
