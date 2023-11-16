from nonebot import logger

from ...config import conf
from .interface import IRateLimitTokenRepository

if conf().access_control_rate_limit_token_storage == "datastore":
    from . import datastore  # noqa

    logger.opt(colors=True).info("use <y>datastore</y> rate_limit_token storage")
elif conf().access_control_rate_limit_token_storage == "inmemory":
    from . import inmemory  # noqa

    logger.opt(colors=True).info("use <y>inmemory</y> rate_limit_token storage")
else:
    raise RuntimeError(
        f"invalid access_control_rate_limit_token_storage: "
        f"{conf().access_control_rate_limit_token_storage}"
    )

__all__ = ("IRateLimitTokenRepository",)
