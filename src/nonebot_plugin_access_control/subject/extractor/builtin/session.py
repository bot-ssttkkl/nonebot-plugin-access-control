from typing import List, Sequence

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot_plugin_session import extract_session, SessionLevel, Session

from ...model import SubjectModel
from ....utils.superuser import is_superuser

OFFER_BY = "nonebot_plugin_access_control"


def _append_subject(li: List[SubjectModel],
                    content_body: str, content_prefix: Sequence[str],
                    tag: Sequence[str]):
    for i in range(min(len(content_prefix), len(tag))):
        li.append(SubjectModel(f"{content_prefix[i]}{content_body}", OFFER_BY, tag[i]))


def extract_from_session(session: Session) -> Sequence[SubjectModel]:
    if session.bot_type == "OneBot V11" or session.bot_type == "OneBot V12":
        prefix = [session.platform, "onebot"]
    else:
        prefix = [session.platform]

    li: List[SubjectModel] = []

    if session.level == SessionLevel.LEVEL3:
        user_id = session.id1
        channel_id = session.id2
        guild_id = session.id3

        _append_subject(li, f":g{guild_id}:c{channel_id}:{user_id}", prefix,
                        ["platform:guild:channel:user", "onebot:guild:channel:user"])
        _append_subject(li, f":c{channel_id}:{user_id}", prefix,
                        ["platform:channel:user", "onebot:channel:user"])
        _append_subject(li, f":g{guild_id}:{user_id}", prefix,
                        ["platform:guild:user", "onebot:guild:user"])
        _append_subject(li, f":{user_id}", prefix,
                        ["platform:user", "onebot:user"])

        if is_superuser(user_id, session.bot_type):
            li.append(SubjectModel("superuser", OFFER_BY, "superuser"))

        _append_subject(li, f":g{guild_id}:c{channel_id}", prefix,
                        ["platform:guild:channel", "onebot:guild:channel"])
        _append_subject(li, f":c{channel_id}", prefix,
                        ["platform:channel", "onebot:channel"])
        _append_subject(li, f":g{guild_id}", prefix,
                        ["platform:guild", "onebot:guild"])

        _append_subject(li, ":channel", prefix,
                        ["platform:chat_type", "onebot:chat_type"])
        li.append(SubjectModel("channel", OFFER_BY, "chat_type"))
    elif session.level == SessionLevel.LEVEL2:
        user_id = session.id1
        group_id = session.id2

        _append_subject(li, f":g{group_id}:{user_id}", prefix,
                        ["platform:group:user", "onebot:group:user"])
        _append_subject(li, f":{user_id}", prefix,
                        ["platform:user", "onebot:user"])

        if is_superuser(user_id, session.bot_type):
            li.append(SubjectModel("superuser", OFFER_BY, "superuser"))

        _append_subject(li, f":g{group_id}", prefix,
                        ["platform:group", "onebot:group"])
        _append_subject(li, ":group", prefix,
                        ["platform:chat_type", "onebot:chat_type"])
        li.append(SubjectModel("group", OFFER_BY, "chat_type"))
    elif session.level == SessionLevel.LEVEL1:
        user_id = session.id1

        _append_subject(li, f":{user_id}", prefix,
                        ["platform:user", "onebot:user"])

        if is_superuser(user_id, session.bot_type):
            li.append(SubjectModel("superuser", OFFER_BY, "superuser"))

        _append_subject(li, ":private", prefix,
                        ["platform:chat_type", "onebot:chat_type"])
        li.append(SubjectModel("private", OFFER_BY, "chat_type"))

    _append_subject(li, "", prefix,
                    ["platform", "onebot"])

    li.append(SubjectModel("all", OFFER_BY, "all"))

    return li


def extract_by_session(bot: Bot, event: Event, current: Sequence[SubjectModel]) -> Sequence[SubjectModel]:
    session = extract_session(bot, event)
    return [*current, *extract_from_session(session)]
