from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class TaskLogBase(BaseModel):
    task_id: UUID
    execution_time: datetime
    status: str
    retry_count: int = 0
    message: Optional[str] = None

class TaskLogCreate(TaskLogBase):
    pass

class TaskLogUpdate(TaskLogBase):
    task_id: Optional[UUID] = None
    execution_time: Optional[datetime] = None
    status: Optional[str] = None
    retry_count: Optional[int] = None
    message: Optional[str] = None

class TaskLogInDBBase(TaskLogBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaskLog(TaskLogInDBBase):
    pass

class TaskLogInDB(TaskLogInDBBase):
    pass

class TaskLogListResponse(BaseModel):
    task_logs: List[TaskLog]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True