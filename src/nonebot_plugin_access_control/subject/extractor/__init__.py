from typing import List

from nonebot import Bot, logger
from nonebot.internal.adapter import Event

from .base import SubjectExtractor
from .union import UnionSubjectExtractor, union_subject_extractor


def extract_subjects(bot: Bot, event: Event) -> List[str]:
    sbj = union_subject_extractor.extract(bot, event)
    logger.trace("subjects: " + ', '.join(sbj))
    return sbj


__all__ = ("SubjectExtractor", "UnionSubjectExtractor", "union_subject_extractor", "extract_subjects")
