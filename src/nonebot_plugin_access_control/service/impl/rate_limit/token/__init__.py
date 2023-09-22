from nonebot import logger

from nonebot_plugin_access_control import conf
from .interface import TokenStorage

if conf.access_control_rate_limit_token_storage == 'datastore':
    from .datastore import get_datastore_token_storage

    get_token_storage = get_datastore_token_storage
    logger.opt(colors=True).info("use <y>datastore</y> token storage")
elif conf.access_control_rate_limit_token_storage == 'inmemory':
    from .inmemory import get_inmemory_token_storage

    get_token_storage = get_inmemory_token_storage
    logger.opt(colors=True).info("use <y>inmemory</y> token storage")
else:
    raise RuntimeError(f"invalid access_control_rate_limit_token_storage: "
                       f"{conf.access_control_rate_limit_token_storage}")

__all__ = ("get_token_storage", "TokenStorage")
