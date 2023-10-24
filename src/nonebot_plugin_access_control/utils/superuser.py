from nonebot import get_driver

superusers = get_driver().config.superusers


def is_superuser(user_id: str, bot_type: str) -> bool:
    return (
        f"{bot_type.split(maxsplit=1)[0].lower()}:{user_id}" in superusers
        or user_id in superusers  # 兼容旧配置
    )
