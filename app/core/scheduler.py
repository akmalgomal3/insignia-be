import asyncio
import logging
from datetime import datetime, timezone
from croniter import croniter
from app.models.task import Task
from app.core.database import SessionLocal
from app.core.task_executor import TaskExecutor
from sqlalchemy import and_

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.running = False
        self.last_check = None
    
    async def start(self):
        """Start the task scheduler"""
        self.running = True
        self.last_check = datetime.now(timezone.utc)
        logger.info("Task scheduler started")
        
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)
                logger.debug(f"Scheduler check - Last: {self.last_check.isoformat()}, Current: {current_time.isoformat()}")
                await self._check_and_execute_tasks(self.last_check, current_time)
                self.last_check = current_time

                # Check every minute
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in scheduler: {str(e)}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop the task scheduler"""
        self.running = False
        logger.info("Task scheduler stopped")
    
    async def _check_and_execute_tasks(self, last_check: datetime, current_time: datetime):
        """Check for tasks that need to be executed and execute them"""
        db = SessionLocal()
        try:
            # Get all active tasks
            tasks = db.query(Task).filter(Task.status == "active").all()
            
            if tasks:
                logger.debug(f"Checking {len(tasks)} active tasks")

            for task in tasks:
                logger.debug(f"Checking task {task.id} with schedule '{task.schedule}'")
                if self._should_execute_task(task, last_check, current_time):
                    logger.info(f"Executing task {task.id}: {task.name}")

                    # Execute task with retry logic
                    async with TaskExecutor() as executor:
                        await executor.execute_task_with_retry(task)
        except Exception as e:
            logger.error(f"Error checking tasks: {str(e)}")
        finally:
            db.close()
    
    def _should_execute_task(self, task: Task, last_check: datetime, current_time: datetime) -> bool:
        """
        Check if a task should be executed based on its schedule.
        We determine this by checking if we've moved from a time before the scheduled
        execution to a time at or after it.
        """
        try:
            # Create a cron iterator based on the last check time
            cron = croniter(task.schedule, last_check)
            
            # Get the next scheduled execution time after last_check
            next_execution = cron.get_next(datetime)
            
            # Log scheduler information for debugging
            logger.debug(f"Task {task.id}: Last check: {last_check.isoformat()}, "
                        f"Next execution: {next_execution.isoformat()}, "
                        f"Current time: {current_time.isoformat()}")
            
            # Check if the next execution time is at or before the current time
            # This means we've crossed into or past the scheduled execution time
            should_execute = next_execution <= current_time
            
            if should_execute:
                logger.info(f"Task {task.id} scheduled for {next_execution.isoformat()} should execute now")
            
            return should_execute
        except Exception as e:
            logger.error(f"Error parsing cron for task {task.id}: {str(e)}")
            return False