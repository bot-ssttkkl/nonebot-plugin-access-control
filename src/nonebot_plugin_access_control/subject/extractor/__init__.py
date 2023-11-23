from collections.abc import Sequence

from nonebot import logger
from nonebot_plugin_access_control_api.subject.extractor import extractor_chain
from nonebot_plugin_session import Session

from .builtin.kaiheila import extract_kaiheila_role
from .builtin.onebot_v11 import extract_onebot_v11_group_role
from .builtin.qqguild import extract_qqguild_role
from .builtin.session import extract_by_session, extract_from_session

extractor_chain.add_first(
    extract_by_session,
    extract_onebot_v11_group_role,
    extract_qqguild_role,
    extract_kaiheila_role,
)
logger.debug(f"added default subject extractors")


def extract_subjects_from_session(session: Session) -> Sequence[str]:
    sbj = [x.content for x in extract_from_session(session)]
    logger.debug("subjects: " + ", ".join(sbj))
    return sbj


__all__ = ("extract_subjects_from_session",)
