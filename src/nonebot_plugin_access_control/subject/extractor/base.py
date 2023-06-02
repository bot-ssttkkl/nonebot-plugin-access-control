from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

from nonebot import Bot
from nonebot.internal.adapter import Event

T_Bot = TypeVar('T_Bot', bound=Bot, covariant=True)
T_Event = TypeVar('T_Event', bound=Event, covariant=True)


class SubjectExtractor(ABC, Generic[T_Bot, T_Event]):
    @classmethod
    @abstractmethod
    def bot_type(cls) -> str:
        ...

    @abstractmethod
    def extract(self, bot: T_Bot, event: T_Event) -> List[str]:
        ...
