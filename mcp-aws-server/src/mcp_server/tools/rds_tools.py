"""
RDS Tools - AWS RDS database management operations.

Provides MCP tools for RDS instance status, snapshots, and basic operations.
"""

import logging
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

from ...utils.circuit_breaker import circuit_breaker
from ...utils.audit import audit_log

logger = logging.getLogger(__name__)


class RDSTools:
    """AWS RDS operations exposed as MCP tools"""

    def __init__(self):
        """Initialize RDS client"""
        self.rds_client = boto3.client("rds")

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of RDS tools"""
        return [
            {
                "name": "rds.describe_instances",
                "description": "List RDS database instances",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "rds.get_instance_status",
                "description": "Get status of a specific RDS instance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "db_instance_id": {"type": "string"},
                    },
                    "required": ["db_instance_id"],
                },
            },
            {
                "name": "rds.create_snapshot",
                "description": "Create a manual snapshot of an RDS instance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "db_instance_id": {"type": "string"},
                        "snapshot_id": {"type": "string"},
                    },
                    "required": ["db_instance_id", "snapshot_id"],
                },
            },
            {
                "name": "rds.list_snapshots",
                "description": "List RDS snapshots",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "db_instance_id": {
                            "type": "string",
                            "description": "Filter by DB instance ID (optional)",
                        },
                    },
                },
            },
        ]

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an RDS operation"""
        operation_map = {
            "describe_instances": self.describe_instances,
            "get_instance_status": self.get_instance_status,
            "create_snapshot": self.create_snapshot,
            "list_snapshots": self.list_snapshots,
        }

        if operation not in operation_map:
            raise ValueError(f"Unknown RDS operation: {operation}")

        handler = operation_map[operation]
        return await handler(**parameters)

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="rds.describe_instances")
    async def describe_instances(self) -> Dict[str, Any]:
        """List all RDS instances"""
        try:
            response = self.rds_client.describe_db_instances()

            instances = []
            for db in response.get("DBInstances", []):
                instances.append({
                    "db_instance_id": db["DBInstanceIdentifier"],
                    "engine": db["Engine"],
                    "engine_version": db["EngineVersion"],
                    "status": db["DBInstanceStatus"],
                    "endpoint": db.get("Endpoint", {}).get("Address"),
                    "port": db.get("Endpoint", {}).get("Port"),
                    "instance_class": db["DBInstanceClass"],
                    "storage": db["AllocatedStorage"],
                    "multi_az": db["MultiAZ"],
                })

            return {"instances": instances, "count": len(instances)}

        except ClientError as e:
            logger.error(f"Error describing RDS instances: {e}")
            raise

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="rds.get_instance_status")
    async def get_instance_status(self, db_instance_id: str) -> Dict[str, Any]:
        """Get RDS instance status"""
        try:
            response = self.rds_client.describe_db_instances(
                DBInstanceIdentifier=db_instance_id
            )

            if not response.get("DBInstances"):
                raise ValueError(f"RDS instance not found: {db_instance_id}")

            db = response["DBInstances"][0]

            return {
                "db_instance_id": db["DBInstanceIdentifier"],
                "status": db["DBInstanceStatus"],
                "endpoint": db.get("Endpoint", {}).get("Address"),
                "engine": db["Engine"],
                "multi_az": db["MultiAZ"],
            }

        except ClientError as e:
            logger.error(f"Error getting status for {db_instance_id}: {e}")
            raise

    @circuit_breaker(failure_threshold=3, timeout=120)
    @audit_log(operation="rds.create_snapshot", sensitive=True)
    async def create_snapshot(
        self, db_instance_id: str, snapshot_id: str
    ) -> Dict[str, Any]:
        """Create RDS snapshot"""
        try:
            response = self.rds_client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_id, DBInstanceIdentifier=db_instance_id
            )

            snapshot = response["DBSnapshot"]

            return {
                "snapshot_id": snapshot["DBSnapshotIdentifier"],
                "db_instance_id": snapshot["DBInstanceIdentifier"],
                "status": snapshot["Status"],
                "message": f"Snapshot {snapshot_id} creation initiated",
            }

        except ClientError as e:
            logger.error(f"Error creating snapshot: {e}")
            raise

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="rds.list_snapshots")
    async def list_snapshots(self, db_instance_id: str = None) -> Dict[str, Any]:
        """List RDS snapshots"""
        try:
            kwargs = {}
            if db_instance_id:
                kwargs["DBInstanceIdentifier"] = db_instance_id

            response = self.rds_client.describe_db_snapshots(**kwargs)

            snapshots = []
            for snap in response.get("DBSnapshots", []):
                snapshots.append({
                    "snapshot_id": snap["DBSnapshotIdentifier"],
                    "db_instance_id": snap["DBInstanceIdentifier"],
                    "status": snap["Status"],
                    "created_at": snap["SnapshotCreateTime"].isoformat(),
                    "snapshot_type": snap["SnapshotType"],
                })

            return {"snapshots": snapshots, "count": len(snapshots)}

        except ClientError as e:
            logger.error(f"Error listing snapshots: {e}")
            raise
