from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T_SubService = TypeVar("T_SubService", bound="ISubServiceOwner", covariant=True)


class ISubServiceOwner(Generic[T_SubService], ABC):
    @abstractmethod
    def create_subservice(self, name: str) -> T_SubService:
        raise NotImplementedError()
