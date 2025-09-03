import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.database import Base, engine
from app.core.scheduler import TaskScheduler
from app.core.logging_config import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="Insignia Task Scheduler")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(api_router)

# Global scheduler instance
scheduler = None
scheduler_task = None


@app.on_event("startup")
async def startup_event():
    global scheduler, scheduler_task
    logger.info("Starting application...")

    # Initialize and start scheduler only if not already running
    if scheduler is None:
        scheduler = TaskScheduler()
        scheduler_task = asyncio.create_task(scheduler.start())


@app.on_event("shutdown")
async def shutdown_event():
    global scheduler, scheduler_task
    logger.info("Shutting down application...")

    # Stop scheduler
    if scheduler:
        await scheduler.stop()

    # Cancel scheduler task
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
