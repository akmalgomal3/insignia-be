# Insignia Task Scheduler - Backend

A FastAPI-based task scheduler application with PostgreSQL database integration.

## Features

- FastAPI framework with uvicorn ASGI server
- SQLAlchemy ORM with PostgreSQL
- Alembic for database migrations
- Dockerized application with docker-compose
- Pydantic for data validation
- Black and Ruff for code formatting and linting
- Bearer token authentication for API security
- Task scheduling engine with cron-like functionality
- Retry logic for failed tasks (configurable per task)
- Discord webhook integration for task execution notifications

## Project Structure

```
insignia-be/
├── app/
│   ├── api/          # API routers
│   ├── core/         # Configuration, settings, scheduler, and task executor
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   └── main.py       # Application entry point
├── alembic/          # Database migrations
├── tests/            # Test files
├── Dockerfile        # Docker configuration
├── docker-compose.yml # Multi-container setup
├── requirements.txt   # Python dependencies
└── alembic.ini       # Alembic configuration
```

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```
3. Update the `API_TOKEN` value in your `.env` file with a strong secret token
4. Run with Docker:
   ```bash
   docker-compose up --build
   ```

## API Authentication

All API endpoints require Bearer token authentication. Include the token in your requests:

```
Authorization: Bearer your-super-secret-token-here
```

## Task Scheduling

Tasks are scheduled using cron expressions. When a task is due, the system will:

1. Send a HTTP POST request to the provided Discord Webhook URL
2. Use the payload JSON as the request body
3. Implement retry logic if the request fails (configurable per task)

### How Scheduling Works

The scheduler checks for tasks to execute every minute. For each active task, it:

1. Calculates the next scheduled execution time based on the cron expression
2. Executes the task if the next scheduled time is at or before the current time

This approach ensures that tasks with specific times (like "28 2 * * *" for 2:28 AM) are properly executed, as long as the application is running when that time occurs.

Note: Tasks can only execute when the application is running. If the application is stopped during a scheduled execution time, that execution will be missed.

### Retry Logic

When a task fails to execute (due to network issues, invalid webhook URL, etc.), the system will automatically retry based on the `max_retry` value configured for that task:

1. If a task fails, it will retry up to `max_retry` times
2. Retry intervals use exponential backoff (1s, 2s, 4s, 8s, etc.)
3. After exceeding `max_retry` attempts, the task will be automatically deactivated to prevent continuous failures

This ensures that temporary issues can be resolved automatically while preventing tasks with persistent problems from continuously consuming system resources.

**Note**: The scheduler now refreshes task status before execution to ensure deactivated tasks are not executed again.

## Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the application:
```bash
python main.py
```

## Database Migrations

Initialize Alembic:
```bash
alembic init alembic
```

Create a migration:
```bash
alembic revision --autogenerate -m "Migration message"
```

Apply migrations:
```bash
alembic upgrade head
```

## Code Quality

Format code with Black:
```bash
black .
```

Lint with Ruff:
```bash
ruff check .
```

Fix linting issues:
```bash
ruff check . --fix
```

## Testing

Run all tests:
```bash
python -m pytest -v
```

Run specific test files:
```bash
# Test main endpoints
pytest tests/test_main.py

# Test task endpoints
pytest tests/test_tasks.py

# Test task log endpoints
pytest tests/test_task_logs.py

# Test scheduler functionality
pytest tests/test_scheduler.py

# Test retry logic
pytest tests/test_retry_logic.py
```

The test suite includes:
- Unit tests for all API endpoints
- Integration tests for database operations
- Tests for scheduler functionality
- Tests for retry logic and task deactivation
- Authentication tests

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Tasks

#### Create a Task
- **Endpoint**: `POST /tasks/`
- **Description**: Create a new scheduled task
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  Content-Type: application/json
  ```
