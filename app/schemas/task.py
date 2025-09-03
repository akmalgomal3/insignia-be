from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.task_log import TaskLogBase

class TaskBase(BaseModel):
    name: str
    schedule: str
    webhook_url: str
    payload: Optional[dict] = None
    max_retry: int = 3
    status: str = "active"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    name: Optional[str] = None
    schedule: Optional[str] = None
    webhook_url: Optional[str] = None
    payload: Optional[dict] = None
    max_retry: Optional[int] = None
    status: Optional[str] = None

class TaskInDBBase(TaskBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Task(TaskInDBBase):
    logs: Optional[list["TaskLogBase"]] = []

class TaskInDB(TaskInDBBase):
    pass

class TaskListResponse(BaseModel):
    tasks: List[Task]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True