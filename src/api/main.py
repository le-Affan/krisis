from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
