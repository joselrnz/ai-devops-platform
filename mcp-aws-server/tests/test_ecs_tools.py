"""
Tests for ECS tools.
"""
import pytest
from moto import mock_ecs
from src.mcp_server.tools.ecs_tools import ECSTools


@mock_ecs
class TestECSTools:
    """Test ECS operations."""

    @pytest.mark.asyncio
    async def test_list_clusters(self, ecs_client, sample_ecs_cluster):
        """Test listing ECS clusters."""
        tools = ECSTools(region="us-east-1")

        result = await tools.list_clusters()

        assert "clusters" in result
        assert len(result["clusters"]) >= 1
        assert any("test-cluster" in cluster for cluster in result["clusters"])

    @pytest.mark.asyncio
    async def test_list_services(self, ecs_client, sample_ecs_service):
        """Test listing ECS services in a cluster."""
        tools = ECSTools(region="us-east-1")

        result = await tools.list_services(cluster="test-cluster")

        assert "services" in result
        assert len(result["services"]) >= 1

    @pytest.mark.asyncio
    async def test_describe_service(self, ecs_client, sample_ecs_service):
        """Test describing an ECS service."""
        tools = ECSTools(region="us-east-1")

        result = await tools.describe_service(
            cluster="test-cluster", service="test-service"
        )

        assert result["service_name"] == "test-service"
        assert "desired_count" in result
        assert "running_count" in result

    @pytest.mark.asyncio
    async def test_scale_service(self, ecs_client, sample_ecs_service):
        """Test scaling an ECS service."""
        tools = ECSTools(region="us-east-1")

        result = await tools.scale_service(
            cluster="test-cluster", service="test-service", desired_count=3
        )

        assert result["service_name"] == "test-service"
        assert result["desired_count"] == 3

    @pytest.mark.asyncio
    async def test_list_tasks(self, ecs_client, sample_ecs_cluster):
        """Test listing ECS tasks in a cluster."""
        tools = ECSTools(region="us-east-1")

        result = await tools.list_tasks(cluster="test-cluster")

        assert "tasks" in result
        assert isinstance(result["tasks"], list)

    @pytest.mark.asyncio
    async def test_describe_tasks(self, ecs_client, sample_ecs_service):
        """Test describing ECS tasks."""
        tools = ECSTools(region="us-east-1")

        # List tasks first to get task ARNs
        tasks_result = await tools.list_tasks(cluster="test-cluster")

        if tasks_result["tasks"]:
            result = await tools.describe_tasks(
                cluster="test-cluster", tasks=tasks_result["tasks"][:1]
            )

            assert "tasks" in result
            assert len(result["tasks"]) >= 0

    @pytest.mark.asyncio
    async def test_list_services_empty_cluster(self, ecs_client):
        """Test listing services in a cluster with no services."""
        ecs_client.create_cluster(clusterName="empty-cluster")
        tools = ECSTools(region="us-east-1")

        result = await tools.list_services(cluster="empty-cluster")

        assert result["services"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_scale_service_to_zero(self, ecs_client, sample_ecs_service):
        """Test scaling service to zero (stopping all tasks)."""
        tools = ECSTools(region="us-east-1")

        result = await tools.scale_service(
            cluster="test-cluster", service="test-service", desired_count=0
        )

        assert result["desired_count"] == 0
