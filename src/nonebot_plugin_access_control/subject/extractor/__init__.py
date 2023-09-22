from typing import List

from nonebot import Bot, logger
from nonebot.internal.adapter import Event
from nonebot_plugin_session import Session

from .base import SubjectExtractor, SubjectExtractorChain
from .builtin.session import extract_by_session, extract_from_session
from .builtin.onebot_v11 import extract_onebot_v11_group_role

extractor_chain = SubjectExtractorChain(
    extract_by_session,
    extract_onebot_v11_group_role
)


def add_subject_extractor(extractor: SubjectExtractor) -> SubjectExtractor:
    extractor_chain.add(extractor)
    return extractor


def extract_subjects(bot: Bot, event: Event) -> List[str]:
    sbj = extractor_chain(bot, event, [])
    logger.debug("subjects: " + ', '.join(sbj))
    return sbj


def extract_subjects_from_session(session: Session) -> List[str]:
    sbj = extract_from_session(session)
    logger.debug("subjects: " + ', '.join(sbj))
    return sbj


__all__ = ("SubjectExtractor", "add_subject_extractor",
           "extract_subjects", "extract_subjects_from_session")
