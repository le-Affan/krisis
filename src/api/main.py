import logging
import os
import subprocess
import time

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import get_settings
from src.core import ABTestFramework
from src.logging_config import setup_logging

settings = get_settings()

START_TIME = time.time()

app = FastAPI(
    title="A/B Testing Framework for Machine Learning Models",
    description="Production grade experimentation system for your models",
    version="1.0",
)


@app.on_event("startup")
def run_migrations():
    """Run Alembic migrations before serving any requests.

    The resolved DATABASE_URL from application settings is injected into the
    subprocess environment so Alembic migrates the *same* database the app
    connects to — never the postgres fallback baked into alembic.ini.

    check=True ensures the process exits with an error if the migration
    fails — uvicorn will not finish starting up and no requests will be
    served against an uninitialised schema.
    """
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        env={**os.environ, "DATABASE_URL": settings.database_url},
    )

Instrumentator().instrument(app).expose(app)

setup_logging()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logging.info(
        "request_processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
        },
    )

    return response


# CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection for framework instance
# When an endpoint needs the framework, create one and give it.
# Models are resolved per-experiment from the registry (see
# src/api/routes/models.py and ABTestFramework._invoke_variant in
# src/core.py) — there are no hardcoded model stand-ins.
framework = ABTestFramework()


def get_framework():
    return framework
    # Create singleton or per-request instance


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "storage_backend": settings.storage_backend,
    }


from src.api.routes import experiments, models, predictions, results

# Include routers
app.include_router(models.router, prefix="/api/v1", tags=["models"])
app.include_router(experiments.router, prefix="/api/v1", tags=["experiments"])
app.include_router(predictions.router, prefix="/api/v1", tags=["predictions"])
app.include_router(results.router, prefix="/api/v1", tags=["results"])


# Custom Exception Handler
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid value",
            "detail": str(exc),
        },
    )


@app.get("/metrics/app")
async def app_metrics(framework=Depends(get_framework)):
    return {
        "total_experiments": framework.storage.get_experiment_count(),
        "total_requests": framework.storage.get_request_count(),
        "total_outcomes": framework.storage.get_outcome_count(),
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }
