from fastapi import APIRouter
from . import tasks, task_logs, router

api_router = APIRouter()

api_router.include_router(router.router)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(task_logs.router, prefix="/task-logs", tags=["task_logs"])
