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

# 3) Run API server
uvicorn main:app --reload --host 127.0.0.1 --port 8888
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

- SQLite database file defaults to `tasks.db` in project root.
- You can override DB path with `SQLITE_DB_PATH`.



# Environment Variables


# Coverage Report

`python -m pytest tests -v --cov=app --cov-report=term-missing --cov-report=html`


# Production

## Live Back End URL
https://python-todo-fullstack-project.onrender.com

## Live Front End URL
https://linguyenvivito.github.io/python-todo-fullstack-project