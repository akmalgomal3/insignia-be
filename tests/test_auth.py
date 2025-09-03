import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint_without_token():
    response = client.get("/")
    assert response.status_code == 403  # Forbidden without token

def test_health_endpoint_without_token():
    response = client.get("/health")
    assert response.status_code == 403  # Forbidden without token

def test_root_endpoint_with_invalid_token():
    response = client.get("/", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401  # Unauthorized with invalid token

def test_health_endpoint_with_invalid_token():
    response = client.get("/health", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401  # Unauthorized with invalid token