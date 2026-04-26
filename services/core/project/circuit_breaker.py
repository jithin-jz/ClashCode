import logging
import time

from django.core.cache import cache

logger = logging.getLogger(__name__)


class RedisCircuitBreaker:
    """
    A simple Redis-backed circuit breaker for microservices resilience.
    States: closed, open, half-open.
    """

    def __init__(self, name, failure_threshold=5, recovery_timeout=60):
        self.name = f"cb:{name}"
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    def _get_state(self):
        return cache.get(f"{self.name}:state", "closed")

    def _get_failures(self):
        return cache.get(f"{self.name}:failures", 0)

    def is_available(self) -> bool:
        state = self._get_state()
        if state == "closed":
            return True

        if state == "open":
            last_failure = cache.get(f"{self.name}:last_failure", 0)
            if time.time() - last_failure > self.recovery_timeout:
                # Transition to half-open to test the service
                logger.warning(f"Circuit Breaker {self.name} entering HALF-OPEN state")
                cache.set(f"{self.name}:state", "half-open")
                return True
            return False

        if state == "half-open":
            # In half-open, we allow one request through
            return True

        return True

    def record_success(self):
        state = self._get_state()
        if state != "closed":
            logger.info(f"Circuit Breaker {self.name} CLOSED (Service recovered)")
            cache.set(f"{self.name}:state", "closed")
            cache.set(f"{self.name}:failures", 0)

    def record_failure(self):
        failures = cache.get(f"{self.name}:failures", 0) + 1
        cache.set(f"{self.name}:failures", failures, timeout=self.recovery_timeout * 2)

        if failures >= self.failure_threshold:
            logger.error(f"Circuit Breaker {self.name} OPENED after {failures} failures")
            cache.set(f"{self.name}:state", "open")
            cache.set(f"{self.name}:last_failure", time.time())
