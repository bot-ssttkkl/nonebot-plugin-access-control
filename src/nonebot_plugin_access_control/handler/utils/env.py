from typing import Literal

T_ENV = Literal["nonebot", "script"]

_env: T_ENV = "nonebot"


def ac_set_script_env():
    global _env
    _env = "script"


def ac_get_env() -> T_ENV:
    return _env
