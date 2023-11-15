from typing import TextIO

from nonebot.internal.matcher import current_bot, current_event

from nonebot_plugin_access_control_api.subject import extract_subjects
from nonebot_plugin_access_control_api.errors import AccessControlBadRequestError

from .utils.env import ac_get_env


async def subject(f: TextIO):
    if ac_get_env() != "nonebot":
        raise AccessControlBadRequestError("该指令仅限聊天中使用")

    bot = current_bot.get()
    event = current_event.get()

    for sbj in extract_subjects(bot, event):
        f.write(sbj)
        f.write("\n")
