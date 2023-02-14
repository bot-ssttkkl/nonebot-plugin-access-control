class AccessControlError(RuntimeError):
    ...


class PermissionDeniedError(AccessControlError):
    ...


class RateLimitedError(AccessControlError):
    ...
