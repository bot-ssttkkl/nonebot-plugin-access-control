from typing import Callable, Dict, List

from nonebot import Bot, logger
from nonebot.internal.adapter import Event

T_SubjectExtractor = Callable[[Bot, Event], List[str]]

_subject_extractors: Dict[str, T_SubjectExtractor] = {}


def register_subject_extractor(adapter: str, subject_extractor: T_SubjectExtractor):
    _subject_extractors[adapter] = subject_extractor


def extract_subjects(bot: Bot, event: Event) -> List[str]:
    adapter = bot.adapter.get_name()
    subject_extractor = _subject_extractors.get(adapter, None)
    if subject_extractor is None:
        logger.warning(f"no subject extractor found for adapter {adapter}")

        adapter = adapter.split(maxsplit=1)[0].lower()
        return [f"{adapter}:unknown", adapter, "all"]
    return subject_extractor(bot, event)


__all__ = ("register_subject_extractor", "extract_subjects")
