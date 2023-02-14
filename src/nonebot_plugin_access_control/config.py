from typing import Literal, List, Optional

from nonebot import get_driver
from pydantic import BaseSettings, Field


class Config(BaseSettings):
    access_control_default_permission: Literal['allow', 'deny'] = 'allow'

    access_control_auto_patch_enabled: bool = False
    access_control_auto_patch_ignore: List[str] = Field(default_factory=list)

    access_control_reply_on_permission_denied: Optional[str]
    access_control_reply_on_rate_limited: Optional[str]

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
