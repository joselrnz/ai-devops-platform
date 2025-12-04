"""
CloudWatch Tools - AWS CloudWatch monitoring operations.

Provides MCP tools for metrics, alarms, and log operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ...utils.circuit_breaker import circuit_breaker
from ...utils.audit import audit_log

logger = logging.getLogger(__name__)


class CloudWatchTools:
    """AWS CloudWatch operations exposed as MCP tools"""

    def __init__(self):
        """Initialize CloudWatch client"""
        self.cloudwatch_client = boto3.client("cloudwatch")

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of CloudWatch tools"""
        return [
            {
                "name": "cloudwatch.get_metric_data",
                "description": "Get metric data from CloudWatch",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "metric_name": {"type": "string"},
                        "dimensions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "Name": {"type": "string"},
                                    "Value": {"type": "string"},
                                },
                            },
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period in seconds",
                            "default": 300,
                        },
                        "hours_back": {
                            "type": "integer",
                            "description": "Hours of data to retrieve",
                            "default": 1,
                        },
                    },
                    "required": ["namespace", "metric_name"],
                },
            },
            {
                "name": "cloudwatch.list_alarms",
                "description": "List CloudWatch alarms",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "state_value": {
                            "type": "string",
                            "enum": ["OK", "ALARM", "INSUFFICIENT_DATA"],
                            "description": "Filter by alarm state",
                        },
                    },
                },
            },
            {
                "name": "cloudwatch.describe_alarm",
                "description": "Get detailed information about an alarm",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "alarm_name": {"type": "string"},
                    },
                    "required": ["alarm_name"],
                },
            },
            {
                "name": "cloudwatch.put_metric_alarm",
                "description": "Create or update a CloudWatch alarm",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "alarm_name": {"type": "string"},
                        "metric_name": {"type": "string"},
                        "namespace": {"type": "string"},
                        "threshold": {"type": "number"},
                        "comparison_operator": {"type": "string"},
                        "evaluation_periods": {"type": "integer"},
                    },
                    "required": [
                        "alarm_name",
                        "metric_name",
                        "namespace",
                        "threshold",
                        "comparison_operator",
                        "evaluation_periods",
                    ],
                },
            },
        ]

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CloudWatch operation"""
        operation_map = {
            "get_metric_data": self.get_metric_data,
            "list_alarms": self.list_alarms,
            "describe_alarm": self.describe_alarm,
            "put_metric_alarm": self.put_metric_alarm,
        }

        if operation not in operation_map:
            raise ValueError(f"Unknown CloudWatch operation: {operation}")

        handler = operation_map[operation]
        return await handler(**parameters)

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="cloudwatch.get_metric_data")
    async def get_metric_data(
        self,
        namespace: str,
        metric_name: str,
        dimensions: Optional[List[Dict[str, str]]] = None,
        period: int = 300,
        hours_back: int = 1,
    ) -> Dict[str, Any]:
        """Get CloudWatch metric data"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)

            metric_stat = {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": metric_name,
                },
                "Period": period,
                "Stat": "Average",
            }

            if dimensions:
                metric_stat["Metric"]["Dimensions"] = dimensions

            response = self.cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions or [],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=["Average", "Sum", "Maximum", "Minimum"],
            )

            datapoints = sorted(
                response.get("Datapoints", []), key=lambda x: x["Timestamp"]
            )

            return {
                "metric_name": metric_name,
                "namespace": namespace,
                "datapoints": [
                    {
                        "timestamp": dp["Timestamp"].isoformat(),
                        "average": dp.get("Average"),
                        "sum": dp.get("Sum"),
                        "maximum": dp.get("Maximum"),
                        "minimum": dp.get("Minimum"),
                    }
                    for dp in datapoints
                ],
                "count": len(datapoints),
            }

        except ClientError as e:
            logger.error(f"Error getting metric data: {e}")
            raise

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="cloudwatch.list_alarms")
    async def list_alarms(self, state_value: Optional[str] = None) -> Dict[str, Any]:
        """List CloudWatch alarms"""
        try:
            kwargs = {}
            if state_value:
                kwargs["StateValue"] = state_value

            response = self.cloudwatch_client.describe_alarms(**kwargs)

            alarms = []
            for alarm in response.get("MetricAlarms", []):
                alarms.append({
                    "alarm_name": alarm["AlarmName"],
                    "state": alarm["StateValue"],
                    "state_reason": alarm["StateReason"],
                    "metric_name": alarm["MetricName"],
                    "namespace": alarm["Namespace"],
                    "threshold": alarm["Threshold"],
                    "comparison_operator": alarm["ComparisonOperator"],
                })

            return {"alarms": alarms, "count": len(alarms)}

        except ClientError as e:
            logger.error(f"Error listing alarms: {e}")
            raise

    @circuit_breaker(failure_threshold=5, timeout=60)
    @audit_log(operation="cloudwatch.describe_alarm")
    async def describe_alarm(self, alarm_name: str) -> Dict[str, Any]:
        """Describe a specific alarm"""
        try:
            response = self.cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])

            if not response.get("MetricAlarms"):
                raise ValueError(f"Alarm not found: {alarm_name}")

            alarm = response["MetricAlarms"][0]

            return {
                "alarm_name": alarm["AlarmName"],
                "alarm_arn": alarm["AlarmArn"],
                "state": alarm["StateValue"],
                "state_reason": alarm["StateReason"],
                "state_updated_at": alarm["StateUpdatedTimestamp"].isoformat(),
                "metric_name": alarm["MetricName"],
                "namespace": alarm["Namespace"],
                "threshold": alarm["Threshold"],
                "comparison_operator": alarm["ComparisonOperator"],
                "evaluation_periods": alarm["EvaluationPeriods"],
                "period": alarm["Period"],
            }

        except ClientError as e:
            logger.error(f"Error describing alarm {alarm_name}: {e}")
            raise

    @circuit_breaker(failure_threshold=3, timeout=60)
    @audit_log(operation="cloudwatch.put_metric_alarm", sensitive=True)
    async def put_metric_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        namespace: str,
        threshold: float,
        comparison_operator: str,
        evaluation_periods: int,
        period: int = 300,
        statistic: str = "Average",
    ) -> Dict[str, Any]:
        """Create or update a CloudWatch alarm"""
        try:
            self.cloudwatch_client.put_metric_alarm(
                AlarmName=alarm_name,
                MetricName=metric_name,
                Namespace=namespace,
                Threshold=threshold,
                ComparisonOperator=comparison_operator,
                EvaluationPeriods=evaluation_periods,
                Period=period,
                Statistic=statistic,
            )

            return {
                "alarm_name": alarm_name,
                "metric_name": metric_name,
                "threshold": threshold,
                "message": f"Alarm {alarm_name} created/updated successfully",
            }

        except ClientError as e:
            logger.error(f"Error creating/updating alarm {alarm_name}: {e}")
            raise
