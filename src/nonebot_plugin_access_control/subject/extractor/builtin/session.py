from typing import List, Sequence

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot_plugin_session import extract_session, SessionLevel, Session

from ....utils.superuser import is_superuser


def _append_with_tags(li: List[str], body: str, tags: Sequence[str]):
    for t in tags:
        li.append(f"{t}:{body}")


def extract_from_session(session: Session) -> Sequence[str]:
    if session.bot_type == "OneBot V11" or session.bot_type == "OneBot V12":
        tags = [session.platform, "onebot"]
    else:
        tags = [session.platform]

    li = []

    if session.level == SessionLevel.LEVEL3:
        user_id = session.id1
        channel_id = session.id2
        guild_id = session.id3

        _append_with_tags(li, f"g{guild_id}:c{channel_id}:{user_id}", tags)
        _append_with_tags(li, f"c{channel_id}:{user_id}", tags)
        _append_with_tags(li, f"g{guild_id}:{user_id}", tags)
        _append_with_tags(li, f"{user_id}", tags)

        if is_superuser(user_id, session.bot_type):
            li.append("superuser")

        _append_with_tags(li, f"g{guild_id}:c{channel_id}", tags)
        _append_with_tags(li, f"c{channel_id}", tags)
        _append_with_tags(li, f"g{guild_id}", tags)

        _append_with_tags(li, f"channel", tags)
    elif session.level == SessionLevel.LEVEL2:
        user_id = session.id1
        group_id = session.id2

        _append_with_tags(li, f"g{group_id}:{user_id}", tags)
        _append_with_tags(li, f"{user_id}", tags)

        if is_superuser(user_id, session.bot_type):
            li.append("superuser")

        _append_with_tags(li, f"g{group_id}", tags)
        _append_with_tags(li, f"group", tags)
    elif session.level == SessionLevel.LEVEL1:
        user_id = session.id1

        _append_with_tags(li, f"{user_id}", tags)

        if is_superuser(user_id, session.bot_type):
            li.append("superuser")

        _append_with_tags(li, f"private", tags)

    for t in tags:
        li.append(t)

    li.append("all")

    return li


def extract_by_session(bot: Bot, event: Event, current: Sequence[str]) -> Sequence[str]:
    session = extract_session(bot, event)
    return [*current, *extract_from_session(session)]
