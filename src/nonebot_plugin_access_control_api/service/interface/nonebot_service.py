from abc import ABC
from typing import TypeVar, Optional

from .service import IService
from .plugin_service import IPluginService

T_Service = TypeVar("T_Service", bound=IService, covariant=True)
T_ChildService = TypeVar("T_ChildService", bound=IPluginService, covariant=True)


class INoneBotService(
    IService[T_Service, None, T_ChildService],
    ABC,
):
    def create_plugin_service(self, plugin_name: str) -> T_ChildService:
        ...

    def get_plugin_service(
        self, plugin_name: str, *, raise_on_not_exists: bool = False
    ) -> Optional[T_ChildService]:
        ...

    def get_or_create_plugin_service(self, plugin_name: str) -> T_ChildService:
        ...

    def get_service_by_qualified_name(
        self, qualified_name: str, *, raise_on_not_exists: bool = False
    ) -> Optional[T_Service]:
        ...
