from typing import Literal

from nonebot import get_driver
from pydantic import BaseSettings


class Config(BaseSettings):
    access_control_database_conn_url: str = "sqlite+aiosqlite:///access_control.db"
    access_control_default_permission: Literal['allow', 'deny'] = 'allow'
    access_control_enable_patch: bool = True

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
