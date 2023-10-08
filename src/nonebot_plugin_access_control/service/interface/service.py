from abc import ABC
from typing import Generic, TypeVar, Optional

from .base import IServiceBase
from .permission import IServicePermission
from .rate_limit import IServiceRateLimit

T_Service = TypeVar("T_Service", bound="IService", covariant=True)
T_ParentService = TypeVar(
    "T_ParentService", bound=Optional["IServiceBase"], covariant=True
)
T_ChildService = TypeVar("T_ChildService", bound="IService", covariant=True)


class IService(
    Generic[T_Service, T_ParentService, T_ChildService],
    IServiceBase[T_Service, T_ParentService, T_ChildService],
    IServicePermission,
    IServiceRateLimit,
    ABC,
):
    ...
