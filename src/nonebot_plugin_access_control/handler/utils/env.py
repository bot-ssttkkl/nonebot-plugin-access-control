from typing import Literal

T_ENV = Literal["nonebot", "script"]

_env: T_ENV = "nonebot"


def set_script_env():
    global _env
    _env = "script"


def get_env() -> T_ENV:
    return _env
