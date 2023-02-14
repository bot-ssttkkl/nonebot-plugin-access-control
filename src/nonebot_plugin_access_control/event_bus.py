from asyncio import gather
from collections import defaultdict
from enum import Enum
from inspect import isawaitable, signature
from typing import Dict, List, Callable, Awaitable, Any, Tuple, Optional, TypeVar

from nonebot import logger


class EventType(str, Enum):
    service_set_permission = "service_set_permission"
    """
    当某个服务设置权限成功时触发
    """

    service_remove_permission = "service_remove_permission"
    """
    当某个服务删除权限成功时触发
    """

    service_change_permission = "service_change_permission"
    """
    当某个服务权限变更时触发（包括该服务及其所有祖先服务设置、删除权限导致的权限变更）
    """

    service_add_rate_limit_rule = "service_add_rate_limit_rule"
    """
    当某个服务添加限流规则时触发（该服务及其所有祖先服务添加限流规则时都会触发）
    """
    service_remove_rate_limit_rule = "service_remove_rate_limit_rule"
    """
    当某个服务删除限流规则时触发（该服务及其所有祖先服务删除限流规则时都会触发）
    """


T = TypeVar("T")
T_Kwargs = Dict[str, Any]
T_Filter = Callable[[...], bool]
T_Listener = Callable[[...], Awaitable[None]]

_listeners: Dict[EventType, List[Tuple[T_Filter, T_Listener]]] = defaultdict(list)


def _call_with_kwargs(func: Callable[[...], T], kwargs: T_Kwargs) -> T:
    filtered_kwargs = {}

    sig = signature(func)
    for p in sig.parameters:
        filtered_kwargs[p] = kwargs[p]

    return func(**filtered_kwargs)


async def fire_event(event_type: EventType, kwargs: T_Kwargs):
    logger.trace(f"on event {event_type}  (kwargs: {', '.join(map(lambda k: f'{k}={kwargs[k]}', kwargs))})")

    coros = []

    for filter_func, func in _listeners[event_type]:
        if _call_with_kwargs(filter_func, kwargs):
            coro = _call_with_kwargs(func, kwargs)
            if isawaitable(coro):
                coros.append(coro)

    await gather(*coros)


def on_event(event_type: EventType, filter_func: T_Filter, func: Optional[T_Listener] = None):
    def decorator(func):
        _listeners[event_type].append((filter_func, func))
        return func

    if func is None:
        return decorator
    else:
        return decorator(func)
