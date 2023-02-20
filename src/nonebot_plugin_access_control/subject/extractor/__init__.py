from typing import List

from nonebot import Bot
from nonebot.internal.adapter import Event

from .base import SubjectExtractor
from .union import UnionSubjectExtractor, union_subject_extractor


def extract_subjects(bot: Bot, event: Event) -> List[str]:
    return union_subject_extractor.extract(bot, event)


__all__ = ("SubjectExtractor", "UnionSubjectExtractor", "union_subject_extractor", "extract_subjects")
