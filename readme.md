# Task Management API (FastAPI + React)

A simple task management project built with:

- Backend: FastAPI + SQLite
- Frontend: React + Vite
- Tests: pytest
- CI: GitHub Actions

## Project Structure

- `app/`: backend application code (core + task slice)
- `frontend/`: React UI
- `tests/`: API tests
- `main.py`: FastAPI application entrypoint

## Prerequisites

- Python 3.10+ recommended
- Node.js 20+ recommended
- npm

## Backend Setup And Run

From project root:

```powershell
# 1) Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2) Install Python dependencies
pip install -r requirements.txt

# 2.5) (Optional) Local secret env file
Copy-Item .env.example .env
# Then edit .env and set DATABASE_URL

# 3) Run API server
uvicorn main:app --reload --host 127.0.0.1 --port 8888
```

If you are using a local `.env` file, run with:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8888 --env-file .env
```

API docs:

- Swagger UI: http://127.0.0.1:8888/docs
- ReDoc: http://127.0.0.1:8888/redoc

## Frontend Setup And Run

From project root:

```powershell
cd .\frontend
npm install
npm run dev -- --host 0.0.0.0 --port 8880
```

Frontend URL:

- http://localhost:8880

The frontend calls `http://127.0.0.1:8888` by default.
To override, set `VITE_API_BASE_URL`.

## API Endpoints

Base URL: `http://127.0.0.1:8888`

- `POST /tasks` create a task
- `GET /tasks` list tasks
- `GET /tasks/{task_id}` get task by id
- `GET /tasks/name/{task_name}` get task by name
- `PATCH /tasks/{task_id}` update task
- `DELETE /tasks/{task_id}` delete task

Task status values:

- `todo`
- `in_progress`
- `done`
- `archived`

Example create payload:

```json
{
	"title": "Write tests",
	"description": "Add API coverage"
}
```

## Testing

Run all tests:

```powershell
pytest -v
```

Run a specific file:

```powershell
pytest tests/test_tasks_api.py -v
```

## Seed Data

Seed a demo user and sample `todo` tasks:

```powershell
.\.venv\Scripts\python.exe seed_tasks.py
```

Default seeded login credentials:

- username: `demo`
- password: `demo123`

Re-seed and replace existing tasks for the demo user:

```powershell
.\.venv\Scripts\python.exe seed_tasks.py --force
```

Optional overrides:

- `SEED_DEMO_USERNAME`
- `SEED_DEMO_PASSWORD`

## Coverage

Generate terminal + HTML coverage report:

```powershell
python -m pytest tests -v --cov=app --cov-report=term-missing --cov-report=html
```

Open HTML report:

- `htmlcov/index.html`

## GitHub Actions (CI)

Workflow file: `.github/workflows/ci.yml`

CI runs on push and pull request:

- Backend tests on Python 3.10 and 3.11
- Frontend production build on Node 20

## Notes

- Default database is SQLite (`tasks.db` in project root).
- Set `SQLITE_DB_PATH` to override the SQLite file path.
- To use PostgreSQL instead, set `DATABASE_URL`.



# Environment Variables

- `SQLITE_DB_PATH` (optional): path to SQLite file.
- `DATABASE_URL` (optional): PostgreSQL connection string.

Example PostgreSQL value:

```powershell
$env:DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/tasks_db"
```

Permanent secret for this Windows user (not in git):

```powershell
setx DATABASE_URL "postgresql://username:password@host:5432/database?sslmode=require"
# Restart terminal after setx
```


# Coverage Report

`python -m pytest tests -v --cov=app --cov-report=term-missing --cov-report=html`


# Production

## Live Back End URL
https://python-todo-fullstack-project.onrender.com/docs

## Live Front End URL
https://linguyenvivito.github.io/python-todo-fullstack-project