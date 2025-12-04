"""
RBAC Policy Engine - Role-Based Access Control with OPA/Rego.

Evaluates authorization policies using Open Policy Agent.
Supports fine-grained permissions for users, teams, and tenants.
"""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    RBAC policy engine using OPA (Open Policy Agent).

    Evaluates authorization decisions using Rego policies.
    """

    def __init__(self, opa_url: str = "http://localhost:8181"):
        """
        Initialize policy engine.

        Args:
            opa_url: OPA server URL
        """
        self.opa_url = opa_url
        self.policy_path = "/v1/data/llm/authz/allow"
        self.client = httpx.AsyncClient()

        logger.info(f"PolicyEngine initialized with OPA at {opa_url}")

    async def evaluate(
        self,
        user: Dict[str, Any],
        action: str,
        resource: Dict[str, Any],
    ) -> bool:
        """
        Evaluate authorization policy.

        Args:
            user: User context (user_id, role, tier, tenant)
            action: Action being performed (e.g., "chat", "admin")
            resource: Resource being accessed (e.g., model info)

        Returns:
            True if authorized, False otherwise
        """
        # Build OPA input
        opa_input = {
            "input": {
                "user": user,
                "action": action,
                "resource": resource,
            }
        }

        try:
            # Query OPA
            response = await self.client.post(
                f"{self.opa_url}{self.policy_path}",
                json=opa_input,
                timeout=5.0,
            )

            if response.status_code == 200:
                result = response.json()
                is_allowed = result.get("result", False)

                logger.info(
                    f"Authorization decision: {is_allowed} for user {user.get('user_id')} "
                    f"action={action} resource={resource}"
                )

                return is_allowed
            else:
                logger.error(f"OPA request failed: {response.status_code} {response.text}")
                # Fail-closed: deny access if OPA is unavailable
                return False

        except Exception as e:
            logger.error(f"Error evaluating policy: {e}")
            # Fail-closed: deny access on error
            return False

    async def get_user_permissions(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user's permissions.

        Args:
            user: User context

        Returns:
            User permissions
        """
        opa_input = {"input": {"user": user}}

        try:
            response = await self.client.post(
                f"{self.opa_url}/v1/data/llm/authz/permissions",
                json=opa_input,
                timeout=5.0,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                return {}

        except Exception as e:
            logger.error(f"Error getting permissions: {e}")
            return {}

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
