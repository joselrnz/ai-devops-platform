"""
EC2 Tools - AWS EC2 instance management operations.

Provides MCP tools for listing, describing, starting, and stopping EC2 instances.
"""

import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ...utils.circuit_breaker import circuit_breaker
from ...utils.audit import audit_log

logger = logging.getLogger(__name__)


class EC2Tools:
    """AWS EC2 operations exposed as MCP tools"""

    def __init__(self):
        """Initialize EC2 client"""
        self.ec2_client = boto3.client("ec2")

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Return list of EC2 tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "ec2.list_instances",
                "description": "List EC2 instances with optional filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "array",
                            "description": "Filters for instance search",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "Name": {"type": "string"},
                                    "Values": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                            },
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 50,
                        },
                    },
                },
            },
            {
                "name": "ec2.describe_instance",
                "description": "Get detailed information about a specific EC2 instance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "EC2 instance ID",
                        },
                    },
                    "required": ["instance_id"],
                },
            },
            {
                "name": "ec2.start_instance",
                "description": "Start a stopped EC2 instance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "EC2 instance ID to start",
                        },
                    },
                    "required": ["instance_id"],
                },
            },
            {
                "name": "ec2.stop_instance",
                "description": "Stop a running EC2 instance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "EC2 instance ID to stop",
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force stop the instance",
                            "default": False,
                        },
                    },
                    "required": ["instance_id"],
                },
            },
        ]

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an EC2 operation.

        Args:
            operation: Operation name (e.g., "list_instances")
            parameters: Operation parameters

        Returns:
            Operation result

        Raises:
            ValueError: If operation is unknown
        """
        operation_map = {
            "list_instances": self.list_instances,
            "describe_instance": self.describe_instance,
            "start_instance": self.start_instance,
            "stop_instance": self.stop_instance,
        }

        if operation not in operation_map:
            raise ValueError(f"Unknown EC2 operation: {operation}")

        handler = operation_map[operation]
        return await handler(**parameters)

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="ec2.list_instances")
    async def list_instances(
        self,
        filters: Optional[List[Dict[str, Any]]] = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        List EC2 instances.

        Args:
            filters: Filters for instance search
            max_results: Maximum number of results

        Returns:
            List of instances with basic info
        """
        try:
            kwargs: Dict[str, Any] = {"MaxResults": max_results}

            if filters:
                kwargs["Filters"] = filters

            response = self.ec2_client.describe_instances(**kwargs)

            instances = []
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append({
                        "instance_id": instance["InstanceId"],
                        "instance_type": instance["InstanceType"],
                        "state": instance["State"]["Name"],
                        "private_ip": instance.get("PrivateIpAddress"),
                        "public_ip": instance.get("PublicIpAddress"),
                        "launch_time": instance["LaunchTime"].isoformat(),
                        "tags": {
                            tag["Key"]: tag["Value"]
                            for tag in instance.get("Tags", [])
                        },
                    })

            return {
                "instances": instances,
                "count": len(instances),
            }

        except ClientError as e:
            logger.error(f"Error listing instances: {e}")
            raise

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="ec2.describe_instance")
    async def describe_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Describe a specific EC2 instance.

        Args:
            instance_id: EC2 instance ID

        Returns:
            Detailed instance information
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])

            if not response["Reservations"]:
                raise ValueError(f"Instance not found: {instance_id}")

            instance = response["Reservations"][0]["Instances"][0]

            return {
                "instance_id": instance["InstanceId"],
                "instance_type": instance["InstanceType"],
                "state": instance["State"]["Name"],
                "availability_zone": instance["Placement"]["AvailabilityZone"],
                "private_ip": instance.get("PrivateIpAddress"),
                "public_ip": instance.get("PublicIpAddress"),
                "vpc_id": instance.get("VpcId"),
                "subnet_id": instance.get("SubnetId"),
                "security_groups": [
                    {
                        "id": sg["GroupId"],
                        "name": sg["GroupName"],
                    }
                    for sg in instance.get("SecurityGroups", [])
                ],
                "launch_time": instance["LaunchTime"].isoformat(),
                "tags": {
                    tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])
                },
            }

        except ClientError as e:
            logger.error(f"Error describing instance {instance_id}: {e}")
            raise

    @circuit_breaker(failure_threshold=3, timeout=60)
    @audit_log(operation="ec2.start_instance", sensitive=True)
    async def start_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Start an EC2 instance.

        Args:
            instance_id: EC2 instance ID

        Returns:
            Start operation result
        """
        try:
            response = self.ec2_client.start_instances(InstanceIds=[instance_id])

            current_state = response["StartingInstances"][0]["CurrentState"]["Name"]
            previous_state = response["StartingInstances"][0]["PreviousState"]["Name"]

            return {
                "instance_id": instance_id,
                "previous_state": previous_state,
                "current_state": current_state,
                "message": f"Instance {instance_id} is starting",
            }

        except ClientError as e:
            logger.error(f"Error starting instance {instance_id}: {e}")
            raise

    @circuit_breaker(failure_threshold=3, timeout=60)
    @audit_log(operation="ec2.stop_instance", sensitive=True)
    async def stop_instance(self, instance_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Stop an EC2 instance.

        Args:
            instance_id: EC2 instance ID
            force: Force stop the instance

        Returns:
            Stop operation result
        """
        try:
            kwargs: Dict[str, Any] = {"InstanceIds": [instance_id]}
            if force:
                kwargs["Force"] = True

            response = self.ec2_client.stop_instances(**kwargs)

            current_state = response["StoppingInstances"][0]["CurrentState"]["Name"]
            previous_state = response["StoppingInstances"][0]["PreviousState"]["Name"]

            return {
                "instance_id": instance_id,
                "previous_state": previous_state,
                "current_state": current_state,
                "force": force,
                "message": f"Instance {instance_id} is stopping",
            }

        except ClientError as e:
            logger.error(f"Error stopping instance {instance_id}: {e}")
            raise
