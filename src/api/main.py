from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import experiments, predictions, results
from src.config import get_settings
from src.core import ABTestFramework

settings = get_settings()

app = FastAPI(
    title="A/B Testing Framework for Machine Learning Models",
    description="Production grade experimentation system for your models",
    version="1.0",
)

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
def get_framework():
    return ABTestFramework()  # Create singleton or per-request instance


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "storage_backend": settings.storage_backend,
    }


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
