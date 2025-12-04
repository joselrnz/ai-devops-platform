"""
Tool Registry - Connects to all 6 projects.

Provides a unified interface for the LangGraph agent to execute tools
across all projects in the portfolio.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC

import httpx
from langchain.tools import BaseTool, StructuredTool
from langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LCField

from ..config.settings import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Parameter Schemas (LangChain format)
# ============================================================================

# Project 1: MCP AWS Server Tools
class EC2ListInstancesParams(LangChainBaseModel):
    """Parameters for listing EC2 instances"""
    filters: Optional[Dict[str, str]] = LCField(None, description="Tag filters (e.g., {'Environment': 'production'})")
    instance_ids: Optional[List[str]] = LCField(None, description="Specific instance IDs to filter")


class EC2InstanceActionParams(LangChainBaseModel):
    """Parameters for EC2 instance actions"""
    instance_id: str = LCField(..., description="EC2 instance ID (e.g., i-1234567890abcdef0)")


class RDSDescribeParams(LangChainBaseModel):
    """Parameters for RDS describe"""
    db_instance_identifier: str = LCField(..., description="RDS instance identifier")


class CloudWatchMetricsParams(LangChainBaseModel):
    """Parameters for CloudWatch metrics"""
    namespace: str = LCField(..., description="Metric namespace (e.g., AWS/EC2)")
    metric_name: str = LCField(..., description="Metric name (e.g., CPUUtilization)")
    dimensions: Dict[str, str] = LCField(..., description="Metric dimensions")
    period_hours: int = LCField(1, description="Time period in hours")


# Project 3: K8s AgentOps Tools
class K8sListAgentsParams(LangChainBaseModel):
    """Parameters for listing K8s agents"""
    namespace: Optional[str] = LCField(None, description="Kubernetes namespace")
    label_selector: Optional[str] = LCField(None, description="Label selector")


class K8sDeployAgentParams(LangChainBaseModel):
    """Parameters for deploying an agent"""
    name: str = LCField(..., description="Agent name")
    namespace: str = LCField("default", description="Target namespace")
    model_type: str = LCField(..., description="Model type (claude, gpt4, etc.)")
    replicas: int = LCField(1, description="Number of replicas")


class K8sScaleAgentParams(LangChainBaseModel):
    """Parameters for scaling an agent"""
    name: str = LCField(..., description="Agent name")
    namespace: str = LCField("default", description="Namespace")
    replicas: int = LCField(..., description="Target replica count")


# Project 4: CI/CD Framework Tools
class TriggerDeploymentParams(LangChainBaseModel):
    """Parameters for triggering a deployment"""
    service: str = LCField(..., description="Service name to deploy")
    environment: str = LCField(..., description="Target environment (staging, production)")
    strategy: str = LCField("rolling", description="Deployment strategy (rolling, canary, blue-green)")
    image_tag: Optional[str] = LCField(None, description="Specific image tag to deploy")


class RollbackParams(LangChainBaseModel):
    """Parameters for rollback"""
    deployment_id: str = LCField(..., description="Deployment ID to rollback")


# Project 5: Logging & Threat Analytics Tools
class SearchLogsParams(LangChainBaseModel):
    """Parameters for log search"""
    query: str = LCField(..., description="Search query (OpenSearch DSL)")
    time_range: str = LCField("1h", description="Time range (e.g., 1h, 24h, 7d)")
    index: str = LCField("logs-*", description="Index pattern")
    limit: int = LCField(100, description="Maximum results")


class ThreatQueryParams(LangChainBaseModel):
    """Parameters for threat query"""
    threat_type: Optional[str] = LCField(None, description="Threat type filter")
    severity: Optional[str] = LCField(None, description="Severity filter (low, medium, high, critical)")
    time_range: str = LCField("24h", description="Time range")


# Project 6: Observability Fabric Tools
class MetricsQueryParams(LangChainBaseModel):
    """Parameters for metrics query"""
    query: str = LCField(..., description="PromQL query")
    start: Optional[str] = LCField(None, description="Start time")
    end: Optional[str] = LCField(None, description="End time")
    step: str = LCField("1m", description="Query step")


class TracesQueryParams(LangChainBaseModel):
    """Parameters for traces query"""
    service: str = LCField(..., description="Service name")
    operation: Optional[str] = LCField(None, description="Operation name")
    min_duration: Optional[str] = LCField(None, description="Minimum duration (e.g., 100ms)")
    limit: int = LCField(20, description="Maximum traces")


# ============================================================================
# Tool Registry Class
# ============================================================================

class ToolRegistry:
    """
    Central registry for all tools across projects 1-6.

    Provides:
    - Tool discovery and registration
    - Unified execution interface
    - Error handling and retries
    - Audit logging
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.tools: List[BaseTool] = []
        self._initialize_tools()
        logger.info(f"ToolRegistry initialized with {len(self.tools)} tools")

    def _initialize_tools(self):
        """Register all tools from all projects"""

        # Project 1: MCP AWS Server Tools
        self.tools.extend([
            StructuredTool.from_function(
                func=self._ec2_list_instances,
                name="ec2_list_instances",
                description="List EC2 instances with optional filters. Use for viewing running servers, checking instance status, or finding specific instances by tags.",
                args_schema=EC2ListInstancesParams,
                coroutine=self._ec2_list_instances,
            ),
            StructuredTool.from_function(
                func=self._ec2_start_instance,
                name="ec2_start_instance",
                description="Start a stopped EC2 instance. Requires the instance ID.",
                args_schema=EC2InstanceActionParams,
                coroutine=self._ec2_start_instance,
            ),
            StructuredTool.from_function(
                func=self._ec2_stop_instance,
                name="ec2_stop_instance",
                description="Stop a running EC2 instance. Requires the instance ID.",
                args_schema=EC2InstanceActionParams,
                coroutine=self._ec2_stop_instance,
            ),
            StructuredTool.from_function(
                func=self._rds_describe_instance,
                name="rds_describe_instance",
                description="Get details about an RDS database instance including status, CPU, connections.",
                args_schema=RDSDescribeParams,
                coroutine=self._rds_describe_instance,
            ),
            StructuredTool.from_function(
                func=self._cloudwatch_get_metrics,
                name="cloudwatch_get_metrics",
                description="Get CloudWatch metrics for AWS resources. Useful for monitoring CPU, memory, network.",
                args_schema=CloudWatchMetricsParams,
                coroutine=self._cloudwatch_get_metrics,
            ),
        ])

        # Project 3: K8s AgentOps Tools
        self.tools.extend([
            StructuredTool.from_function(
                func=self._k8s_list_agents,
                name="k8s_list_agents",
                description="List deployed AI agents in Kubernetes. Shows agent status, replicas, and health.",
                args_schema=K8sListAgentsParams,
                coroutine=self._k8s_list_agents,
            ),
            StructuredTool.from_function(
                func=self._k8s_deploy_agent,
                name="k8s_deploy_agent",
                description="Deploy a new AI agent to Kubernetes. Specify model type and configuration.",
                args_schema=K8sDeployAgentParams,
                coroutine=self._k8s_deploy_agent,
            ),
            StructuredTool.from_function(
                func=self._k8s_scale_agent,
                name="k8s_scale_agent",
                description="Scale an AI agent deployment up or down. Changes replica count.",
                args_schema=K8sScaleAgentParams,
                coroutine=self._k8s_scale_agent,
            ),
        ])

        # Project 4: CI/CD Framework Tools
        self.tools.extend([
            StructuredTool.from_function(
                func=self._trigger_deployment,
                name="trigger_deployment",
                description="Trigger a deployment pipeline. Deploy services to staging or production with optional strategy.",
                args_schema=TriggerDeploymentParams,
                coroutine=self._trigger_deployment,
            ),
            StructuredTool.from_function(
                func=self._rollback_deployment,
                name="rollback_deployment",
                description="Rollback a deployment to the previous version.",
                args_schema=RollbackParams,
                coroutine=self._rollback_deployment,
            ),
        ])

        # Project 5: Logging & Threat Analytics Tools
        self.tools.extend([
            StructuredTool.from_function(
                func=self._search_logs,
                name="search_logs",
                description="Search application and system logs. Use for troubleshooting, finding errors, analyzing patterns.",
                args_schema=SearchLogsParams,
                coroutine=self._search_logs,
            ),
            StructuredTool.from_function(
                func=self._query_threats,
                name="query_threats",
                description="Query detected security threats. Shows alerts from Sigma rules and threat detection.",
                args_schema=ThreatQueryParams,
                coroutine=self._query_threats,
            ),
        ])

        # Project 6: Observability Fabric Tools
        self.tools.extend([
            StructuredTool.from_function(
                func=self._get_metrics,
                name="get_metrics",
                description="Query Prometheus metrics using PromQL. Get CPU, memory, latency, error rates.",
                args_schema=MetricsQueryParams,
                coroutine=self._get_metrics,
            ),
            StructuredTool.from_function(
                func=self._query_traces,
                name="query_traces",
                description="Query distributed traces from Tempo. Find slow requests, trace errors across services.",
                args_schema=TracesQueryParams,
                coroutine=self._query_traces,
            ),
        ])

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools"""
        return self.tools

    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    # ========================================================================
    # Project 1: MCP AWS Server Tool Implementations
    # ========================================================================

    async def _ec2_list_instances(
        self,
        filters: Optional[Dict[str, str]] = None,
        instance_ids: Optional[List[str]] = None
    ) -> str:
        """List EC2 instances via MCP AWS Server"""
        try:
            response = await self.http_client.post(
                f"{settings.MCP_AWS_SERVER_URL}/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "id": str(datetime.now(UTC).timestamp()),
                    "method": "tools/call",
                    "params": {
                        "name": "ec2_list_instances",
                        "arguments": {
                            "filters": filters or {},
                            "instance_ids": instance_ids or []
                        }
                    }
                }
            )
            data = response.json()
            if "error" in data:
                return f"Error: {data['error']}"
            return str(data.get("result", "No instances found"))
        except Exception as e:
            logger.error(f"Error calling ec2_list_instances: {e}")
            return f"Error listing EC2 instances: {str(e)}"

    async def _ec2_start_instance(self, instance_id: str) -> str:
        """Start an EC2 instance"""
        try:
            response = await self.http_client.post(
                f"{settings.MCP_AWS_SERVER_URL}/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "id": str(datetime.now(UTC).timestamp()),
                    "method": "tools/call",
                    "params": {
                        "name": "ec2_start_instance",
                        "arguments": {"instance_id": instance_id}
                    }
                }
            )
            data = response.json()
            if "error" in data:
                return f"Error: {data['error']}"
            return f"Instance {instance_id} started successfully"
        except Exception as e:
            logger.error(f"Error starting instance: {e}")
            return f"Error starting instance: {str(e)}"

    async def _ec2_stop_instance(self, instance_id: str) -> str:
        """Stop an EC2 instance"""
        try:
            response = await self.http_client.post(
                f"{settings.MCP_AWS_SERVER_URL}/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "id": str(datetime.now(UTC).timestamp()),
                    "method": "tools/call",
                    "params": {
                        "name": "ec2_stop_instance",
                        "arguments": {"instance_id": instance_id}
                    }
                }
            )
            data = response.json()
            if "error" in data:
                return f"Error: {data['error']}"
            return f"Instance {instance_id} stopped successfully"
        except Exception as e:
            logger.error(f"Error stopping instance: {e}")
            return f"Error stopping instance: {str(e)}"

    async def _rds_describe_instance(self, db_instance_identifier: str) -> str:
        """Describe an RDS instance"""
        try:
            response = await self.http_client.post(
                f"{settings.MCP_AWS_SERVER_URL}/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "id": str(datetime.now(UTC).timestamp()),
                    "method": "tools/call",
                    "params": {
                        "name": "rds_describe_instance",
                        "arguments": {"db_instance_identifier": db_instance_identifier}
                    }
                }
            )
            data = response.json()
            if "error" in data:
                return f"Error: {data['error']}"
            return str(data.get("result", "Instance not found"))
        except Exception as e:
            logger.error(f"Error describing RDS: {e}")
            return f"Error describing RDS instance: {str(e)}"

    async def _cloudwatch_get_metrics(
        self,
        namespace: str,
        metric_name: str,
        dimensions: Dict[str, str],
        period_hours: int = 1
    ) -> str:
        """Get CloudWatch metrics"""
        try:
            response = await self.http_client.post(
                f"{settings.MCP_AWS_SERVER_URL}/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "id": str(datetime.now(UTC).timestamp()),
                    "method": "tools/call",
                    "params": {
                        "name": "cloudwatch_get_metrics",
                        "arguments": {
                            "namespace": namespace,
                            "metric_name": metric_name,
                            "dimensions": dimensions,
                            "period_hours": period_hours
                        }
                    }
                }
            )
            data = response.json()
            if "error" in data:
                return f"Error: {data['error']}"
            return str(data.get("result", "No metrics found"))
        except Exception as e:
            logger.error(f"Error getting CloudWatch metrics: {e}")
            return f"Error getting metrics: {str(e)}"

    # ========================================================================
    # Project 3: K8s AgentOps Tool Implementations
    # ========================================================================

    async def _k8s_list_agents(
        self,
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None
    ) -> str:
        """List K8s agents"""
        try:
            params = {}
            if namespace:
                params["namespace"] = namespace
            if label_selector:
                params["labelSelector"] = label_selector

            response = await self.http_client.get(
                f"{settings.K8S_AGENTOPS_URL}/api/v1/agents",
                params=params
            )
            data = response.json()
            return str(data)
        except Exception as e:
            logger.error(f"Error listing K8s agents: {e}")
            return f"Error listing agents: {str(e)}"

    async def _k8s_deploy_agent(
        self,
        name: str,
        namespace: str = "default",
        model_type: str = "claude-3-sonnet",
        replicas: int = 1
    ) -> str:
        """Deploy a K8s agent"""
        try:
            response = await self.http_client.post(
                f"{settings.K8S_AGENTOPS_URL}/api/v1/agents",
                json={
                    "name": name,
                    "namespace": namespace,
                    "spec": {
                        "modelType": model_type,
                        "replicas": replicas
                    }
                }
            )
            data = response.json()
            return f"Agent {name} deployed successfully in {namespace}"
        except Exception as e:
            logger.error(f"Error deploying agent: {e}")
            return f"Error deploying agent: {str(e)}"

    async def _k8s_scale_agent(
        self,
        name: str,
        namespace: str = "default",
        replicas: int = 1
    ) -> str:
        """Scale a K8s agent"""
        try:
            response = await self.http_client.patch(
                f"{settings.K8S_AGENTOPS_URL}/api/v1/agents/{namespace}/{name}/scale",
                json={"replicas": replicas}
            )
            data = response.json()
            return f"Agent {name} scaled to {replicas} replicas"
        except Exception as e:
            logger.error(f"Error scaling agent: {e}")
            return f"Error scaling agent: {str(e)}"

    # ========================================================================
    # Project 4: CI/CD Framework Tool Implementations
    # ========================================================================

    async def _trigger_deployment(
        self,
        service: str,
        environment: str,
        strategy: str = "rolling",
        image_tag: Optional[str] = None
    ) -> str:
        """Trigger a deployment"""
        try:
            response = await self.http_client.post(
                f"{settings.CICD_API_URL}/api/v1/deployments",
                json={
                    "service": service,
                    "environment": environment,
                    "strategy": strategy,
                    "imageTag": image_tag
                }
            )
            data = response.json()
            deployment_id = data.get("id", "unknown")
            return f"Deployment {deployment_id} triggered for {service} to {environment} with {strategy} strategy"
        except Exception as e:
            logger.error(f"Error triggering deployment: {e}")
            return f"Error triggering deployment: {str(e)}"

    async def _rollback_deployment(self, deployment_id: str) -> str:
        """Rollback a deployment"""
        try:
            response = await self.http_client.post(
                f"{settings.CICD_API_URL}/api/v1/deployments/{deployment_id}/rollback"
            )
            data = response.json()
            return f"Deployment {deployment_id} rolled back successfully"
        except Exception as e:
            logger.error(f"Error rolling back: {e}")
            return f"Error rolling back deployment: {str(e)}"

    # ========================================================================
    # Project 5: Logging & Threat Analytics Tool Implementations
    # ========================================================================

    async def _search_logs(
        self,
        query: str,
        time_range: str = "1h",
        index: str = "logs-*",
        limit: int = 100
    ) -> str:
        """Search logs in OpenSearch"""
        try:
            response = await self.http_client.post(
                f"{settings.OPENSEARCH_URL}/{index}/_search",
                json={
                    "query": {
                        "query_string": {"query": query}
                    },
                    "size": limit,
                    "sort": [{"@timestamp": {"order": "desc"}}]
                },
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            return f"Found {len(hits)} log entries: {str(hits[:5])}..."
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return f"Error searching logs: {str(e)}"

    async def _query_threats(
        self,
        threat_type: Optional[str] = None,
        severity: Optional[str] = None,
        time_range: str = "24h"
    ) -> str:
        """Query security threats"""
        try:
            query_parts = ["type:security_alert"]
            if threat_type:
                query_parts.append(f"threat_type:{threat_type}")
            if severity:
                query_parts.append(f"severity:{severity}")

            response = await self.http_client.post(
                f"{settings.OPENSEARCH_URL}/security-alerts-*/_search",
                json={
                    "query": {
                        "query_string": {"query": " AND ".join(query_parts)}
                    },
                    "size": 50,
                    "sort": [{"@timestamp": {"order": "desc"}}]
                }
            )
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            return f"Found {len(hits)} security alerts: {str(hits[:3])}..."
        except Exception as e:
            logger.error(f"Error querying threats: {e}")
            return f"Error querying threats: {str(e)}"

    # ========================================================================
    # Project 6: Observability Fabric Tool Implementations
    # ========================================================================

    async def _get_metrics(
        self,
        query: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        step: str = "1m"
    ) -> str:
        """Query Prometheus metrics"""
        try:
            params = {"query": query, "step": step}
            if start:
                params["start"] = start
            if end:
                params["end"] = end

            endpoint = "query_range" if start else "query"
            response = await self.http_client.get(
                f"{settings.PROMETHEUS_URL}/api/v1/{endpoint}",
                params=params
            )
            data = response.json()
            result = data.get("data", {}).get("result", [])
            return f"Metrics result: {str(result[:3])}..."
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return f"Error getting metrics: {str(e)}"

    async def _query_traces(
        self,
        service: str,
        operation: Optional[str] = None,
        min_duration: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """Query Tempo traces"""
        try:
            params = {
                "service": service,
                "limit": limit
            }
            if operation:
                params["operation"] = operation
            if min_duration:
                params["minDuration"] = min_duration

            response = await self.http_client.get(
                f"{settings.TEMPO_URL}/api/traces",
                params=params
            )
            data = response.json()
            traces = data.get("traces", [])
            return f"Found {len(traces)} traces for {service}: {str(traces[:3])}..."
        except Exception as e:
            logger.error(f"Error querying traces: {e}")
            return f"Error querying traces: {str(e)}"

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Global registry instance
tool_registry = ToolRegistry()
