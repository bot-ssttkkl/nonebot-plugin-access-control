import re
from abc import ABC, abstractmethod
from typing import TypeVar, Optional
from collections.abc import Collection

from nonebot import logger

from nonebot_plugin_access_control.errors import AccessControlError
from .base import Service
from .interface.subservice_owner import ISubServiceOwner


def _validate_name(name: str) -> bool:
    match_result = re.match(r"[_a-zA-Z]\w*", name)
    return match_result is not None


T_ParentService = TypeVar("T_ParentService", bound=Optional[Service], covariant=True)
T_ChildService = TypeVar("T_ChildService", bound="SubServiceOwner", covariant=True)


class SubServiceOwner(
    Service[T_ParentService, T_ChildService], ISubServiceOwner[T_ChildService], ABC
):
    def __init__(self):
        super().__init__()
        self._subservices: dict[str, T_ChildService] = {}

    @abstractmethod
    def _make_subservice(self, name: str) -> T_ChildService:
        raise NotImplementedError()

    @property
    def children(self) -> Collection[T_ChildService]:
        return self._subservices.values()

    def create_subservice(self, name: str) -> T_ChildService:
        if not _validate_name(name):
            raise AccessControlError(f"invalid name: {name}")

        if name in self._subservices:
            raise AccessControlError(
                f"subservice already exists: {self.qualified_name}.{name}"
            )

        service = self._make_subservice(name)
        self._subservices[name] = service
        logger.trace(
            f"created subservice {service.qualified_name}"
            f"  (parent: {self.qualified_name})"
        )
        return self._subservices[name]
