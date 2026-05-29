import os
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.slices.auth.router import router as auth_router
from app.slices.tasks.router import router as tasks_router


def create_app() -> FastAPI:
    app = FastAPI(title="Task Management API")

    @app.get("/health")
    def health_check() -> Dict[str, str]:
        return {"status": "ok"}

    cors_allow_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://127.0.0.1:8880,http://localhost:8880,http://127.0.0.1:5173,http://localhost:5173",
    )
    allow_origins = [origin.strip() for origin in cors_allow_origins.split(",") if origin.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(tasks_router)
    return app


app = create_app()
