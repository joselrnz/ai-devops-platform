"""
Unit tests for the example Python application.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_check(self):
        """Test health check returns 200 and correct status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_readiness_check(self):
        """Test readiness check returns 200 and correct status."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["version"] == "1.0.0"


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome" in data["message"]


class TestProcessEndpoint:
    """Test message processing endpoint."""

    def test_process_message_success(self):
        """Test successful message processing."""
        test_message = "Hello, World!"
        response = client.post("/process", json={"message": test_message})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == test_message
        assert data["reversed"] == test_message[::-1]
        assert data["length"] == len(test_message)

    def test_process_empty_message(self):
        """Test processing empty message returns 400."""
        response = client.post("/process", json={"message": ""})
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_process_unicode_message(self):
        """Test processing Unicode message."""
        test_message = "Hello 世界 🌍"
        response = client.post("/process", json={"message": test_message})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == test_message
        assert data["reversed"] == test_message[::-1]
        assert data["length"] == len(test_message)

    def test_process_long_message(self):
        """Test processing long message."""
        test_message = "A" * 10000
        response = client.post("/process", json={"message": test_message})

        assert response.status_code == 200
        data = response.json()
        assert data["length"] == 10000


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    def test_metrics_endpoint(self):
        """Test metrics endpoint is accessible."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
