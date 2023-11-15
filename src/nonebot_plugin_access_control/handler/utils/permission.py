from functools import wraps

from nonebot.permission import SUPERUSER
from nonebot.internal.matcher import current_bot, current_event

from nonebot_plugin_access_control_api.errors import PermissionDeniedError

from .env import ac_get_env


def require_superuser_or_script(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        if ac_get_env() != "script":
            if not await SUPERUSER(current_bot.get(), current_event.get()):
                raise PermissionDeniedError()

        return await f(*args, **kwargs)

    return wrapper
