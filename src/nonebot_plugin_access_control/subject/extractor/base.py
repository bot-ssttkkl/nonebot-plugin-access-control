from typing import Sequence, Callable

from nonebot import Bot, logger
from nonebot.internal.adapter import Event

T_SubjectExtractor = Callable[[Bot, Event, Sequence[str]], Sequence[str]]


class SubjectExtractorChain:
    def __init__(self, *extractors: T_SubjectExtractor):
        self.extractors = list(extractors)

    def __call__(self, bot: Bot, event: Event, current: Sequence[str]) -> Sequence[str]:
        for ext in self.extractors:
            current = ext(bot, event, current)
            logger.trace("current subjects: " + ', '.join(current))
        return current

    def add(self, extractor: T_SubjectExtractor):
        self.extractors.append(extractor)
