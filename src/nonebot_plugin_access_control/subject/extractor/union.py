from typing import Dict, List

from nonebot import Bot, logger
from nonebot.internal.adapter import Event

from nonebot_plugin_access_control.subject.extractor.base import SubjectExtractor


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
        if subject_extractor is None:
            logger.warning(f"no subject extractor found for adapter {adapter}")

            adapter = adapter.split(maxsplit=1)[0].lower()
            return [f"{adapter}:unknown", adapter, "all"]
        return subject_extractor.extract(bot, event)


union_subject_extractor = UnionSubjectExtractor()
