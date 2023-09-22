from typing import Sequence

from nonebot import Bot, logger
from nonebot.internal.adapter import Event
from nonebot_plugin_session import Session

from .base import T_SubjectExtractor, SubjectExtractorChain
from .builtin.onebot_v11 import extract_onebot_v11_group_role
from .builtin.session import extract_by_session, extract_from_session

extractor_chain = SubjectExtractorChain(
    extract_by_session,
    extract_onebot_v11_group_role
)


def add_subject_extractor(extractor: T_SubjectExtractor) -> T_SubjectExtractor:
    extractor_chain.add(extractor)
    return extractor


def extract_subjects(bot: Bot, event: Event) -> Sequence[str]:
    sbj = extractor_chain(bot, event, [])
    logger.debug("subjects: " + ', '.join(sbj))
    return sbj


def extract_subjects_from_session(session: Session) -> Sequence[str]:
    sbj = extract_from_session(session)
    logger.debug("subjects: " + ', '.join(sbj))
    return sbj


__all__ = ("T_SubjectExtractor", "add_subject_extractor",
           "extract_subjects", "extract_subjects_from_session")
