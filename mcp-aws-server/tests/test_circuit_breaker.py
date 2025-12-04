"""
Tests for circuit breaker utility.
"""
import pytest
import asyncio
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in CLOSED state allows requests."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1)

        @breaker
        async def successful_operation():
            return "success"

        result = await successful_operation()
        assert result == "success"
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after exceeding failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1)

        @breaker
        async def failing_operation():
            raise Exception("Operation failed")

        # Trigger failures
        for _ in range(3):
            with pytest.raises(Exception):
                await failing_operation()

        assert breaker.state == "OPEN"
        assert breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects requests when OPEN."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=1)

        @breaker
        async def failing_operation():
            raise Exception("Operation failed")

        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await failing_operation()

        # Next request should be rejected immediately
        with pytest.raises(CircuitBreakerError, match="Circuit breaker is OPEN"):
            await failing_operation()

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self):
        """Test circuit breaker transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=1)

        @breaker
        async def operation(should_fail=True):
            if should_fail:
                raise Exception("Operation failed")
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await operation(should_fail=True)

        assert breaker.state == "OPEN"

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Should transition to HALF_OPEN and allow one test request
        result = await operation(should_fail=False)
        assert result == "success"
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker resets failure count on successful request."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1)

        @breaker
        async def operation(should_fail=False):
            if should_fail:
                raise Exception("Operation failed")
            return "success"

        # Some failures
        with pytest.raises(Exception):
            await operation(should_fail=True)

        assert breaker.failure_count == 1

        # Successful request should reset
        await operation(should_fail=False)
        assert breaker.failure_count == 0
        assert breaker.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_different_exceptions(self):
        """Test circuit breaker handles different exception types."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=1)

        @breaker
        async def operation(exception_type):
            raise exception_type("Test error")

        with pytest.raises(ValueError):
            await operation(ValueError)

        with pytest.raises(RuntimeError):
            await operation(RuntimeError)

        assert breaker.state == "OPEN"
        assert breaker.failure_count == 2
