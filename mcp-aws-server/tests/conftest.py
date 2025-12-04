"""
Pytest configuration and fixtures for MCP AWS Server tests.
"""
import pytest
import boto3
from moto import mock_ec2, mock_ecs, mock_rds, mock_cloudwatch
from typing import Generator
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mock AWS credentials for testing."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def ec2_client(aws_credentials):
    """Create a mocked EC2 client."""
    with mock_ec2():
        yield boto3.client("ec2", region_name="us-east-1")


@pytest.fixture
def ecs_client(aws_credentials):
    """Create a mocked ECS client."""
    with mock_ecs():
        yield boto3.client("ecs", region_name="us-east-1")


@pytest.fixture
def rds_client(aws_credentials):
    """Create a mocked RDS client."""
    with mock_rds():
        yield boto3.client("rds", region_name="us-east-1")


@pytest.fixture
def cloudwatch_client(aws_credentials):
    """Create a mocked CloudWatch client."""
    with mock_cloudwatch():
        yield boto3.client("cloudwatch", region_name="us-east-1")


@pytest.fixture
def sample_ec2_instances(ec2_client):
    """Create sample EC2 instances for testing."""
    # Create instances
    response = ec2_client.run_instances(
        ImageId="ami-12345678",
        MinCount=2,
        MaxCount=2,
        InstanceType="t2.micro",
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "test-instance-1"},
                    {"Key": "ManagedBy", "Value": "mcp-server"},
                ],
            }
        ],
    )
    return [inst["InstanceId"] for inst in response["Instances"]]


@pytest.fixture
def sample_ecs_cluster(ecs_client):
    """Create a sample ECS cluster for testing."""
    response = ecs_client.create_cluster(clusterName="test-cluster")
    return response["cluster"]["clusterArn"]


@pytest.fixture
def sample_ecs_service(ecs_client, sample_ecs_cluster):
    """Create a sample ECS service for testing."""
    # Register task definition
    ecs_client.register_task_definition(
        family="test-task",
        containerDefinitions=[
            {
                "name": "test-container",
                "image": "nginx:latest",
                "memory": 512,
            }
        ],
    )

    # Create service
    response = ecs_client.create_service(
        cluster="test-cluster",
        serviceName="test-service",
        taskDefinition="test-task",
        desiredCount=1,
    )
    return response["service"]["serviceArn"]


@pytest.fixture
def sample_rds_instance(rds_client):
    """Create a sample RDS instance for testing."""
    response = rds_client.create_db_instance(
        DBInstanceIdentifier="test-db",
        DBInstanceClass="db.t3.micro",
        Engine="postgres",
        MasterUsername="admin",
        MasterUserPassword="password123",
        AllocatedStorage=20,
    )
    return response["DBInstance"]["DBInstanceIdentifier"]


@pytest.fixture
def mcp_request():
    """Generate a sample MCP request."""
    return {
        "jsonrpc": "2.0",
        "id": "test-123",
        "method": "tools/list",
        "params": {},
    }


@pytest.fixture
def mcp_tool_request():
    """Generate a sample MCP tool execution request."""
    return {
        "jsonrpc": "2.0",
        "id": "test-456",
        "method": "tools/call",
        "params": {
            "name": "ec2",
            "arguments": {
                "operation": "list",
                "filters": [],
            },
        },
    }
