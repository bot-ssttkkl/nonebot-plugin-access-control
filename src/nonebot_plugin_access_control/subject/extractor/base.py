from typing import Callable
from collections.abc import Sequence

from nonebot import Bot, logger
from nonebot.internal.adapter import Event

from ..model import SubjectModel

T_SubjectExtractor = Callable[
    [Bot, Event, Sequence[SubjectModel]], Sequence[SubjectModel]
]


class SubjectExtractorChain:
    def __init__(self, *extractors: T_SubjectExtractor):
        self.extractors = list(extractors)

    def __call__(
        self, bot: Bot, event: Event, current: Sequence[SubjectModel]
    ) -> Sequence[SubjectModel]:
        for ext in self.extractors:
            current = ext(bot, event, current)
            logger.trace("current subjects: " + ", ".join(map(str, current)))
        return current

    def add(self, extractor: T_SubjectExtractor):
        self.extractors.append(extractor)
