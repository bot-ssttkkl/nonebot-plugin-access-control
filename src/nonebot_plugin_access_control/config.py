from typing import Literal, List

from nonebot import get_driver
from pydantic import BaseSettings, Field


class Config(BaseSettings):
    access_control_database_conn_url: str = "sqlite+aiosqlite:///access_control.db"
    access_control_default_permission: Literal['allow', 'deny'] = 'allow'
    access_control_auto_patch_enabled: bool = False
    access_control_auto_patch_ignore: List[str] = Field(default_factory=list)

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