- **Request Body**:
  ```json
  {
    "name": "Daily Report",
    "schedule": "0 9 * * *",  // Every day at 9 AM
    "webhook_url": "https://discord.com/api/webhooks/1412840086331986083/b-_i-mdfpPA7nZMHyUZGLeOWfHv9oUoKj1i0OWvyHGCgc_je6t4kYOZ-J3otDGONLDjl",
    "payload": {
      "content": "Daily report is ready!",
      "embeds": [
        {
          "title": "Daily Report",
          "description": "Here's your daily report",
          "color": 3447003
        }
      ]
    },
    "max_retry": 3,
    "status": "active"
  }
  ```
- **Response**: Returns the created task object with ID and timestamps

#### Get a Task
- **Endpoint**: `GET /tasks/{task_id}`
- **Description**: Retrieve a specific task by its ID
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  ```
- **Path Parameters**:
  - `task_id` (UUID): The unique identifier of the task
- **Response**: Returns the task object

#### Update a Task
- **Endpoint**: `PUT /tasks/{task_id}`
- **Description**: Update an existing task
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  Content-Type: application/json
  ```
- **Path Parameters**:
  - `task_id` (UUID): The unique identifier of the task
- **Request Body** (any of the following fields can be updated):
  ```json
  {
    "name": "Updated Task Name",
    "schedule": "0 10 * * *",  // Every day at 10 AM
    "webhook_url": "https://discord.com/api/webhooks/new/webhook/url",
    "payload": {
      "content": "Updated message"
    },
    "max_retry": 5,
    "status": "inactive"
  }
  ```
- **Response**: Returns the updated task object

#### Delete a Task
- **Endpoint**: `DELETE /tasks/{task_id}`
- **Description**: Delete a task
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  ```
- **Path Parameters**:
  - `task_id` (UUID): The unique identifier of the task
- **Response**: Returns a success message

#### List Tasks
- **Endpoint**: `GET /tasks/`
- **Description**: Retrieve a list of tasks with optional filtering and pagination
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  ```
- **Query Parameters**:
  - `skip` (integer, optional): Number of tasks to skip (default: 0)
  - `limit` (integer, optional): Maximum number of tasks to return (default: 100, max: 1000)
  - `status` (string, optional): Filter tasks by status (e.g., "active", "inactive")
  - `search` (string, optional): Search tasks by name
- **Response**: Returns a paginated list of tasks with total count
  ```json
  {
    "tasks": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Daily Report",
        "schedule": "0 9 * * *",
        "webhook_url": "https://discord.com/api/webhooks/1412840086331986083/b-_i-mdfpPA7nZMHyUZGLeOWfHv9oUoKj1i0OWvyHGCgc_je6t4kYOZ-J3otDGONLDjl",
        "payload": {
          "content": "Daily report is ready!"
        },
        "max_retry": 3,
        "status": "active",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 100
  }
  ```

### Task Logs

#### Create a Task Log
- **Endpoint**: `POST /task-logs/`
- **Description**: Create a new task execution log
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  Content-Type: application/json
  ```
- **Request Body**:
  ```json
  {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "execution_time": "2023-01-01T10:00:00Z",
    "status": "success",
    "retry_count": 0,
    "message": "Task executed successfully"
  }
  ```
- **Response**: Returns the created task log object

#### Get a Task Log
- **Endpoint**: `GET /task-logs/{task_log_id}`
- **Description**: Retrieve a specific task log by its ID
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  ```
- **Path Parameters**:
  - `task_log_id` (UUID): The unique identifier of the task log
- **Response**: Returns the task log object

#### Update a Task Log
- **Endpoint**: `PUT /task-logs/{task_log_id}`
- **Description**: Update an existing task log
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  Content-Type: application/json
  ```
- **Path Parameters**:
  - `task_log_id` (UUID): The unique identifier of the task log
- **Request Body**:
  ```json
  {
    "status": "failed",
    "message": "Task execution failed after 3 retries"
  }
  ```
- **Response**: Returns the updated task log object

#### Delete a Task Log
- **Endpoint**: `DELETE /task-logs/{task_log_id}`
- **Description**: Delete a task log
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  ```
- **Path Parameters**:
  - `task_log_id` (UUID): The unique identifier of the task log
