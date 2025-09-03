from fastapi import APIRouter
from . import tasks, task_logs

router = APIRouter()

router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(task_logs.router, prefix="/task-logs", tags=["task_logs"])