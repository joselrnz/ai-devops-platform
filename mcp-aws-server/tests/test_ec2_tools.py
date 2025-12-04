"""
Tests for EC2 tools.
"""
import pytest
from moto import mock_ec2
from src.mcp_server.tools.ec2_tools import EC2Tools


@mock_ec2
class TestEC2Tools:
    """Test EC2 operations."""

    @pytest.mark.asyncio
    async def test_list_instances(self, ec2_client, sample_ec2_instances):
        """Test listing EC2 instances."""
        tools = EC2Tools(region="us-east-1")

        result = await tools.list_instances()

        assert "instances" in result
        assert len(result["instances"]) == 2
        assert all(inst["instance_id"] in sample_ec2_instances for inst in result["instances"])

    @pytest.mark.asyncio
    async def test_list_instances_with_filters(self, ec2_client, sample_ec2_instances):
        """Test listing EC2 instances with filters."""
        tools = EC2Tools(region="us-east-1")

        filters = [{"Name": "tag:ManagedBy", "Values": ["mcp-server"]}]
        result = await tools.list_instances(filters=filters)

        assert len(result["instances"]) == 2

    @pytest.mark.asyncio
    async def test_describe_instance(self, ec2_client, sample_ec2_instances):
        """Test describing a specific EC2 instance."""
        tools = EC2Tools(region="us-east-1")
        instance_id = sample_ec2_instances[0]

        result = await tools.describe_instance(instance_id=instance_id)

        assert result["instance_id"] == instance_id
        assert "state" in result
        assert "instance_type" in result

    @pytest.mark.asyncio
    async def test_start_instance(self, ec2_client, sample_ec2_instances):
        """Test starting an EC2 instance."""
        tools = EC2Tools(region="us-east-1")
        instance_id = sample_ec2_instances[0]

        # Stop instance first
        ec2_client.stop_instances(InstanceIds=[instance_id])

        result = await tools.start_instance(instance_id=instance_id)

        assert result["instance_id"] == instance_id
        assert result["previous_state"] == "stopped"
        assert result["current_state"] in ["pending", "running"]

    @pytest.mark.asyncio
    async def test_stop_instance(self, ec2_client, sample_ec2_instances):
        """Test stopping an EC2 instance."""
        tools = EC2Tools(region="us-east-1")
        instance_id = sample_ec2_instances[0]

        result = await tools.stop_instance(instance_id=instance_id)

        assert result["instance_id"] == instance_id
        assert result["current_state"] in ["stopping", "stopped"]

    @pytest.mark.asyncio
    async def test_list_instances_empty(self, ec2_client):
        """Test listing instances when none exist."""
        tools = EC2Tools(region="us-east-1")

        result = await tools.list_instances()

        assert result["instances"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_describe_nonexistent_instance(self, ec2_client):
        """Test describing a non-existent instance raises error."""
        tools = EC2Tools(region="us-east-1")

        with pytest.raises(Exception):
            await tools.describe_instance(instance_id="i-nonexistent")

    @pytest.mark.asyncio
    async def test_list_instances_max_results(self, ec2_client):
        """Test listing instances with max_results parameter."""
        # Create 5 instances
        ec2_client.run_instances(ImageId="ami-12345678", MinCount=5, MaxCount=5)

        tools = EC2Tools(region="us-east-1")
        result = await tools.list_instances(max_results=3)

        assert len(result["instances"]) == 3
