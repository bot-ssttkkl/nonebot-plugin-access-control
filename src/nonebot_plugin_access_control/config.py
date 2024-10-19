from typing import Literal, Optional

from nonebot import get_plugin_config
from pydantic import Field, BaseModel


class Config(BaseModel):
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


def conf() -> Config:
    return get_plugin_config(Config)
