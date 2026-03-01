"""
Basic tests for Canon Builder API
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Canon Builder API"
    assert data["status"] == "running"


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data


def test_login_demo_user(client):
    """Test login with demo credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "demo"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401


def test_query_without_auth(client):
    """Test query endpoint without authentication"""
    response = client.post(
        "/api/v1/query",
        json={"question": "What is the magic system?"}
    )
    assert response.status_code == 403  # Should require authentication
