from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar
from collections.abc import Collection, Generator

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher

T_Service = TypeVar("T_Service", bound="IServiceBase", covariant=True)
T_ParentService = TypeVar(
    "T_ParentService", bound=Optional["IServiceBase"], covariant=True
)
T_ChildService = TypeVar("T_ChildService", bound="IServiceBase", covariant=True)


class IServiceBase(Generic[T_Service, T_ParentService, T_ChildService], ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def qualified_name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def parent(self) -> Optional[T_ParentService]:
        raise NotImplementedError()

    @property
    def children(self) -> Collection[T_ChildService]:
        raise NotImplementedError()

    @abstractmethod
    def travel(self) -> Generator[T_Service, None, None]:
        raise NotImplementedError()

    @abstractmethod
    def trace(self) -> Generator[T_Service, None, None]:
        raise NotImplementedError()

    @abstractmethod
    def get_child(self, name: str) -> Optional[T_Service]:
        raise NotImplementedError()

    @abstractmethod
    def patch_matcher(self, matcher: type[Matcher]) -> type[Matcher]:
        raise NotImplementedError()

    @abstractmethod
    def patch_handler(self, retire_on_throw: bool = False):
        raise NotImplementedError()

    @abstractmethod
    async def check(
        self,
        bot: Bot,
        event: Event,
        *,
        acquire_rate_limit_token: bool = True,
        throw_on_fail: bool = False,
    ) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def check_by_subject(
        self,
        *subjects: str,
        acquire_rate_limit_token: bool = True,
        throw_on_fail: bool = False,
    ) -> bool:
        raise NotImplementedError()