- **Response**: Returns a success message

#### List Task Logs
- **Endpoint**: `GET /task-logs/`
- **Description**: Retrieve a list of task logs with optional filtering and pagination
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  ```
- **Query Parameters**:
  - `skip` (integer, optional): Number of task logs to skip (default: 0)
  - `limit` (integer, optional): Maximum number of task logs to return (default: 100, max: 1000)
  - `task_id` (UUID, optional): Filter task logs by task ID
  - `status` (string, optional): Filter task logs by status (e.g., "success", "failed")
- **Response**: Returns a paginated list of task logs with total count
  ```json
  {
    "task_logs": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "task_id": "123e4567-e89b-12d3-a456-426614174000",
        "execution_time": "2023-01-01T10:00:00Z",
        "status": "success",
        "retry_count": 0,
        "message": "Task executed successfully",
        "created_at": "2023-01-01T10:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 100
  }
  ```

#### List Task Logs by Task
- **Endpoint**: `GET /task-logs/task/{task_id}`
- **Description**: Retrieve a list of task logs for a specific task with optional filtering and pagination
- **Headers**: 
  ```
  Authorization: Bearer your-super-secret-token-here
  ```
- **Path Parameters**:
  - `task_id` (UUID): The unique identifier of the task
- **Query Parameters**:
  - `skip` (integer, optional): Number of task logs to skip (default: 0)
  - `limit` (integer, optional): Maximum number of task logs to return (default: 100, max: 1000)
  - `status` (string, optional): Filter task logs by status (e.g., "success", "failed")
- **Response**: Returns a paginated list of task logs with total count
  ```json
  {
    "task_logs": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "task_id": "123e4567-e89b-12d3-a456-426614174000",
        "execution_time": "2023-01-01T10:00:00Z",
        "status": "success",
        "retry_count": 0,
        "message": "Task executed successfully",
        "created_at": "2023-01-01T10:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 100
  }
  ```

### Health
- **Endpoint**: `GET /health`
- **Description**: Health check endpoint
- **Headers**: 
  ```bash
  Authorization: Bearer your-super-secret-token-here
  ```
- **Response**: 
  ```json
  {
    "status": "healthy"
  }
  ```

## Deploy to Google Cloud Run

### Prerequisites

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Initialize gcloud:
   ```bash
   gcloud init
   ```
3. Set your project:
   ```bash
   gcloud config set project lively-antonym-430302-q4
   ```
4. Enable required APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   ```

### Deploy to Cloud Run

To deploy the application to Google Cloud Run:

1. Build and deploy using Cloud Build:
   ```bash
   gcloud builds submit --tag gcr.io/lively-antonym-430302-q4/insignia-be
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy --image gcr.io/lively-antonym-430302-q4/insignia-be --platform managed
   ```

Alternatively, you can use the automated Cloud Run deployment:
```bash
gcloud run deploy insignia-be \
  --source . \
  --platform managed \
  --region asia-southeast2 \
  --allow-unauthenticated
```

### Environment Variables

When deploying to Cloud Run, make sure to set the required environment variables:
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `API_TOKEN`
- `LOG_LEVEL`

You can set them during deployment:
```bash
gcloud run deploy insignia-be \
  --source . \
  --platform managed \
  --region asia-southeast2 \
  --allow-unauthenticated \
  --set-env-vars POSTGRES_USER=your-user,POSTGRES_PASSWORD=your-password,POSTGRES_DB=your-db,API_TOKEN=your-token
```

## Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the application:
```bash
python main.py
```

Run with Docker Compose:
```bash
docker-compose up --build
```

## Logging Configuration

The application uses a centralized logging configuration that can be customized through environment variables:

- `LOG_LEVEL`: Set the logging level (default: INFO)
  - Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Example: `LOG_LEVEL=DEBUG` for more detailed logging

Logs are written to both console and a rotating file (`app.log`) with a maximum size of 10MB and up to 5 backup files.

SQLAlchemy logging has been reduced to WARNING level to minimize redundant database query logs.