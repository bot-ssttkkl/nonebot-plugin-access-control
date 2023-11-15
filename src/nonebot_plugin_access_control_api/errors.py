from typing import TYPE_CHECKING

from ssttkkl_nonebot_utils.errors.errors import QueryError, BadRequestError

if TYPE_CHECKING:
    from .models.rate_limit import AcquireTokenResult


class AccessControlError(RuntimeError):
    ...


class PermissionDeniedError(AccessControlError):
    ...


class RateLimitedError(AccessControlError):
    def __init__(self, result: "AcquireTokenResult"):
        self.result = result


class AccessControlBadRequestError(BadRequestError, AccessControlError):
    ...


class AccessControlQueryError(QueryError, AccessControlError):
    ...
