from asyncio import gather
from collections import defaultdict
from enum import Enum
from inspect import isawaitable
from typing import Dict, List, Callable, Awaitable, Any, Tuple, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


class EventType(str, Enum):
    service_allow_permission = "service_allow_permission"
    service_deny_permission = "service_deny_permission"
    service_remove_permission = "service_remove_permission"


T_Kwargs = Dict[str, Any]
T_Filter = Callable[[T_Kwargs], bool]
T_Listener = Callable[[...], Awaitable[None]]

_listeners: Dict[EventType, List[Tuple[T_Filter, T_Listener]]] = defaultdict(list)


async def fire_event(event_type: EventType, kwargs: T_Kwargs):
    coros = []

    for filter_func, func in _listeners[event_type]:
        if filter_func(kwargs):
            coro = func(**kwargs)
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
