import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)


@pytest.fixture
def auth_headers(monkeypatch):
    # Mock the API token
    monkeypatch.setenv("API_TOKEN", "very-secret-token")
    
    # Reimport to apply the new token
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    
    return {"Authorization": "Bearer very-secret-token"}


@pytest.fixture
def sample_task(auth_headers):
    # First create a task for testing
    task_data = {
        "name": "Test Task",
        "schedule": "* * * * *",
        "webhook_url": "https://discord.com/api/webhooks/test",
        "payload": {"content": "Test message"},
        "max_retry": 3,
        "status": "active",
    }

    response = client.post("/tasks/", json=task_data, headers=auth_headers)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def sample_task_logs(auth_headers, sample_task):
    # Create multiple task logs for testing
    task_logs_data = [
        {
            "task_id": sample_task["id"],
            "execution_time": "2023-01-01T10:00:00Z",
            "status": "success",
            "retry_count": 0,
            "message": "Task executed successfully",
        },
        {
            "task_id": sample_task["id"],
            "execution_time": "2023-01-01T11:00:00Z",
            "status": "failed",
            "retry_count": 3,
            "message": "Task failed after 3 retries",
        },
        {
            "task_id": sample_task["id"],
            "execution_time": "2023-01-01T12:00:00Z",
            "status": "success",
            "retry_count": 1,
            "message": "Task executed successfully after 1 retry",
        },
    ]

    created_task_logs = []
    for task_log_data in task_logs_data:
        response = client.post("/task-logs/", json=task_log_data, headers=auth_headers)
        assert response.status_code == 200
        created_task_logs.append(response.json())

    return created_task_logs


def test_create_task_log(auth_headers, sample_task):
    task_log_data = {
        "task_id": sample_task["id"],
        "execution_time": "2023-01-01T10:00:00Z",
        "status": "success",
        "retry_count": 0,
        "message": "Task executed successfully",
    }

    response = client.post("/task-logs/", json=task_log_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_log_data["task_id"]
    assert data["status"] == task_log_data["status"]
    assert "id" in data


def test_get_task_log(auth_headers, sample_task):
    # First create a task log
    task_log_data = {
        "task_id": sample_task["id"],
        "execution_time": "2023-01-01T10:00:00Z",
        "status": "success",
        "retry_count": 0,
        "message": "Task executed successfully",
    }

    create_response = client.post(
        "/task-logs/", json=task_log_data, headers=auth_headers
    )
    assert create_response.status_code == 200
    created_task_log = create_response.json()

    # Then get the task log
    task_log_id = created_task_log["id"]
    get_response = client.get(f"/task-logs/{task_log_id}", headers=auth_headers)
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_log_id
    assert data["task_id"] == task_log_data["task_id"]


def test_update_task_log(auth_headers, sample_task):
    # First create a task log
    task_log_data = {
        "task_id": sample_task["id"],
        "execution_time": "2023-01-01T10:00:00Z",
        "status": "success",
        "retry_count": 0,
        "message": "Task executed successfully",
    }

    create_response = client.post(
        "/task-logs/", json=task_log_data, headers=auth_headers
    )
    assert create_response.status_code == 200
    created_task_log = create_response.json()

    # Then update the task log
    task_log_id = created_task_log["id"]
    update_data = {"status": "failed", "message": "Task execution failed"}
    update_response = client.put(
        f"/task-logs/{task_log_id}", json=update_data, headers=auth_headers
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "failed"
    assert data["message"] == "Task execution failed"
    assert data["id"] == task_log_id


def test_delete_task_log(auth_headers, sample_task):
    # First create a task log
    task_log_data = {
        "task_id": sample_task["id"],
        "execution_time": "2023-01-01T10:00:00Z",
        "status": "success",
        "retry_count": 0,
        "message": "Task executed successfully",
    }

    create_response = client.post(
        "/task-logs/", json=task_log_data, headers=auth_headers
    )
    assert create_response.status_code == 200
    created_task_log = create_response.json()

    # Then delete the task log
    task_log_id = created_task_log["id"]
    delete_response = client.delete(f"/task-logs/{task_log_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    # Try to get the deleted task log (should fail)
    get_response = client.get(f"/task-logs/{task_log_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_list_task_logs(auth_headers, sample_task_logs):
    # Test basic listing
    response = client.get("/task-logs/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "task_logs" in data
    assert "total" in data
    assert data["total"] >= 3  # At least our sample task logs
    assert len(data["task_logs"]) >= 3

    # Check that our sample task logs are in the list
    statuses = [log["status"] for log in data["task_logs"]]
    assert "success" in statuses
    assert "failed" in statuses


def test_list_task_logs_with_pagination(auth_headers, sample_task_logs):
    # Test pagination
    response = client.get("/task-logs/?skip=1&limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "task_logs" in data
    assert "total" in data
    assert data["skip"] == 1
    assert data["limit"] == 2
    assert len(data["task_logs"]) == 2


def test_list_task_logs_with_task_id_filter(
    auth_headers, sample_task, sample_task_logs
):
    # Test filtering by task_id
    response = client.get(
        f"/task-logs/?task_id={sample_task['id']}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_logs" in data
    assert "total" in data
    # Check that only task logs for our task are returned
    for log in data["task_logs"]:
        assert log["task_id"] == sample_task["id"]


def test_list_task_logs_with_status_filter(auth_headers, sample_task_logs):
    # Test filtering by status
    response = client.get("/task-logs/?status=success", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "task_logs" in data
    assert "total" in data
    # Check that only success task logs are returned
    for log in data["task_logs"]:
        assert log["status"] == "success"


def test_list_task_logs_by_task(auth_headers, sample_task, sample_task_logs):
    # Test listing task logs by task
    response = client.get(f"/task-logs/task/{sample_task['id']}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "task_logs" in data
    assert "total" in data
    # Check that all logs belong to our task
    for log in data["task_logs"]:
        assert log["task_id"] == sample_task["id"]


def test_list_task_logs_by_task_with_status_filter(
    auth_headers, sample_task, sample_task_logs
):
    # Test listing task logs by task with status filter
    response = client.get(
        f"/task-logs/task/{sample_task['id']}?status=success", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_logs" in data
    assert "total" in data
    # Check that only success logs for our task are returned
    for log in data["task_logs"]:
        assert log["task_id"] == sample_task["id"]
        assert log["status"] == "success"