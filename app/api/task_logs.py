from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import verify_token
from app.models.task_log import TaskLog
from app.models.task import Task
from app.schemas.task_log import (
    TaskLogCreate,
    TaskLogUpdate,
    TaskLog as TaskLogSchema,
    TaskLogListResponse,
)
from uuid import UUID

router = APIRouter()


@router.post("/", response_model=TaskLogSchema, dependencies=[Depends(verify_token)])
def create_task_log(task_log: TaskLogCreate, db: Session = Depends(get_db)):
    db_task_log = TaskLog(**task_log.dict())
    db.add(db_task_log)
    db.commit()
    db.refresh(db_task_log)
    return db_task_log


@router.get(
    "/{task_log_id}", response_model=TaskLogSchema, dependencies=[Depends(verify_token)]
)
def read_task_log(task_log_id: UUID, db: Session = Depends(get_db)):
    db_task_log = db.query(TaskLog).filter(TaskLog.id == task_log_id).first()
    if db_task_log is None:
        raise HTTPException(status_code=404, detail="Task log not found")
    return db_task_log


@router.put(
    "/{task_log_id}", response_model=TaskLogSchema, dependencies=[Depends(verify_token)]
)
def update_task_log(
    task_log_id: UUID, task_log: TaskLogUpdate, db: Session = Depends(get_db)
):
    db_task_log = db.query(TaskLog).filter(TaskLog.id == task_log_id).first()
    if db_task_log is None:
        raise HTTPException(status_code=404, detail="Task log not found")

    for key, value in task_log.dict(exclude_unset=True).items():
        setattr(db_task_log, key, value)

    db.commit()
    db.refresh(db_task_log)
    return db_task_log


@router.delete("/{task_log_id}", dependencies=[Depends(verify_token)])
def delete_task_log(task_log_id: UUID, db: Session = Depends(get_db)):
    db_task_log = db.query(TaskLog).filter(TaskLog.id == task_log_id).first()
    if db_task_log is None:
        raise HTTPException(status_code=404, detail="Task log not found")

    db.delete(db_task_log)
    db.commit()
    return {"message": "Task log deleted successfully"}


@router.get(
    "/", response_model=TaskLogListResponse, dependencies=[Depends(verify_token)]
)
def list_task_logs(
    skip: int = 0,
    limit: int = 100,
    task_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(TaskLog)

    # Apply filters
    if task_id:
        query = query.filter(TaskLog.task_id == task_id)
    if status:
        query = query.filter(TaskLog.status == status)

    # Apply pagination
    total = query.count()
    task_logs = query.offset(skip).limit(min(limit, 1000)).all()

    return {
        "task_logs": task_logs,
        "total": total,
        "skip": skip,
        "limit": min(limit, 1000),
    }


@router.get(
    "/task/{task_id}",
    response_model=TaskLogListResponse,
    dependencies=[Depends(verify_token)],
)
def list_task_logs_by_task(
    task_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # Verify task exists
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    query = db.query(TaskLog).filter(TaskLog.task_id == task_id)

    # Apply filters
    if status:
        query = query.filter(TaskLog.status == status)

    # Apply pagination
    total = query.count()
    task_logs = query.offset(skip).limit(min(limit, 1000)).all()

    return {
        "task_logs": task_logs,
        "total": total,
        "skip": skip,
        "limit": min(limit, 1000),
    }
