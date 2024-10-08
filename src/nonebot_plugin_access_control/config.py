from typing import Literal, Optional

from pydantic import Field
from nonebot import get_driver

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError as e:
        raise ImportError(
            "如果你正在使用pydantic v2，请手动安装pydantic-settings"
        ) from e


class Config(BaseSettings):
    access_control_default_permission: Literal["allow", "deny"] = "allow"

    access_control_rate_limit_token_storage: Literal["datastore", "inmemory"] = (
        "inmemory"
    )

    access_control_auto_patch_enabled: bool = False
    access_control_auto_patch_ignore: list[str] = Field(default_factory=list)

    access_control_reply_on_permission_denied_enabled: bool = False
    access_control_reply_on_permission_denied: str = "你没有权限执行该指令"
    access_control_reply_on_rate_limited_enabled: bool = True
    access_control_reply_on_rate_limited: Optional[str] = None

    class Config:
        extra = "ignore"


_conf: Optional[Config] = None


def conf() -> Config:
    global _conf
    if _conf is None:
        _conf = Config(**get_driver().config.dict())
    return _conf
