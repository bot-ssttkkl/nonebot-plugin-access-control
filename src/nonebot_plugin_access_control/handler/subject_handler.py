from typing import TextIO

from nonebot.internal.matcher import current_bot, current_event

from .utils.env import get_env
from ..errors import AccessControlBadRequestError
from ..subject import extract_subjects


async def subject(f: TextIO):
    if get_env() != "nonebot":
        raise AccessControlBadRequestError("该指令仅限聊天中使用")

    bot = current_bot.get()
    event = current_event.get()

    for sbj in extract_subjects(bot, event):
        f.write(sbj)
        f.write("\n")
