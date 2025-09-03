import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.task import Task
from app.models.task_log import TaskLog
from datetime import datetime
import asyncio

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

def test_task_deactivation_after_max_retries(auth_headers):
    """Test that a task is deactivated after exceeding max retry attempts"""
    # Create a task
    task_data = {
        "name": "Test Task",
        "schedule": "* * * * *",  # Every minute
        "webhook_url": "https://discord.com/api/webhooks/test",
        "payload": {"content": "Test message"},
        "max_retry": 2,  # Only 2 retries
        "status": "active",
    }
    
    # Create the task
    response = client.post("/tasks/", json=task_data, headers=auth_headers)
    assert response.status_code == 200
    created_task = response.json()
    task_id = created_task["id"]
    
    # Verify task is initially active
    get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "active"
    
    # Manually test the _deactivate_task method
    from app.core.task_executor import TaskExecutor
    from app.core.database import SessionLocal
    
    # Get the task from database
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        assert task is not None
        assert task.status == "active"
        
        # Call the _deactivate_task method directly (need to run in async context)
        async def test_deactivate():
            executor = TaskExecutor()
            await executor._deactivate_task(task)
        
        # Run the async function
        asyncio.run(test_deactivate())
        
        # Refresh task from database by querying again
        updated_task = db.query(Task).filter(Task.id == task_id).first()
        
        # Verify task is now inactive
        assert updated_task.status == "inactive"
        
        # Test the _log_task_execution method
        executor = TaskExecutor()
        executor._log_task_execution(updated_task, 2, "failed", "Task failed after max retries")
        
        # Verify task log was created
        log = db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.created_at.desc()).first()
        assert log is not None
        assert log.status == "failed"
        assert log.retry_count == 2
        assert "max retries" in log.message.lower()
        
    finally:
        db.close()

def test_task_execution_with_retry_logic(auth_headers):
    """Test the retry logic flow"""
    # Create a task with an invalid webhook URL that will always fail
    task_data = {
        "name": "Failing Task",
        "schedule": "* * * * *",  # Every minute
        "webhook_url": "https://discord.com/api/webhooks/invalid/invalid",  # Invalid URL
        "payload": {"content": "Test message"},
        "max_retry": 1,  # Only 1 retry
        "status": "active",
    }
    
    # Create the task
    response = client.post("/tasks/", json=task_data, headers=auth_headers)
    assert response.status_code == 200
    created_task = response.json()
    task_id = created_task["id"]
    
    # Create some task logs to simulate retries
    task_logs_data = [
        {
            "task_id": task_id,
            "execution_time": "2023-01-01T10:00:00Z",
            "status": "failed",
            "retry_count": 0,
            "message": "Task execution failed: Initial attempt"
        },
        {
            "task_id": task_id,
            "execution_time": "2023-01-01T10:01:00Z",
            "status": "failed",
            "retry_count": 1,
            "message": "Task execution failed: After 1 retry"
        }
    ]
    
    # Create the task logs
    for log_data in task_logs_data:
        response = client.post("/task-logs/", json=log_data, headers=auth_headers)
        assert response.status_code == 200
    
    # Verify task logs were created
    logs_response = client.get(f"/task-logs/task/{task_id}", headers=auth_headers)
    assert logs_response.status_code == 200
    logs_data = logs_response.json()
    assert logs_data["total"] == 2
    
    # Verify task is still active (since we only simulated the logs, not actual execution)
    get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "active"
