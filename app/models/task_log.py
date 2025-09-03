from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, UUID, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid

class TaskLogStatusEnum(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

class TaskLog(Base):
    __tablename__ = "task_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    execution_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)  # success, failed
    retry_count = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    task = relationship("Task", back_populates="logs")