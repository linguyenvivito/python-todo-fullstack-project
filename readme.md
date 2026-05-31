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
- `GET /email/templates` list supported email templates (requires authentication)
- `POST /email/send` send an email via SMTP (requires authentication)

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

Example send email payload (manual mode):

```json
{
	"to_email": "user@example.com",
	"subject": "Welcome",
	"body": "Thanks for joining."
}
```

Example send email payload (template mode):

```json
{
	"to_email": "user@example.com",
	"template_name": "password_reset",
	"template_data": {
		"username": "alice",
		"reset_link": "https://app.example.com/reset?token=abc123",
		"expiry_minutes": "30"
	}
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

- Ruff lint on Python 3.11
- Backend tests on Python 3.10 and 3.11
- Frontend production build on Node 20

## Notes

- Default database is SQLite (`tasks.db` in project root).
- Set `SQLITE_DB_PATH` to override the SQLite file path.
- To use PostgreSQL instead, set `DATABASE_URL`.



# Environment Variables

- `SQLITE_DB_PATH` (optional): path to SQLite file.
- `DATABASE_URL` (optional): PostgreSQL connection string.
- `CORS_ALLOW_ORIGINS` (optional): comma-separated allowlist of origins allowed for cross-origin browser calls.
- `CORS_STRICT_ORIGIN_CHECK` (optional): when `true` (default), requests with non-allowlisted `Origin` header are rejected with 403.
- `CSRF_ENABLED` (optional): enables CSRF middleware checks for unsafe methods (`POST`, `PUT`, `PATCH`, `DELETE`). Default `true`.
- `CSRF_COOKIE_BASED_ONLY` (optional): when `true` (default), CSRF checks are applied only if request contains cookies.
- `CSRF_TRUSTED_ORIGINS` (optional): comma-separated trusted origins for CSRF validation. Defaults to `CORS_ALLOW_ORIGINS`.
- `SECURITY_HEADERS_ENABLED` (optional): enables standard security headers middleware. Default `true`.
- `SECURITY_HSTS_ENABLED` (optional): enables `Strict-Transport-Security` header for HTTPS requests. Default `true`.
- `REQUEST_LOGGING_ENABLED` (optional): enables app request logging middleware. Default `true`.
- `LOG_LEVEL` (optional): Python log level for app logging, default `INFO`.
- `LOG_FORMAT` (optional): Python logging format string.
- `LOG_JSON` (optional): emits structured JSON logs to stdout when `true`. Default `false`.
- `RATE_LIMITING_ENABLED` (optional): enables SlowAPI rate limiting. Default `true`.
- `RATE_LIMIT_AUTH_REGISTER` (optional): register endpoint rate, default `30/minute`.
- `RATE_LIMIT_AUTH_LOGIN` (optional): login endpoint rate, default `30/minute`.
- `RATE_LIMIT_AUTH_REFRESH` (optional): refresh endpoint rate, default `120/minute`.
- `RATE_LIMIT_AUTH_REVOKE` (optional): revoke endpoint rate, default `60/minute`.
- `RATE_LIMIT_TASKS_CREATE` (optional): create task endpoint rate, default `120/minute`.
- `RATE_LIMIT_TASKS_UPDATE` (optional): update task endpoint rate, default `180/minute`.
- `RATE_LIMIT_TASKS_DELETE` (optional): delete task endpoint rate, default `120/minute`.
- `RATE_LIMIT_EMAIL_SEND` (optional): email send endpoint rate, default `20/minute`.
- `SMTP_HOST` (required for email): SMTP server host.
- `SMTP_PORT` (optional): SMTP server port, default `587`.
- `SMTP_USE_TLS` (optional): enable STARTTLS for plain SMTP connections, default `true`.
- `SMTP_USE_SSL` (optional): use SMTP over SSL, default `false`.
- `SMTP_USERNAME` (optional): SMTP username for authenticated sending.
- `SMTP_PASSWORD` (optional): SMTP password for authenticated sending.
- `SMTP_FROM_EMAIL` (optional): from-address for outbound email; falls back to `SMTP_USERNAME`.
- `SMTP_FROM_NAME` (optional): display sender name, default `Task Management API`.
- `SMTP_TIMEOUT` (optional): SMTP connect timeout in seconds, default `10`.
- `SMTP_MAX_RETRIES` (optional): retry count after first failed send attempt, default `2`.
- `SMTP_RETRY_BACKOFF_SECONDS` (optional): base exponential backoff in seconds, default `0.5`.

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


# Set up env in production

Example: Set these in Render:

JWT_SECRET_KEY = generate a strong random value (64+ chars)
JWT_ALGORITHM = HS256
JWT_EXPIRE_MINUTES = 15
JWT_REFRESH_EXPIRE_MINUTES = 10080
CORS_ALLOW_ORIGINS = your frontend URLs, comma-separated
DATABASE_URL = your production Postgres URL
CORS_STRICT_ORIGIN_CHECK = true
CSRF_ENABLED = true
CSRF_COOKIE_BASED_ONLY = true
CSRF_TRUSTED_ORIGINS = same origin list as frontend URLs
SECURITY_HEADERS_ENABLED = true
SECURITY_HSTS_ENABLED = true
RATE_LIMITING_ENABLED = true

# Production

## Live Back End URL
https://python-todo-fullstack-project.onrender.com/docs

## Live Front End URL
https://linguyenvivito.github.io/python-todo-fullstack-project