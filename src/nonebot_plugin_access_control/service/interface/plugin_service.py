from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from .service import IService
from .subservice_owner import ISubServiceOwner

if TYPE_CHECKING:
    from .nonebot_service import INoneBotService

T_Service = TypeVar("T_Service", bound=IService, covariant=True)
T_ParentService = TypeVar("T_ParentService", bound="INoneBotService", covariant=True)
T_ChildService = TypeVar("T_ChildService", bound=IService, covariant=True)


class IPluginService(
    IService[T_Service, T_ParentService, T_ChildService],
    ISubServiceOwner[T_ChildService],
    ABC,
):
    @property
    @abstractmethod
    def auto_created(self) -> bool:
        ...
