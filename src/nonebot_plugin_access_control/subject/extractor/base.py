from typing import Protocol, Sequence

from nonebot import Bot, logger
from nonebot.internal.adapter import Event


class SubjectExtractor(Protocol):
    def __call__(self, bot: Bot, event: Event, current: Sequence[str]) -> Sequence[str]:
        ...


class SubjectExtractorChain(SubjectExtractor):
    def __init__(self, *extractors: SubjectExtractor):
        self.extractors = list(extractors)

    def __call__(self, bot: Bot, event: Event, current: Sequence[str]) -> Sequence[str]:
        for ext in self.extractors:
            current = ext(bot, event, current)
            logger.trace("current subjects: " + ', '.join(current))
        return current

    def add(self, extractor: SubjectExtractor):
        self.extractors.append(extractor)
