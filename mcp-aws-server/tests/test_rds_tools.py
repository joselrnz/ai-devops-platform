"""
Tests for RDS tools.
"""
import pytest
from moto import mock_rds
from src.mcp_server.tools.rds_tools import RDSTools


@mock_rds
class TestRDSTools:
    """Test RDS operations."""

    @pytest.mark.asyncio
    async def test_list_instances(self, rds_client, sample_rds_instance):
        """Test listing RDS instances."""
        tools = RDSTools(region="us-east-1")

        result = await tools.list_instances()

        assert "instances" in result
        assert len(result["instances"]) >= 1
        assert any(
            inst["db_instance_identifier"] == "test-db"
            for inst in result["instances"]
        )

    @pytest.mark.asyncio
    async def test_describe_instance(self, rds_client, sample_rds_instance):
        """Test describing an RDS instance."""
        tools = RDSTools(region="us-east-1")

        result = await tools.describe_instance(db_instance_identifier="test-db")

        assert result["db_instance_identifier"] == "test-db"
        assert "status" in result
        assert "engine" in result
        assert result["engine"] == "postgres"

    @pytest.mark.asyncio
    async def test_get_instance_status(self, rds_client, sample_rds_instance):
        """Test getting RDS instance status."""
        tools = RDSTools(region="us-east-1")

        result = await tools.get_instance_status(db_instance_identifier="test-db")

        assert result["db_instance_identifier"] == "test-db"
        assert "status" in result

    @pytest.mark.asyncio
    async def test_create_snapshot(self, rds_client, sample_rds_instance):
        """Test creating an RDS snapshot."""
        tools = RDSTools(region="us-east-1")

        result = await tools.create_snapshot(
            db_instance_identifier="test-db", snapshot_identifier="test-snapshot"
        )

        assert result["snapshot_identifier"] == "test-snapshot"
        assert result["db_instance_identifier"] == "test-db"
        assert "status" in result

    @pytest.mark.asyncio
    async def test_list_snapshots(self, rds_client, sample_rds_instance):
        """Test listing RDS snapshots."""
        # Create a snapshot first
        rds_client.create_db_snapshot(
            DBSnapshotIdentifier="test-snapshot-1", DBInstanceIdentifier="test-db"
        )

        tools = RDSTools(region="us-east-1")
        result = await tools.list_snapshots(db_instance_identifier="test-db")

        assert "snapshots" in result
        assert len(result["snapshots"]) >= 1
        assert any(
            snap["snapshot_identifier"] == "test-snapshot-1"
            for snap in result["snapshots"]
        )

    @pytest.mark.asyncio
    async def test_list_snapshots_all(self, rds_client, sample_rds_instance):
        """Test listing all RDS snapshots."""
        tools = RDSTools(region="us-east-1")

        result = await tools.list_snapshots()

        assert "snapshots" in result
        assert isinstance(result["snapshots"], list)

    @pytest.mark.asyncio
    async def test_list_instances_empty(self, rds_client):
        """Test listing RDS instances when none exist."""
        tools = RDSTools(region="us-east-1")

        result = await tools.list_instances()

        assert result["instances"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_describe_nonexistent_instance(self, rds_client):
        """Test describing a non-existent RDS instance."""
        tools = RDSTools(region="us-east-1")

        with pytest.raises(Exception):
            await tools.describe_instance(db_instance_identifier="nonexistent-db")
