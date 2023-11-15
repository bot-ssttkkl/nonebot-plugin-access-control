from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from ..service import Service


class Permission(NamedTuple):
    service: "Service"
    subject: str
    allow: bool
