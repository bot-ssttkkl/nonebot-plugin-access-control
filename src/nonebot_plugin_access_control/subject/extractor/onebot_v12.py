from typing import List

from nonebot.adapters.onebot.v12 import Bot, Event

from .session import SessionSubjectExtractor


class OneBotV12SubjectExtractor(SessionSubjectExtractor):
    @classmethod
    def bot_type(cls) -> str:
        return 'OneBot V12'

    def extract(self, bot: Bot, event: Event) -> List[str]:
        res = super().extract(bot, event)

        li = []
        for sbj in res:
            li.append(sbj)
            if sbj.startswith(f"{bot.platform}:"):
                li.append(sbj.replace(f"{bot.platform}:", "onebot:"))

        return li
