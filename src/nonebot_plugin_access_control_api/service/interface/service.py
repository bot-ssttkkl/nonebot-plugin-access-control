from abc import ABC
from typing import Generic, TypeVar, Optional

from .service_base import IServiceBase
from .rate_limit import IServiceRateLimit
from .permission import IServicePermission

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
