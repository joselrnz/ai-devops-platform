"""
Example MCP client for interacting with the AWS MCP server.
"""
import asyncio
import json
from typing import Dict, Any
import httpx


class MCPClient:
    """Simple MCP client for AWS operations."""

    def __init__(self, server_url: str, api_key: str = None):
        """
        Initialize MCP client.

        Args:
            server_url: URL of the MCP server
            api_key: Optional API key for authentication
        """
        self.server_url = server_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
        self.request_id = 0

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool (e.g., 'ec2', 'ecs')
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": f"req-{self.request_id}",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.server_url, json=request, headers=self.headers, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def list_tools(self) -> Dict[str, Any]:
        """
        List all available tools.

        Returns:
            List of available tools
        """
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": f"req-{self.request_id}",
            "method": "tools/list",
            "params": {},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.server_url, json=request, headers=self.headers
            )
            response.raise_for_status()
            return response.json()


async def main():
    """Example usage of the MCP client."""
    # Initialize client
    client = MCPClient(
        server_url="http://localhost:8000/mcp", api_key="your-api-key-here"
    )

    # Example 1: List available tools
    print("=" * 60)
    print("Example 1: List Available Tools")
    print("=" * 60)
    tools_response = await client.list_tools()
    print(json.dumps(tools_response, indent=2))

    # Example 2: List EC2 instances
    print("\n" + "=" * 60)
    print("Example 2: List EC2 Instances")
    print("=" * 60)
    ec2_response = await client.call_tool(
        tool_name="ec2", arguments={"operation": "list", "max_results": 10}
    )
    print(json.dumps(ec2_response, indent=2))

    # Example 3: List EC2 instances with filters
    print("\n" + "=" * 60)
    print("Example 3: List Running EC2 Instances")
    print("=" * 60)
    filtered_response = await client.call_tool(
        tool_name="ec2",
        arguments={
            "operation": "list",
            "filters": [{"Name": "instance-state-name", "Values": ["running"]}],
        },
    )
    print(json.dumps(filtered_response, indent=2))

    # Example 4: Describe specific instance
    print("\n" + "=" * 60)
    print("Example 4: Describe EC2 Instance")
    print("=" * 60)
    describe_response = await client.call_tool(
        tool_name="ec2",
        arguments={"operation": "describe", "instance_id": "i-0123456789abcdef0"},
    )
    print(json.dumps(describe_response, indent=2))

    # Example 5: List ECS clusters
    print("\n" + "=" * 60)
    print("Example 5: List ECS Clusters")
    print("=" * 60)
    ecs_response = await client.call_tool(
        tool_name="ecs", arguments={"operation": "list-clusters"}
    )
    print(json.dumps(ecs_response, indent=2))

    # Example 6: Scale ECS service
    print("\n" + "=" * 60)
    print("Example 6: Scale ECS Service")
    print("=" * 60)
    scale_response = await client.call_tool(
        tool_name="ecs",
        arguments={
            "operation": "scale",
            "cluster": "production",
            "service": "web-app",
            "desired_count": 5,
        },
    )
    print(json.dumps(scale_response, indent=2))

    # Example 7: Create RDS snapshot
    print("\n" + "=" * 60)
    print("Example 7: Create RDS Snapshot")
    print("=" * 60)
    snapshot_response = await client.call_tool(
        tool_name="rds",
        arguments={
            "operation": "create-snapshot",
            "db_instance_identifier": "production-db",
            "snapshot_identifier": "backup-2024-01-15",
        },
    )
    print(json.dumps(snapshot_response, indent=2))

    # Example 8: Get CloudWatch metrics
    print("\n" + "=" * 60)
    print("Example 8: Get CloudWatch Metrics")
    print("=" * 60)
    from datetime import datetime, timedelta

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    metrics_response = await client.call_tool(
        tool_name="cloudwatch",
        arguments={
            "operation": "get-metrics",
            "namespace": "AWS/EC2",
            "metric_name": "CPUUtilization",
            "dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdef0"}],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "period": 300,
            "statistics": ["Average", "Maximum"],
        },
    )
    print(json.dumps(metrics_response, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
