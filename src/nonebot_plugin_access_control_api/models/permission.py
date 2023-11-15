from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from ..service.interface import IService


class Permission(NamedTuple):
    service: "IService"
    subject: str
    allow: bool
