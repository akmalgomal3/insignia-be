import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.task import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

client = TestClient(app)

@pytest.fixture
def auth_headers(monkeypatch):
    # Mock the API token
    monkeypatch.setenv("API_TOKEN", "test-token")
    
    # Reimport to apply the new token
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def sample_tasks(auth_headers):
    # Create multiple tasks for testing
    tasks_data = [
        {
            "name": "Test Task 1",
            "schedule": "* * * * *",
            "webhook_url": "https://discord.com/api/webhooks/test1",
            "payload": {"content": "Test message 1"},
            "max_retry": 3,
            "status": "active"
        },
        {
            "name": "Test Task 2",
            "schedule": "0 * * * *",
            "webhook_url": "https://discord.com/api/webhooks/test2",
            "payload": {"content": "Test message 2"},
            "max_retry": 5,
            "status": "inactive"
        },
        {
            "name": "Another Task",
            "schedule": "0 0 * * *",
            "webhook_url": "https://discord.com/api/webhooks/test3",
            "payload": {"content": "Test message 3"},
            "max_retry": 2,
            "status": "active"
        }
    ]
    
    created_tasks = []
    for task_data in tasks_data:
        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        assert response.status_code == 200
        created_tasks.append(response.json())
    
    return created_tasks

def test_create_task(auth_headers):
    task_data = {
        "name": "Test Task",
        "schedule": "* * * * *",
        "webhook_url": "https://discord.com/api/webhooks/test",
        "payload": {"content": "Test message"},
        "max_retry": 3,
        "status": "active"
    }
    
    response = client.post("/tasks/", json=task_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == task_data["name"]
    assert data["schedule"] == task_data["schedule"]
    assert "id" in data

def test_get_task(auth_headers):
    # First create a task
    task_data = {
        "name": "Test Task",
        "schedule": "* * * * *",
        "webhook_url": "https://discord.com/api/webhooks/test",
        "payload": {"content": "Test message"},
        "max_retry": 3,
        "status": "active"
    }
    
    create_response = client.post("/tasks/", json=task_data, headers=auth_headers)
    assert create_response.status_code == 200
    created_task = create_response.json()
    
    # Then get the task
    task_id = created_task["id"]
    get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["name"] == task_data["name"]

def test_update_task(auth_headers):
    # First create a task
    task_data = {
        "name": "Test Task",
        "schedule": "* * * * *",
        "webhook_url": "https://discord.com/api/webhooks/test",
        "payload": {"content": "Test message"},
        "max_retry": 3,
        "status": "active"
    }
    
    create_response = client.post("/tasks/", json=task_data, headers=auth_headers)
    assert create_response.status_code == 200
    created_task = create_response.json()
    
    # Then update the task
    task_id = created_task["id"]
    update_data = {"name": "Updated Task Name"}
    update_response = client.put(f"/tasks/{task_id}", json=update_data, headers=auth_headers)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Task Name"
    assert data["id"] == task_id

def test_delete_task(auth_headers):
    # First create a task
    task_data = {
        "name": "Test Task",
        "schedule": "* * * * *",
        "webhook_url": "https://discord.com/api/webhooks/test",
        "payload": {"content": "Test message"},
        "max_retry": 3,
        "status": "active"
    }
    
    create_response = client.post("/tasks/", json=task_data, headers=auth_headers)
    assert create_response.status_code == 200
    created_task = create_response.json()
    
    # Then delete the task
    task_id = created_task["id"]
    delete_response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    
    # Try to get the deleted task (should fail)
    get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_response.status_code == 404

def test_list_tasks(auth_headers, sample_tasks):
    # Test basic listing
    response = client.get("/tasks/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    assert data["total"] >= 3  # At least our sample tasks
    assert len(data["tasks"]) >= 3
    
    # Check that our sample tasks are in the list
    task_names = [task["name"] for task in data["tasks"]]
    assert "Test Task 1" in task_names
    assert "Test Task 2" in task_names
    assert "Another Task" in task_names

def test_list_tasks_with_pagination(auth_headers, sample_tasks):
    # Test pagination
    response = client.get("/tasks/?skip=1&limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    assert data["skip"] == 1
    assert data["limit"] == 2
    assert len(data["tasks"]) == 2

def test_list_tasks_with_status_filter(auth_headers, sample_tasks):
    # Test filtering by status
    response = client.get("/tasks/?status=active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    # Check that only active tasks are returned
    for task in data["tasks"]:
        assert task["status"] == "active"

def test_list_tasks_with_search_filter(auth_headers, sample_tasks):
    # Test search by name
    response = client.get("/tasks/?search=Test", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    # Check that only tasks with "Test" in the name are returned
    for task in data["tasks"]:
        assert "Test" in task["name"]