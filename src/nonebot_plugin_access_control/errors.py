from .service.interface.rate_limit import AcquireTokenResult


class AccessControlError(RuntimeError):
    ...


class PermissionDeniedError(AccessControlError):
    ...


class RateLimitedError(AccessControlError):
    def __init__(self, result: AcquireTokenResult):
        self.result = result


class AccessControlValueError(AccessControlError, ValueError):
    ...
