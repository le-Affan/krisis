import logging
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
framework = ABTestFramework()


def model_a(x):
    return x["x"] + 1


def model_b(x):
    return x["x"] * 2


framework.register_models(model_a, model_b)


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


from src.api.routes import experiments, predictions, results

# Include routers
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


@app.get("/metrics")
async def metrics(framework=Depends(get_framework)):
    return {
        "total_experiments": framework.storage.get_experiment_count(),
        "total_requests": framework.storage.get_request_count(),
        "total_outcomes": framework.storage.get_outcome_count(),
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }
