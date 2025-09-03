import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint_without_token():
    response = client.get("/")
    assert response.status_code == 200  # Root endpoint is public

def test_health_endpoint_without_token():
    response = client.get("/health")
    assert response.status_code == 403  # Health endpoint requires auth

def test_root_endpoint_with_invalid_token():
    response = client.get("/", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 200  # Root endpoint is public

def test_health_endpoint_with_invalid_token():
    response = client.get("/health", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401  # Unauthorized with invalid token

def test_root_endpoint_with_valid_token(monkeypatch):
    # Mock the API token
    monkeypatch.setenv("API_TOKEN", "very-secret-token")
    
    # Reimport to apply the new token
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    
    response = client.get("/", headers={"Authorization": "Bearer very-secret-token"})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_health_endpoint_with_valid_token(monkeypatch):
    # Mock the API token
    monkeypatch.setenv("API_TOKEN", "very-secret-token")
    
    # Reimport to apply the new token
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    
    response = client.get("/health", headers={"Authorization": "Bearer very-secret-token"})
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}