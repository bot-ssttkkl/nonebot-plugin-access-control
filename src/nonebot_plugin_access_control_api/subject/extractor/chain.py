from nonebot import Bot, logger
from nonebot.internal.adapter import Event

from ..model import SubjectModel
from ..manager import SubjectManager
from .base import T_SubjectExtractor
from ...utils.call_with_params import call_with_params


class SubjectExtractorChain:
    def __init__(self, *extractors: T_SubjectExtractor):
        self.extractors = list(extractors)

    def __call__(self, bot: Bot, event: Event, manager: SubjectManager):
        for ext in self.extractors:
            result = call_with_params(
                ext,
                {
                    "bot": bot,
                    "event": event,
                    "current": manager.subjects,
                    "manager": manager,
                },
            )
            # 如果返回值是Sequence[SubjectModel]
            if (
                result is not None
                and isinstance(result, (list, tuple))
                and all(isinstance(x, SubjectModel) for x in result)
            ):
                manager.replace(*result)

            logger.trace("current subjects: " + ", ".join(map(str, manager.subjects)))

    def add(self, extractor: T_SubjectExtractor):
        self.extractors.append(extractor)
