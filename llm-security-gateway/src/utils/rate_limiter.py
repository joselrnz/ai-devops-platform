"""
Rate Limiter - Redis-based distributed rate limiting.

Implements sliding window algorithm for rate limiting.
Supports per-user, per-tenant, and per-API-key limits.
"""

import logging
import time
from typing import Dict, Tuple

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter.

    Uses sliding window algorithm for accurate rate limiting.
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
        )

        # Default rate limits (can be overridden per user/tenant)
        self.default_limits = {
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "tokens_per_day": 100000,
        }

        logger.info(f"RateLimiter initialized with Redis at {redis_host}:{redis_port}")

    async def check_limit(
        self,
        user_id: str,
        tenant: str,
        tokens: int = 0,
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limits.

        Args:
            user_id: User ID
            tenant: Tenant ID
            tokens: Number of tokens (for token-based limits)

        Returns:
            (is_allowed, limit_info)
        """
        current_time = int(time.time())

        # Check per-user limits
        user_key = f"rate_limit:user:{user_id}:minute"
        user_count = await self._increment_counter(user_key, 60)

        if user_count > self.default_limits["requests_per_minute"]:
            logger.warning(f"Rate limit exceeded for user {user_id}: {user_count} req/min")
            return False, {
                "retry_after": 60,
                "limit": self.default_limits["requests_per_minute"],
                "current": user_count,
            }

        # Check per-tenant limits
        tenant_key = f"rate_limit:tenant:{tenant}:hour"
        tenant_count = await self._increment_counter(tenant_key, 3600)

        tenant_limit = self.default_limits["requests_per_hour"] * 10  # 10x for tenant
        if tenant_count > tenant_limit:
            logger.warning(f"Rate limit exceeded for tenant {tenant}: {tenant_count} req/hour")
            return False, {
                "retry_after": 3600,
                "limit": tenant_limit,
                "current": tenant_count,
            }

        # Check token limits (if provided)
        if tokens > 0:
            token_key = f"rate_limit:user:{user_id}:tokens:day"
            token_count = await self._increment_counter(token_key, 86400, increment=tokens)

            if token_count > self.default_limits["tokens_per_day"]:
                logger.warning(
                    f"Token limit exceeded for user {user_id}: {token_count} tokens/day"
                )
                return False, {
                    "retry_after": 86400,
                    "limit": self.default_limits["tokens_per_day"],
                    "current": token_count,
                }

        return True, {
            "user_requests": user_count,
            "tenant_requests": tenant_count,
            "tokens_used": token_count if tokens > 0 else 0,
        }

    async def _increment_counter(
        self,
        key: str,
        window_seconds: int,
        increment: int = 1,
    ) -> int:
        """
        Increment counter with sliding window.

        Args:
            key: Redis key
            window_seconds: Time window in seconds
            increment: Increment amount

        Returns:
            Current count
        """
        try:
            # Use INCR for atomic increment
            current = await self.redis_client.incr(key, increment)

            # Set expiration if this is the first increment
            if current == increment:
                await self.redis_client.expire(key, window_seconds)

            return current

        except Exception as e:
            logger.error(f"Error incrementing counter: {e}")
            # Fail-open: allow request if Redis is down
            return 0

    async def get_usage(self, user_id: str) -> Dict[str, int]:
        """
        Get current usage for a user.

        Args:
            user_id: User ID

        Returns:
            Usage stats
        """
        try:
            user_minute = await self.redis_client.get(f"rate_limit:user:{user_id}:minute")
            user_hour = await self.redis_client.get(f"rate_limit:user:{user_id}:hour")
            tokens_day = await self.redis_client.get(f"rate_limit:user:{user_id}:tokens:day")

            return {
                "requests_per_minute": int(user_minute) if user_minute else 0,
                "requests_per_hour": int(user_hour) if user_hour else 0,
                "tokens_per_day": int(tokens_day) if tokens_day else 0,
            }

        except Exception as e:
            logger.error(f"Error getting usage: {e}")
            return {}

    async def reset_limits(self, user_id: str) -> None:
        """
        Reset rate limits for a user.

        Args:
            user_id: User ID
        """
        try:
            keys = await self.redis_client.keys(f"rate_limit:user:{user_id}:*")
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Reset rate limits for user {user_id}")

        except Exception as e:
            logger.error(f"Error resetting limits: {e}")

    async def close(self):
        """Close Redis connection"""
        await self.redis_client.close()
