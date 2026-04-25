"""
Custom throttle classes for rate limiting different types of operations.

These throttles work with Django REST Framework's built-in throttling system.
Add Redis cache backend for horizontal scaling in production.
"""

from rest_framework.throttling import SimpleRateThrottle


class AuthRateThrottle(SimpleRateThrottle):
    """
    Strict throttle for authentication endpoints (login, register).
    Prevents brute force attacks on user credentials.

    Rate: Configured in settings.DEFAULT_THROTTLE_RATES['auth']
    """

    scope = "auth"

    def get_cache_key(self, request, _view):
        # For auth, use IP address since user might not be authenticated
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class StoreRateThrottle(SimpleRateThrottle):
    """
    Throttle for store and purchase operations.
    Prevents transaction flooding and potential payment abuse.

    Rate: Configured in settings.DEFAULT_THROTTLE_RATES['store']
    """

    scope = "store"

    def get_cache_key(self, request, _view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class SensitiveOperationThrottle(SimpleRateThrottle):
    """
    Throttle for sensitive operations like password reset, email change.
    Very strict to prevent enumeration and abuse.

    Rate: Configured in settings.DEFAULT_THROTTLE_RATES['sensitive']
    """

    scope = "sensitive"

    def get_cache_key(self, request, _view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class BurstRateThrottle(SimpleRateThrottle):
    """
    Short burst throttle to prevent rapid-fire requests.
    Used for endpoints that should have a cool-down period.

    Rate: Configured in settings.DEFAULT_THROTTLE_RATES['burst']
    """

    scope = "burst"

    def get_cache_key(self, request, _view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class NotificationRateThrottle(SimpleRateThrottle):
    """
    Throttle for notifications feed polling.
    Kept higher than generic user throttle to support periodic refresh.

    Rate: Configured in settings.DEFAULT_THROTTLE_RATES['notifications']
    """

    scope = "notifications"

    def get_cache_key(self, request, _view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class CodeExecutionRateThrottle(SimpleRateThrottle):
    """
    Throttle code execution and submission endpoints.

    These endpoints fan out to the sandbox runtime, so they need a tighter,
    user-scoped limit than ordinary API reads.
    """

    scope = "code_execution"

    def get_cache_key(self, request, _view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}
