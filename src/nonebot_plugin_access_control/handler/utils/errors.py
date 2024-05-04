from inspect import isawaitable
from collections.abc import Awaitable
from contextlib import asynccontextmanager
from typing import Any, Union, Callable, Optional

from nonebot.internal.matcher import current_matcher
from nonebot.exception import ActionFailed, MatcherException
from nonebot_plugin_access_control_api.errors import (
    AccessControlQueryError,
    AccessControlBadRequestError,
)

T_EXCEPTABLE = Union[type[BaseException], tuple[type[BaseException], ...]]
T_ERROR_HANDLER = Union[
    Callable[[BaseException], Optional[str]],
    Callable[[BaseException], Awaitable[Optional[str]]],
]


class ErrorHandlers:
    def __init__(self):
        self.handlers: list[tuple[T_EXCEPTABLE, T_ERROR_HANDLER]] = []

    def register(
        self, error_type: T_EXCEPTABLE, func: Optional[T_ERROR_HANDLER] = None
    ):
        def decorator(func: Optional[T_ERROR_HANDLER]):
            self.handlers.append((error_type, func))
            return func

        if func is not None:
            decorator(func)
        else:
            return decorator

    @asynccontextmanager
    async def run_excepting(
        self,
        receive_error_message: Optional[
            Union[Callable[[str], Any], Callable[[str], Awaitable[Any]]]
        ] = None,
        *,
        reraise_unhandled: bool = False,
    ):
        try:
            yield
        except MatcherException as e:
            raise e
        except ActionFailed as e:
            # 避免当发送消息错误时再尝试发送
            raise e
        except BaseException as e:
            for excs, handler in self.handlers:
                if not isinstance(excs, tuple):
                    excs = (excs,)

                for exc in excs:
                    if isinstance(e, exc):
                        msg = handler(e)
                        if isawaitable(msg):
                            msg = await msg

                        if msg:
                            coro = receive_error_message(msg)
                            if isawaitable(coro):
                                await coro
                        return

            if isinstance(e, (AccessControlBadRequestError, AccessControlQueryError)):
                msg = e.message

                matcher = None
                try:
                    matcher = current_matcher.get()
                except LookupError:
                    pass

                help_info = getattr(matcher, "__help_info__", None)
                if help_info is not None:
                    msg += f"\n\n指令用法：{help_info}"

                if msg:
                    coro = receive_error_message(msg)
                    if isawaitable(coro):
                        await coro
                return

            # fallback
            try:
                coro = receive_error_message(f"内部错误：{type(e)}{str(e)}")
                if isawaitable(coro):
                    await coro
            finally:
                if reraise_unhandled:
                    raise e  # 重新抛出未处理的异常
