from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, UUID, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class TaskStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    schedule = Column(String, nullable=False)  # cron expression
    webhook_url = Column(String, nullable=False)
    payload = Column(JSONB, nullable=True)
    max_retry = Column(Integer, default=3)
    status = Column(String, default="active")  # active, inactive, deleted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
