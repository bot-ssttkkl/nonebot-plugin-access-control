from typing import List

from nonebot import Bot, logger
from nonebot.internal.adapter import Event

from .base import SubjectExtractor
from .session import SessionSubjectExtractor
from .union import UnionSubjectExtractor

union_subject_extractor = UnionSubjectExtractor(SessionSubjectExtractor())

try:
    from .onebot_v11 import OneBotV11SubjectExtractor

    union_subject_extractor.register(OneBotV11SubjectExtractor())
except ImportError:
    pass

try:
    from .onebot_v12 import OneBotV12SubjectExtractor

    union_subject_extractor.register(OneBotV12SubjectExtractor())
except ImportError:
    pass


def extract_subjects(bot: Bot, event: Event) -> List[str]:
    sbj = union_subject_extractor.extract(bot, event)
    logger.trace("subjects: " + ', '.join(sbj))
    return sbj


__all__ = ("extract_subjects",)
