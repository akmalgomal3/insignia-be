import asyncio
import aiohttp
from datetime import datetime
from app.models.task import Task
from app.models.task_log import TaskLog
from app.core.database import SessionLocal
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TaskExecutor:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def execute_task(self, task: Task, retry_count: int = 0) -> bool:
        """
        Execute a task by sending a POST request to the webhook URL.
        Returns True if successful, False otherwise.
        """
        try:
            # Send webhook request
            payload = task.payload or {}
            async with self.session.post(task.webhook_url, json=payload) as response:
                if response.status == 200 or response.status == 204:
                    # Log success
                    self._log_task_execution(
                        task, retry_count, "success", "Task executed successfully"
                    )
                    return True
                else:
                    # Log failure
                    message = f"Webhook request failed with status {response.status}"
                    self._log_task_execution(task, retry_count, "failed", message)
                    return False

        except Exception as e:
            # Log the error
            message = f"Task execution failed: {str(e)}"
            logger.error(f"Error executing task {task.id}: {message}")
            self._log_task_execution(task, retry_count, "failed", message)
            return False

    async def execute_task_with_retry(self, task: Task) -> bool:
        """
        Execute a task with retry logic.
        Returns True if successful, False otherwise.
        """
        retry_count = 1
        success = False

        while retry_count <= task.max_retry and not success:
            success = await self.execute_task(task, retry_count)

            if not success and retry_count < task.max_retry:
                # Wait before retrying (exponential backoff)
                wait_time = 2**retry_count
                logger.info(
                    f"Task {task.id} failed, retrying in {wait_time} seconds... (retry {retry_count + 1}/{task.max_retry})"
                )
                await asyncio.sleep(wait_time)
                retry_count += 1
            elif success:
                logger.info(f"Task {task.id} executed successfully")
            else:
                logger.error(f"Task {task.id} failed after {task.max_retry} retries")
                # Deactivate the task after max retries
                await self._deactivate_task(task)
                return False  # Explicitly return False after deactivation

        return success

    def _log_task_execution(
        self, task: Task, retry_count: int, status: str, message: str
    ):
        """
        Log task execution to the database.
        """
        db = SessionLocal()
        try:
            task_log = TaskLog(
                task_id=task.id,
                execution_time=datetime.utcnow(),
                status=status,
                retry_count=retry_count,
                message=message,
            )
            db.add(task_log)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging task execution for task {task.id}: {str(e)}")
        finally:
            db.close()

    async def _deactivate_task(self, task: Task):
        """
        Deactivate a task after it has failed all retry attempts.
        """
        db = SessionLocal()
        try:
            # Get fresh task instance from database
            fresh_task = db.query(Task).filter(Task.id == task.id).first()
            if fresh_task:
                fresh_task.status = "inactive"
                db.commit()
                logger.info(
                    f"Task {task.id} has been deactivated after exceeding max retry attempts"
                )
            else:
                logger.warning(f"Task {task.id} not found in database for deactivation")
        except Exception as e:
            logger.error(f"Error deactivating task {task.id}: {str(e)}")
            db.rollback()
        finally:
            db.close()
