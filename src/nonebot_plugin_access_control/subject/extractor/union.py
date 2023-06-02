from typing import Dict, List

from nonebot import Bot, logger
from nonebot.internal.adapter import Event

from .base import SubjectExtractor


class UnionSubjectExtractor(SubjectExtractor[Bot, Event]):
    def __init__(self, fallback: SubjectExtractor[Bot, Event]):
        self._extractors: Dict[str, SubjectExtractor] = {}
        self.fallback = fallback

    def register(self, extractor: SubjectExtractor):
        self._extractors[extractor.bot_type()] = extractor
        logger.trace(f"registered subject extractor for {extractor.bot_type()}")

    @classmethod
    def bot_type(cls) -> str:
        return ''

    def extract(self, bot: Bot, event: Event) -> List[str]:
        subject_extractor = self._extractors.get(bot.type, None)
        if subject_extractor is not None:
            return subject_extractor.extract(bot, event)
        else:
            return self.fallback.extract(bot, event)
