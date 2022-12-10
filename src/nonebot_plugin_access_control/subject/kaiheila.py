from nonebot import logger

from .extractor import register_subject_extractor

try:
    from nonebot.adapters.kaiheila import Bot, Event
    from nonebot.adapters.kaiheila.adapter import Adapter


    def kaiheila_subject_extractor(bot: Bot, event: Event):
        li = []

        user_id = getattr(event, "user_id", None)
        if user_id is not None:
            li.append(f"kaiheila:{user_id}")

        channel_id = getattr(event, "channel_id", None)
        if channel_id is not None:
            li.append(f"kaiheila:c{channel_id}")

        if event.extra.guild_id is not None:
            li.append(f"kaiheila:g{event.extra.guild_id}")

        li.append("kaiheila")
        li.append("all")

        return li


    register_subject_extractor(Adapter.get_name(), kaiheila_subject_extractor)
    logger.trace(f"registered subject extractor for {Adapter.get_name()}")
except ImportError:
    pass
