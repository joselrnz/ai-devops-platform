"""
Circuit Breaker - Resilience pattern for AWS API calls.

Implements circuit breaker pattern to prevent cascading failures when AWS services
are experiencing issues. Automatically opens circuit after threshold failures.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failures exceed threshold, requests fail immediately
    - HALF_OPEN: Testing if service recovered, allow limited requests
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (half-open)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: float = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable) -> Callable:
        """
        Wrap function with circuit breaker logic.

        Args:
            func: Function to protect

        Returns:
            Wrapped function
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check circuit state
            if self.state == "OPEN":
                # Check if timeout has elapsed
                if time.time() - self.last_failure_time >= self.timeout:
                    logger.info(f"Circuit breaker entering HALF_OPEN state for {func.__name__}")
                    self.state = "HALF_OPEN"
                else:
                    logger.warning(f"Circuit breaker OPEN for {func.__name__}")
                    raise CircuitBreakerError(
                        f"Circuit breaker open for {func.__name__}. "
                        f"Service unavailable. Retry after {self.timeout}s."
                    )

            try:
                # Call the function
                result = await func(*args, **kwargs)

                # Success - reset failure count if in HALF_OPEN
                if self.state == "HALF_OPEN":
                    logger.info(f"Circuit breaker closing for {func.__name__}")
                    self.state = "CLOSED"
                    self.failure_count = 0

                return result

            except Exception as e:
                # Record failure
                self.failure_count += 1
                self.last_failure_time = time.time()

                logger.error(
                    f"Circuit breaker recorded failure for {func.__name__}: {e}. "
                    f"Failure count: {self.failure_count}/{self.failure_threshold}"
                )

                # Check if threshold exceeded
                if self.failure_count >= self.failure_threshold:
                    logger.error(
                        f"Circuit breaker OPENING for {func.__name__}. "
                        f"Threshold exceeded: {self.failure_count} failures"
                    )
                    self.state = "OPEN"

                raise

        return wrapper


# Global circuit breakers per function
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def circuit_breaker(failure_threshold: int = 5, timeout: int = 60) -> Callable:
    """
    Decorator to add circuit breaker to a function.

    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting recovery

    Returns:
        Decorator function

    Example:
        @circuit_breaker(failure_threshold=3, timeout=30)
        async def call_external_api():
            # This function is protected by circuit breaker
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Create circuit breaker for this function
        breaker_key = f"{func.__module__}.{func.__name__}"

        if breaker_key not in _circuit_breakers:
            _circuit_breakers[breaker_key] = CircuitBreaker(
                failure_threshold=failure_threshold,
                timeout=timeout,
            )

        breaker = _circuit_breakers[breaker_key]

        return breaker.call(func)

    return decorator
