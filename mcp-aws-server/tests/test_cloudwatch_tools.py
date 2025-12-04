"""
Tests for CloudWatch tools.
"""
import pytest
from datetime import datetime, timedelta
from moto import mock_cloudwatch
from src.mcp_server.tools.cloudwatch_tools import CloudWatchTools


@mock_cloudwatch
class TestCloudWatchTools:
    """Test CloudWatch operations."""

    @pytest.mark.asyncio
    async def test_put_metric_data(self, cloudwatch_client):
        """Test putting metric data to CloudWatch."""
        tools = CloudWatchTools(region="us-east-1")

        result = await tools.put_metric_data(
            namespace="TestApp",
            metric_name="RequestCount",
            value=100.0,
            unit="Count",
        )

        assert result["namespace"] == "TestApp"
        assert result["metric_name"] == "RequestCount"
        assert result["value"] == 100.0

    @pytest.mark.asyncio
    async def test_get_metric_statistics(self, cloudwatch_client):
        """Test getting metric statistics from CloudWatch."""
        # Put some metric data first
        cloudwatch_client.put_metric_data(
            Namespace="TestApp",
            MetricData=[
                {
                    "MetricName": "CPUUtilization",
                    "Value": 75.0,
                    "Unit": "Percent",
                    "Timestamp": datetime.utcnow(),
                }
            ],
        )

        tools = CloudWatchTools(region="us-east-1")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        result = await tools.get_metric_statistics(
            namespace="TestApp",
            metric_name="CPUUtilization",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            period=300,
            statistics=["Average", "Maximum"],
        )

        assert result["metric_name"] == "CPUUtilization"
        assert "datapoints" in result

    @pytest.mark.asyncio
    async def test_list_metrics(self, cloudwatch_client):
        """Test listing CloudWatch metrics."""
        # Put some metric data first
        cloudwatch_client.put_metric_data(
            Namespace="TestApp",
            MetricData=[
                {"MetricName": "Metric1", "Value": 1.0},
                {"MetricName": "Metric2", "Value": 2.0},
            ],
        )

        tools = CloudWatchTools(region="us-east-1")
        result = await tools.list_metrics(namespace="TestApp")

        assert "metrics" in result
        # moto may not return metrics immediately, so we check structure
        assert isinstance(result["metrics"], list)

    @pytest.mark.asyncio
    async def test_put_alarm(self, cloudwatch_client):
        """Test creating a CloudWatch alarm."""
        tools = CloudWatchTools(region="us-east-1")

        result = await tools.put_alarm(
            alarm_name="HighCPU",
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=2,
            metric_name="CPUUtilization",
            namespace="AWS/EC2",
            period=300,
            statistic="Average",
            threshold=80.0,
        )

        assert result["alarm_name"] == "HighCPU"
        assert result["threshold"] == 80.0

    @pytest.mark.asyncio
    async def test_list_alarms(self, cloudwatch_client):
        """Test listing CloudWatch alarms."""
        # Create an alarm first
        cloudwatch_client.put_metric_alarm(
            AlarmName="TestAlarm",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=1,
            MetricName="CPUUtilization",
            Namespace="AWS/EC2",
            Period=300,
            Statistic="Average",
            Threshold=80.0,
        )

        tools = CloudWatchTools(region="us-east-1")
        result = await tools.list_alarms()

        assert "alarms" in result
        assert len(result["alarms"]) >= 1
        assert any(alarm["alarm_name"] == "TestAlarm" for alarm in result["alarms"])

    @pytest.mark.asyncio
    async def test_describe_alarms(self, cloudwatch_client):
        """Test describing specific CloudWatch alarms."""
        cloudwatch_client.put_metric_alarm(
            AlarmName="Alarm1",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=1,
            MetricName="CPUUtilization",
            Namespace="AWS/EC2",
            Period=300,
            Statistic="Average",
            Threshold=80.0,
        )

        tools = CloudWatchTools(region="us-east-1")
        result = await tools.describe_alarms(alarm_names=["Alarm1"])

        assert len(result["alarms"]) == 1
        assert result["alarms"][0]["alarm_name"] == "Alarm1"

    @pytest.mark.asyncio
    async def test_delete_alarm(self, cloudwatch_client):
        """Test deleting a CloudWatch alarm."""
        cloudwatch_client.put_metric_alarm(
            AlarmName="AlarmToDelete",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=1,
            MetricName="CPUUtilization",
            Namespace="AWS/EC2",
            Period=300,
            Statistic="Average",
            Threshold=80.0,
        )

        tools = CloudWatchTools(region="us-east-1")
        result = await tools.delete_alarms(alarm_names=["AlarmToDelete"])

        assert result["deleted_alarms"] == ["AlarmToDelete"]
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_list_metrics_with_dimensions(self, cloudwatch_client):
        """Test listing metrics with dimension filters."""
        tools = CloudWatchTools(region="us-east-1")

        result = await tools.list_metrics(
            namespace="AWS/EC2", dimensions=[{"Name": "InstanceId", "Value": "i-123"}]
        )

        assert isinstance(result["metrics"], list)
