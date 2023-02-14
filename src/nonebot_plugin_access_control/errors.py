class AccessControlError(RuntimeError):
    ...


class PermissionDeniedError(AccessControlError):
    ...


class RateLimitedError(AccessControlError):
    ...


class AccessControlValueError(AccessControlError, ValueError):
    ...
