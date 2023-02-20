from nonebot import Bot
from nonebot.internal.adapter import Event


def is_superuser(bot: Bot, event: Event) -> bool:
    try:
        user_id = event.get_user_id()
    except Exception:
        return False
    return (
            f"{bot.adapter.get_name().split(maxsplit=1)[0].lower()}:{user_id}"
            in bot.config.superusers
            or user_id in bot.config.superusers  # 兼容旧配置
    )
