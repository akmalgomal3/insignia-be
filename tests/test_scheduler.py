import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from app.core.task_executor import TaskExecutor
from app.core.scheduler import TaskScheduler
from app.models.task import Task
from app.models.task_log import TaskLog

# Test data
@pytest.fixture
def sample_task():
    return Task(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Task",
        schedule="* * * * *",  # Every minute
        webhook_url="https://discord.com/api/webhooks/test",
        payload={"content": "Test message"},
        max_retry=3,
        status="active",
    )


@pytest.fixture
def sample_task_log():
    return TaskLog(
        id="123e4567-e89b-12d3-a456-426614174001",
        task_id="123e4567-e89b-12d3-a456-426614174000",
        execution_time=datetime.utcnow(),
        status="success",
        retry_count=0,
        message="Test message",
    )


# Test TaskExecutor
@pytest.mark.asyncio
async def test_task_executor_success(sample_task):
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock the POST response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
            mock_response
        )

        async with TaskExecutor() as executor:
            result = await executor.execute_task(sample_task)
            assert result is True


@pytest.mark.asyncio
async def test_task_executor_failure(sample_task):
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock the POST response with error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
            mock_response
        )

        async with TaskExecutor() as executor:
            result = await executor.execute_task(sample_task)
            assert result is False


@pytest.mark.asyncio
async def test_task_executor_exception(sample_task):
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock exception
        mock_session.return_value.__aenter__.return_value.post.side_effect = Exception(
            "Network error"
        )

        async with TaskExecutor() as executor:
            result = await executor.execute_task(sample_task)
            assert result is False


@pytest.mark.asyncio
async def test_task_executor_with_retry_success(sample_task):
    with patch("aiohttp.ClientSession") as mock_session:
        # First call fails, second succeeds
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        mock_response_success = AsyncMock()
        mock_response_success.status = 200

        mock_session.return_value.__aenter__.return_value.post.side_effect = [
            mock_response_fail.__aenter__.return_value,
            mock_response_success.__aenter__.return_value,
        ]

        async with TaskExecutor() as executor:
            result = await executor.execute_task_with_retry(sample_task)
            assert result is True


# Test TaskScheduler
def test_should_execute_task():
    scheduler = TaskScheduler()
    task = Task(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Task",
        schedule="* * * * *",  # Every minute
        webhook_url="https://discord.com/api/webhooks/test",
        payload={"content": "Test message"},
        max_retry=3,
        status="active",
    )

    # Test with times that should trigger execution
    last_check = datetime(2023, 1, 1, 12, 0, 0)
    current_time = datetime(2023, 1, 1, 12, 1, 30)  # 1.5 minutes later

    result = scheduler._should_execute_task(task, last_check, current_time)
    assert result is True


def test_should_not_execute_task():
    scheduler = TaskScheduler()
    task = Task(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Task",
        schedule="0 0 * * *",  # Every day at midnight
        webhook_url="https://discord.com/api/webhooks/test",
        payload={"content": "Test message"},
        max_retry=3,
        status="active",
    )

    # Test with times that should not trigger execution
    last_check = datetime(2023, 1, 1, 12, 0, 0)
    current_time = datetime(2023, 1, 1, 12, 1, 30)  # 1.5 minutes later

    result = scheduler._should_execute_task(task, last_check, current_time)
    assert result is False