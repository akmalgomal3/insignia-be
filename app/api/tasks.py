from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.core.security import verify_token
from app.models.task import Task
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    Task as TaskSchema,
    TaskListResponse,
)
from uuid import UUID

router = APIRouter()


@router.post("/", response_model=TaskSchema, dependencies=[Depends(verify_token)])
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get(
    "/{task_id}", response_model=TaskSchema, dependencies=[Depends(verify_token)]
)
def read_task(task_id: UUID, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put(
    "/{task_id}", response_model=TaskSchema, dependencies=[Depends(verify_token)]
)
def update_task(task_id: UUID, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}", dependencies=[Depends(verify_token)])
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}


@router.get("/", response_model=TaskListResponse, dependencies=[Depends(verify_token)])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task)

    # Apply filters
    if status:
        query = query.filter(Task.status == status)
    if search:
        query = query.filter(Task.name.contains(search))

    # Apply pagination
    total = query.count()
    tasks = query.offset(skip).limit(min(limit, 1000)).all()

    return {"tasks": tasks, "total": total, "skip": skip, "limit": min(limit, 1000)}
