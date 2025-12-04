"""
Audit Logger - Comprehensive audit trail for all requests.

Logs all LLM requests and responses to PostgreSQL for compliance and forensics.
Includes metadata: user, model, tokens, cost, PII detections, latency.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for LLM gateway.

    Logs to:
    - PostgreSQL database (long-term storage)
    - Application logs (real-time monitoring)
    """

    def __init__(self):
        """Initialize audit logger"""
        # TODO: Initialize PostgreSQL connection
        self.db_pool = None
        logger.info("AuditLogger initialized")

    async def log(
        self,
        request_id: str,
        user_id: str,
        tenant: str,
        model: str,
        tokens_used: int,
        cost: float,
        pii_detected: bool,
        pii_entities: List[str],
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Log request to audit trail.

        Args:
            request_id: Unique request ID
            user_id: User ID
            tenant: Tenant ID
            model: Model used
            tokens_used: Total tokens
            cost: API cost in USD
            pii_detected: Whether PII was detected
            pii_entities: List of PII entity types
            latency_ms: Response latency
            error: Error message if failed
        """
        # Create audit log entry
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "user_id": user_id,
            "tenant": tenant,
            "model": model,
            "tokens_used": tokens_used,
            "cost_usd": cost,
            "pii_detected": pii_detected,
            "pii_entities": pii_entities,
            "latency_ms": latency_ms,
            "error": error,
            "status": "error" if error else "success",
        }

        # Log to application logger
        logger.info(
            f"AUDIT: request_id={request_id} user={user_id} model={model} "
            f"tokens={tokens_used} cost=${cost:.4f} pii={pii_detected}",
            extra=audit_entry,
        )

        # TODO: Log to PostgreSQL
        # await self._log_to_database(audit_entry)

    async def _log_to_database(self, entry: Dict[str, Any]) -> None:
        """
        Log entry to PostgreSQL database.

        Args:
            entry: Audit log entry
        """
        # TODO: Implement PostgreSQL insertion
        # SQL: INSERT INTO audit_logs (timestamp, request_id, user_id, ...) VALUES (...)
        pass

    async def get_usage_stats(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            Usage statistics
        """
        # TODO: Query PostgreSQL for stats
        # SELECT model, SUM(tokens_used), SUM(cost_usd) FROM audit_logs
        # WHERE user_id = ? AND timestamp > NOW() - INTERVAL ? GROUP BY model

        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_model": {},
        }

    async def close(self):
        """Close database connection"""
        if self.db_pool:
            await self.db_pool.close()
