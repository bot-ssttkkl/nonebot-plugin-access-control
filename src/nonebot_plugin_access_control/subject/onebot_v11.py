from nonebot import logger

from .extractor import register_subject_extractor

try:
    from nonebot.adapters.onebot.v11 import Bot, Event
    from nonebot.adapters.onebot.v11.adapter import Adapter


    def onebot_v11_subject_extractor(bot: Bot, event: Event):
        user_id = getattr(event, "user_id", None)
        group_id = getattr(event, "group_id", None)

        li = []

        if user_id is not None:
            li.append(f"onebot:{user_id}")

        if group_id is not None:
            li.append(f"onebot:g{group_id}")

        li.append("onebot")
        li.append("all")

        return li


    register_subject_extractor(Adapter.get_name(), onebot_v11_subject_extractor)
    logger.trace(f"registered subject extractor for {Adapter.get_name()}")
except ImportError:
    pass
