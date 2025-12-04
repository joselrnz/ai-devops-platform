"""
ECS Tools - AWS ECS container orchestration operations.

Provides MCP tools for managing ECS services, tasks, and clusters.
"""

import logging
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

from ...utils.circuit_breaker import circuit_breaker
from ...utils.audit import audit_log

logger = logging.getLogger(__name__)


class ECSTools:
    """AWS ECS operations exposed as MCP tools"""

    def __init__(self):
        """Initialize ECS client"""
        self.ecs_client = boto3.client("ecs")

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of ECS tools"""
        return [
            {
                "name": "ecs.list_clusters",
                "description": "List ECS clusters",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "ecs.list_services",
                "description": "List services in an ECS cluster",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cluster": {
                            "type": "string",
                            "description": "Cluster name or ARN",
                        },
                    },
                    "required": ["cluster"],
                },
            },
            {
                "name": "ecs.describe_service",
                "description": "Get detailed information about an ECS service",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cluster": {"type": "string"},
                        "service": {"type": "string"},
                    },
                    "required": ["cluster", "service"],
                },
            },
            {
                "name": "ecs.scale_service",
                "description": "Scale an ECS service to a specific task count",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cluster": {"type": "string"},
                        "service": {"type": "string"},
                        "desired_count": {
                            "type": "integer",
                            "description": "Desired number of tasks",
                        },
                    },
                    "required": ["cluster", "service", "desired_count"],
                },
            },
        ]

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an ECS operation"""
        operation_map = {
            "list_clusters": self.list_clusters,
            "list_services": self.list_services,
            "describe_service": self.describe_service,
            "scale_service": self.scale_service,
        }

        if operation not in operation_map:
            raise ValueError(f"Unknown ECS operation: {operation}")

        handler = operation_map[operation]
        return await handler(**parameters)

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="ecs.list_clusters")
    async def list_clusters(self) -> Dict[str, Any]:
        """List all ECS clusters"""
        try:
            response = self.ecs_client.list_clusters()

            cluster_arns = response.get("clusterArns", [])

            if not cluster_arns:
                return {"clusters": [], "count": 0}

            # Get cluster details
            describe_response = self.ecs_client.describe_clusters(clusters=cluster_arns)

            clusters = []
            for cluster in describe_response.get("clusters", []):
                clusters.append({
                    "name": cluster["clusterName"],
                    "arn": cluster["clusterArn"],
                    "status": cluster["status"],
                    "running_tasks": cluster["runningTasksCount"],
                    "pending_tasks": cluster["pendingTasksCount"],
                    "active_services": cluster["activeServicesCount"],
                })

            return {"clusters": clusters, "count": len(clusters)}

        except ClientError as e:
            logger.error(f"Error listing clusters: {e}")
            raise

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="ecs.list_services")
    async def list_services(self, cluster: str) -> Dict[str, Any]:
        """List services in a cluster"""
        try:
            response = self.ecs_client.list_services(cluster=cluster)

            service_arns = response.get("serviceArns", [])

            return {
                "cluster": cluster,
                "services": service_arns,
                "count": len(service_arns),
            }

        except ClientError as e:
            logger.error(f"Error listing services in cluster {cluster}: {e}")
            raise

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="ecs.describe_service")
    async def describe_service(self, cluster: str, service: str) -> Dict[str, Any]:
        """Describe an ECS service"""
        try:
            response = self.ecs_client.describe_services(
                cluster=cluster, services=[service]
            )

            if not response.get("services"):
                raise ValueError(f"Service not found: {service}")

            svc = response["services"][0]

            return {
                "name": svc["serviceName"],
                "arn": svc["serviceArn"],
                "status": svc["status"],
                "desired_count": svc["desiredCount"],
                "running_count": svc["runningCount"],
                "pending_count": svc["pendingCount"],
                "launch_type": svc.get("launchType"),
                "task_definition": svc["taskDefinition"],
                "created_at": svc["createdAt"].isoformat(),
            }

        except ClientError as e:
            logger.error(f"Error describing service {service}: {e}")
            raise

    @circuit_breaker(failure_threshold=3, timeout=60)
    @audit_log(operation="ecs.scale_service", sensitive=True)
    async def scale_service(
        self, cluster: str, service: str, desired_count: int
    ) -> Dict[str, Any]:
        """Scale an ECS service"""
        try:
            response = self.ecs_client.update_service(
                cluster=cluster, service=service, desiredCount=desired_count
            )

            svc = response["service"]

            return {
                "service": svc["serviceName"],
                "cluster": cluster,
                "previous_count": svc["runningCount"],
                "desired_count": desired_count,
                "message": f"Service {service} scaled to {desired_count} tasks",
            }

        except ClientError as e:
            logger.error(f"Error scaling service {service}: {e}")
            raise
